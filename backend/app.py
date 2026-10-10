import json
import secrets
import socket
from functools import wraps

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from coach import explain
from content_i18n import localize
from curriculum import LEVELS, TOPICS, TOPIC_SUMMARY
from database import award_xp, connect, init_db, touch_streak, write_log
from i18n import current_lang, text
from judge import run_code
from scaffold import independence_score, scaffold_state, unlock_hint
from tracer import trace_code
from ai_service import tutor_reply

DIFFICULTY_RANK = {"easy": 0, "medium": 1, "hard": 2}
XP_REWARD = {"easy": 10, "medium": 20, "hard": 30}
TOPIC_TITLES = dict(TOPICS)

app = Flask(__name__)
CORS(app)


def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db


@app.teardown_appcontext
def close_db(_error):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def public_user(connection, row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "xp": row["xp"],
        "level": row["level"],
        "streak": row["streak"],
        "independence": independence_score(connection, row["id"]),
        "role": row["role"] if "role" in row.keys() else "student",
    }


def json_error(message, status):
    return jsonify({"message": message}), status


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header[7:].strip() if header.startswith("Bearer ") else ""
        if not token:
            return json_error("Кіру қажет.", 401)
        row = get_db().execute(
            """
            SELECT users.*
            FROM tokens
            JOIN users ON users.id = tokens.user_id
            WHERE tokens.token = ?
            """,
            (token,),
        ).fetchone()
        if row is None:
            return json_error("Сессия аяқталды. Қайта кіріңіз.", 401)
        g.user = row
        return view(*args, **kwargs)

    return wrapped


@app.post("/api/auth/register")
def register():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name") or "").strip()
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")

    if len(name) < 2:
        return json_error("Аты-жөнін толық жазыңыз.", 400)
    if "@" not in email or "." not in email.split("@")[-1]:
        return json_error("Email дұрыс емес.", 400)
    if len(password) < 6:
        return json_error("Құпия сөз кемінде 6 таңба болуы керек.", 400)

    connection = get_db()
    exists = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if exists:
        return json_error("Бұл email бұрын тіркелген.", 409)

    cursor = connection.execute(
        """
        INSERT INTO users (name, email, password_hash, xp, level, streak)
        VALUES (?, ?, ?, 0, 1, 0)
        """,
        (name, email, generate_password_hash(password)),
    )
    touch_streak(connection, cursor.lastrowid)
    token = secrets.token_urlsafe(32)
    connection.execute(
        "INSERT INTO tokens (token, user_id) VALUES (?, ?)",
        (token, cursor.lastrowid),
    )
    connection.commit()
    user = connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    write_log(connection, "info", f"Тіркелу: {email}", user["id"])
    connection.commit()
    return jsonify({"token": token, "user": public_user(connection, user)}), 201


@app.post("/api/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    connection = get_db()
    user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        return json_error("Email немесе құпия сөз қате.", 401)

    touch_streak(connection, user["id"])
    token = secrets.token_urlsafe(32)
    connection.execute(
        "INSERT INTO tokens (token, user_id) VALUES (?, ?)",
        (token, user["id"]),
    )
    connection.commit()
    fresh = connection.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    write_log(connection, "info", f"Кіру: {fresh['email']} ({fresh['role']})", fresh["id"])
    connection.commit()
    return jsonify({"token": token, "user": public_user(connection, fresh)})


@app.post("/api/auth/logout")
@login_required
def logout():
    header = request.headers.get("Authorization", "")
    token = header[7:].strip()
    connection = get_db()
    connection.execute("DELETE FROM tokens WHERE token = ?", (token,))
    connection.commit()
    return jsonify({"message": "Шықтыңыз."})


@app.get("/api/user")
@login_required
def current_user():
    connection = get_db()
    touch_streak(connection, g.user["id"])
    connection.commit()
    user = connection.execute("SELECT * FROM users WHERE id = ?", (g.user["id"],)).fetchone()
    return jsonify(public_user(connection, user))


def problem_rows(connection, user_id):
    return connection.execute(
        """
        SELECT
            problems.id,
            problems.title,
            problems.difficulty,
            problems.topic,
            problems.sort_order,
            EXISTS(
                SELECT 1 FROM solves
                WHERE solves.user_id = ? AND solves.problem_id = problems.id
            ) AS solved,
            EXISTS(
                SELECT 1 FROM attempts
                WHERE attempts.user_id = ? AND attempts.problem_id = problems.id
            ) AS attempted
        FROM problems
        ORDER BY problems.sort_order, problems.id
        """,
        (user_id, user_id),
    ).fetchall()


def copy_of(row, lang=None):
    language = lang or current_lang()
    topic = row["topic"] if "topic" in row.keys() else ""
    return localize(row["title"], language, topic)


def shown(row, field, lang=None):
    return copy_of(row, lang).get(field) or row[field]


def status_of(row):
    if row["solved"]:
        return "solved"
    if row["attempted"]:
        return "attempted"
    return "new"


def progress_for(connection, user_id):
    rows = problem_rows(connection, user_id)
    grouped = {topic_id: [] for topic_id, _title in TOPICS}
    for row in rows:
        grouped.setdefault(row["topic"], []).append(row)

    topics = []
    today = None
    today_key = None
    gate = False
    order = 0
    levels = []
    for level in LEVELS:
        level_topics = []
        for topic in level["topics"]:
            order += 1
            topic_id = topic["id"]
            title = topic["title"]
            items = grouped.get(topic_id, [])
            solved = sum(1 for item in items if item["solved"])
            total = len(items)
            done = total > 0 and solved >= total
            if done:
                status = "done"
            elif gate:
                status = "locked"
            else:
                status = "current"
                gate = True
            payload = {
                "id": topic_id,
                "title": title,
                "summary": TOPIC_SUMMARY.get(topic_id, ""),
                "solved": solved,
                "total": total,
                "status": status,
                "order": order,
                "level_id": level["id"],
                "level_name": level["name"],
                "level_subtitle": level["subtitle"],
                "level_emoji": level["emoji"],
                "level_color": level["color"],
            }
            topics.append(payload)
            level_topics.append(payload)
            unsolved = [item for item in items if not item["solved"]]
            if not unsolved:
                continue
            unsolved.sort(key=lambda item: (DIFFICULTY_RANK.get(item["difficulty"], 9), item["sort_order"]))
            mastery = solved / total if total else 1
            key = (mastery, order)
            if today_key is None or key < today_key:
                today_key = key
                chosen = unsolved[0]
                today = {
                    "id": chosen["id"],
                    "title": shown(chosen, "title"),
                    "difficulty": chosen["difficulty"],
                    "topic": topic_id,
                    "topic_title": title,
                    "solved": solved,
                    "total": total,
                    "xp_reward": XP_REWARD.get(chosen["difficulty"], 10),
                    "level_id": level["id"],
                    "level_name": level["name"],
                    "level_subtitle": level["subtitle"],
                    "level_emoji": level["emoji"],
                    "level_color": level["color"],
                    "reason": text("reason", current_lang(), title=title, solved=solved, total=total),
                }
        levels.append(
            {
                "id": level["id"],
                "key": level["key"],
                "name": level["name"],
                "subtitle": level["subtitle"],
                "emoji": level["emoji"],
                "color": level["color"],
                "topics": level_topics,
            }
        )

    solved_total = sum(topic["solved"] for topic in topics)
    problem_total = sum(topic["total"] for topic in topics)
    percent = int(round(100 * solved_total / problem_total)) if problem_total else 0
    if today:
        advice = text("advice", current_lang(), topic=today["topic_title"])
    else:
        advice = text("advice_done", current_lang())

    rates = {
        row["problem_id"]: int(row["rate"])
        for row in connection.execute(
            """
            SELECT problem_id,
                   ROUND(100.0 * SUM(CASE WHEN verdict = 'AC' THEN 1 ELSE 0 END) / COUNT(*)) AS rate
            FROM attempts
            GROUP BY problem_id
            """
        )
    }
    problems = [
        {
            "id": row["id"],
            "title": shown(row, "title"),
            "difficulty": row["difficulty"],
            "topic": row["topic"],
            "topic_title": TOPIC_TITLES.get(row["topic"], row["topic"]),
            "status": status_of(row),
            "acceptance": rates.get(row["id"]),
        }
        for row in rows
    ]
    return {
        "topics": topics,
        "levels": levels,
        "today": today,
        "problems": problems,
        "advice": advice,
        "solved": solved_total,
        "total": problem_total,
        "percent": percent,
    }


def attempt_stats(connection, user_id, problem_id):
    failed = connection.execute(
        """
        SELECT COUNT(*) AS count FROM attempts
        WHERE user_id = ? AND problem_id = ? AND verdict != 'AC'
        """,
        (user_id, problem_id),
    ).fetchone()["count"]
    solved = connection.execute(
        "SELECT 1 FROM solves WHERE user_id = ? AND problem_id = ?",
        (user_id, problem_id),
    ).fetchone()
    unlocked = solved is not None or failed >= 3
    if solved is not None:
        reason = "solved"
    elif failed >= 3:
        reason = "attempts"
    else:
        reason = ""
    return {
        "solved": solved is not None,
        "failed_count": failed,
        "solution_unlocked": unlocked,
        "unlock_reason": reason,
        "attempts_until_unlock": 0 if unlocked else 3 - failed,
    }


def list_attempts(connection, user_id, problem_id):
    rows = connection.execute(
        """
        SELECT id, verdict, message, error_log, coach, code, created_at
        FROM attempts
        WHERE user_id = ? AND problem_id = ?
        ORDER BY id DESC
        LIMIT 20
        """,
        (user_id, problem_id),
    ).fetchall()
    return [dict(row) for row in rows]


def quiz_payload(connection, problem, user_id):
    extra = copy_of(problem)
    options = extra.get("quiz_options") or json.loads(problem["quiz_options"] or "[]")
    saved = connection.execute(
        "SELECT choice, correct FROM quiz_answers WHERE user_id = ? AND problem_id = ?",
        (user_id, problem["id"]),
    ).fetchone()
    payload = {
        "prompt": extra.get("quiz_prompt") or problem["quiz_prompt"],
        "code": problem["quiz_code"],
        "options": options,
        "answered": saved is not None,
    }
    if saved is not None:
        payload["choice"] = saved["choice"]
        payload["correct"] = bool(saved["correct"])
        payload["why"] = extra.get("quiz_why") or problem["quiz_why"]
        payload["right_index"] = problem["quiz_answer"]
    return payload


def learning_payload(connection, problem, user_id):
    stats = attempt_stats(connection, user_id, problem["id"])
    payload = {
        "explanation": shown(problem, "explanation") if stats["solved"] else "",
        "solution_code": problem["solution_code"] if stats["solution_unlocked"] else "",
        **stats,
    }
    return payload


@app.get("/api/progress")
@login_required
def progress():
    return jsonify(progress_for(get_db(), g.user["id"]))


@app.get("/api/problems")
@login_required
def list_problems():
    return jsonify(progress_for(get_db(), g.user["id"])["problems"])


@app.get("/api/problems/<int:problem_id>")
@login_required
def problem_detail(problem_id):
    connection = get_db()
    problem = connection.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if problem is None:
        return json_error("Есеп табылмады.", 404)
    samples = connection.execute(
        """
        SELECT input_data AS input, output_data AS output
        FROM tests
        WHERE problem_id = ? AND is_sample = 1
        ORDER BY id
        """,
        (problem_id,),
    ).fetchall()
    learning = learning_payload(connection, problem, g.user["id"])
    return jsonify(
        {
            "id": problem["id"],
            "title": shown(problem, "title"),
            "difficulty": problem["difficulty"],
            "topic": problem["topic"],
            "topic_title": TOPIC_TITLES.get(problem["topic"], problem["topic"]),
            "theory": shown(problem, "theory"),
            "statement": shown(problem, "statement"),
            "starter_code": problem["starter_code"],
            "input_format": shown(problem, "input_format"),
            "output_format": shown(problem, "output_format"),
            "samples": [dict(sample) for sample in samples],
            "quiz": quiz_payload(connection, problem, g.user["id"]),
            "attempts": list_attempts(connection, g.user["id"], problem_id),
            **learning,
        }
    )


@app.post("/api/problems/<int:problem_id>/quiz")
@login_required
def answer_quiz(problem_id):
    connection = get_db()
    problem = connection.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if problem is None:
        return json_error("Есеп табылмады.", 404)
    existing = connection.execute(
        "SELECT choice, correct FROM quiz_answers WHERE user_id = ? AND problem_id = ?",
        (g.user["id"], problem_id),
    ).fetchone()
    if existing is None:
        body = request.get_json(silent=True) or {}
        try:
            choice = int(body.get("choice"))
        except (TypeError, ValueError):
            return json_error("Нұсқаны таңдаңыз.", 400)
        options = json.loads(problem["quiz_options"] or "[]")
        if choice < 0 or choice >= len(options):
            return json_error("Нұсқаны таңдаңыз.", 400)
        correct = 1 if choice == problem["quiz_answer"] else 0
        connection.execute(
            """
            INSERT INTO quiz_answers (user_id, problem_id, choice, correct)
            VALUES (?, ?, ?, ?)
            """,
            (g.user["id"], problem_id, choice, correct),
        )
        connection.commit()
    return jsonify({"quiz": quiz_payload(connection, problem, g.user["id"])})


@app.post("/api/problems/<int:problem_id>/run")
@login_required
def run_problem(problem_id):
    connection = get_db()
    problem = connection.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if problem is None:
        return json_error("Есеп табылмады.", 404)

    body = request.get_json(silent=True) or {}
    code = body.get("code") or ""
    tests = connection.execute(
        "SELECT input_data, output_data FROM tests WHERE problem_id = ? ORDER BY id",
        (problem_id,),
    ).fetchall()
    lang = current_lang()
    result = run_code(code, tests, lang=lang)
    coach = explain(
        result["verdict"],
        result.pop("stderr", ""),
        result.pop("actual", ""),
        result.pop("expected", ""),
        code,
        shown(problem, "coach_hint", lang),
        lang,
    )
    result["coach"] = coach

    connection.execute(
        """
        INSERT INTO attempts (user_id, problem_id, code, verdict, message, error_log, coach, runtime_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            g.user["id"],
            problem_id,
            code,
            result["verdict"],
            result["message"],
            result["error_log"],
            coach,
            result.get("runtime_ms"),
        ),
    )

    xp_gained = 0
    if result["verdict"] == "AC":
        xp_gained = award_xp(connection, g.user["id"], problem_id, problem["difficulty"])
        if xp_gained:
            result["message"] = text("ac_xp", lang, xp=xp_gained)
        else:
            result["message"] = text("ac_again", lang)

    connection.commit()
    learning = learning_payload(connection, problem, g.user["id"])
    user = connection.execute("SELECT * FROM users WHERE id = ?", (g.user["id"],)).fetchone()
    result["user"] = public_user(connection, user)
    result.update(learning)
    return jsonify(result)


@app.get("/api/problems/<int:problem_id>/scaffold")
@login_required
def scaffold_status(problem_id):
    connection = get_db()
    problem = connection.execute("SELECT id FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if problem is None:
        return json_error("Есеп табылмады.", 404)
    return jsonify(scaffold_state(connection, g.user["id"], problem_id))


@app.post("/api/problems/<int:problem_id>/scaffold")
@login_required
def scaffold_unlock(problem_id):
    connection = get_db()
    problem = connection.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if problem is None:
        return json_error("Есеп табылмады.", 404)
    body = request.get_json(silent=True) or {}
    try:
        level = int(body.get("level"))
    except (TypeError, ValueError):
        return json_error("Кеңес деңгейін таңдаңыз.", 400)
    if level not in (1, 2, 3):
        return json_error("Кеңес деңгейін таңдаңыз.", 400)
    verdict = str(body.get("verdict") or "WA").strip().upper()
    if verdict not in {"WA", "TLE", "RE", "CE", "AC"}:
        verdict = "WA"
    payload = unlock_hint(connection, g.user["id"], problem, level, verdict, current_lang())
    write_log(connection, "info", f"Кеңес {level} / {verdict} / {payload['source']}", g.user["id"])
    connection.commit()
    return jsonify(payload)


@app.post("/api/problems/<int:problem_id>/trace")
@login_required
def trace_problem(problem_id):
    connection = get_db()
    problem = connection.execute("SELECT id FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if problem is None:
        return json_error("Есеп табылмады.", 404)
    sample = connection.execute(
        """
        SELECT input_data FROM tests
        WHERE problem_id = ? AND is_sample = 1
        ORDER BY id
        LIMIT 1
        """,
        (problem_id,),
    ).fetchone()
    body = request.get_json(silent=True) or {}
    payload = trace_code(body.get("code") or "", sample["input_data"] if sample else "")
    return jsonify(payload)


@app.post("/api/tutor")
@login_required
def tutor_chat():
    body = request.get_json(silent=True) or {}
    message = str(body.get("message") or "")
    reply = tutor_reply(message)
    connection = get_db()
    write_log(connection, "info", f"Тьютор ({reply['source']})", g.user["id"])
    connection.commit()
    return jsonify({"reply": reply["text"], "source": reply["source"]})


@app.get("/api/results")
@login_required
def results():
    connection = get_db()
    user = connection.execute("SELECT * FROM users WHERE id = ?", (g.user["id"],)).fetchone()
    submissions = connection.execute(
        """
        SELECT attempts.id, attempts.verdict, attempts.runtime_ms, attempts.created_at,
               attempts.problem_id, problems.title, problems.topic, problems.difficulty
        FROM attempts
        JOIN problems ON problems.id = attempts.problem_id
        WHERE attempts.user_id = ?
        ORDER BY attempts.id DESC
        LIMIT 40
        """,
        (g.user["id"],),
    ).fetchall()
    heatmap = {topic_id: {"id": topic_id, "title": title, "AC": 0, "WA": 0, "RE": 0, "TLE": 0, "CE": 0} for topic_id, title in TOPICS}
    for row in connection.execute(
        """
        SELECT problems.topic AS topic, attempts.verdict AS verdict, COUNT(*) AS count
        FROM attempts
        JOIN problems ON problems.id = attempts.problem_id
        WHERE attempts.user_id = ?
        GROUP BY problems.topic, attempts.verdict
        """,
        (g.user["id"],),
    ):
        bucket = heatmap.get(row["topic"])
        if bucket and row["verdict"] in bucket:
            bucket[row["verdict"]] = row["count"]
    progress = progress_for(connection, g.user["id"])
    solved_hard = connection.execute(
        """
        SELECT 1
        FROM solves
        JOIN problems ON problems.id = solves.problem_id
        WHERE solves.user_id = ? AND problems.difficulty = 'hard'
        LIMIT 1
        """,
        (g.user["id"],),
    ).fetchone()
    return jsonify(
        {
            "user": public_user(connection, user),
            "submissions": [dict(item) for item in submissions],
            "topics": progress["topics"],
            "heatmap": list(heatmap.values()),
            "badges": {
                "medalist": solved_hard is not None,
                "streak": (user["streak"] or 0) >= 7,
                "debug": independence_score(connection, user["id"]) >= 80 and bool(progress["topics"] and any(topic["solved"] for topic in progress["topics"])),
            },
        }
    )


@app.get("/api/health")
def health():
    from database import DB_PATH

    return jsonify({"ok": True, "database": str(DB_PATH)})


def lan_ip():
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        address = probe.getsockname()[0]
        probe.close()
        return address
    except OSError:
        return "127.0.0.1"


from portal import portal_bp

if not getattr(portal_bp, "_got_registered_once", False):
    app.register_blueprint(portal_bp)


if __name__ == "__main__":
    init_db()
    address = lan_ip()
    print(f"Database: {__import__('database').DB_PATH}")
    print(f"Phone URL: http://{address}:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
