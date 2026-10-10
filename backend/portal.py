from datetime import date, timedelta

from flask import Blueprint, g, jsonify, request

from ai_service import draft_reply, parent_reply
from curriculum import TOPICS, level_of
from database import write_log
from scaffold import independence_score

portal_bp = Blueprint("portal", __name__)
ROLES = {"student", "teacher", "parent", "admin"}
POINTS = {"easy": 10, "medium": 20, "hard": 30}
VERDICTS = ("AC", "WA", "RE", "TLE", "CE")


def _tools():
    from app import get_db, json_error

    return get_db, json_error


def roles_required(*allowed):
    def decorator(view):
        def wrapped(*args, **kwargs):
            get_db, json_error = _tools()
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
            if (row["role"] or "student") not in allowed:
                return json_error("Бұл бөлім сіздің рөліңізге жабық.", 403)
            return view(*args, **kwargs)

        wrapped.__name__ = view.__name__
        return wrapped

    return decorator


def _student_card(connection, row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "xp": row["xp"],
        "level": row["level"],
        "streak": row["streak"],
        "independence": independence_score(connection, row["id"]),
    }


def _heatmap(connection, teacher_id):
    counts = {
        topic_id: {"id": topic_id, "title": title, **{verdict: 0 for verdict in VERDICTS}}
        for topic_id, title in TOPICS
    }
    rows = connection.execute(
        """
        SELECT problems.topic AS topic, attempts.verdict AS verdict, COUNT(*) AS count
        FROM attempts
        JOIN classroom_students ON classroom_students.student_id = attempts.user_id
        JOIN classrooms ON classrooms.id = classroom_students.classroom_id
        JOIN problems ON problems.id = attempts.problem_id
        WHERE classrooms.teacher_id = ?
        GROUP BY problems.topic, attempts.verdict
        """,
        (teacher_id,),
    ).fetchall()
    for row in rows:
        bucket = counts.get(row["topic"])
        if bucket and row["verdict"] in bucket:
            bucket[row["verdict"]] = row["count"]
    return list(counts.values())


def _weekly_xp(connection, user_id):
    start = (date.today() - timedelta(days=6)).isoformat()
    rows = connection.execute(
        """
        SELECT problems.difficulty AS difficulty
        FROM solves
        JOIN problems ON problems.id = solves.problem_id
        WHERE solves.user_id = ? AND date(solves.solved_at) >= date(?)
        """,
        (user_id, start),
    ).fetchall()
    return sum(POINTS.get(row["difficulty"], 10) for row in rows)


def _topic_mastery(connection, user_id):
    rows = connection.execute(
        """
        SELECT problems.topic AS topic,
               SUM(CASE WHEN solves.user_id IS NOT NULL THEN 1 ELSE 0 END) AS solved,
               COUNT(problems.id) AS total
        FROM problems
        LEFT JOIN solves ON solves.problem_id = problems.id AND solves.user_id = ?
        GROUP BY problems.topic
        """,
        (user_id,),
    ).fetchall()
    titles = dict(TOPICS)
    ranked = []
    for row in rows:
        total = row["total"] or 0
        solved = row["solved"] or 0
        ratio = solved / total if total else 0
        ranked.append((ratio, titles.get(row["topic"], row["topic"])))
    ranked.sort()
    weakness = ranked[0][1] if ranked else "әлі байқалмады"
    strength = ranked[-1][1] if ranked else "әлі байқалмады"
    if ranked and ranked[-1][0] == 0:
        strength = "әлі шешім жоқ"
    return strength, weakness


@portal_bp.get("/api/teacher/home")
@roles_required("teacher")
def teacher_home():
    get_db, _json_error = _tools()
    connection = get_db()
    classrooms = connection.execute(
        "SELECT id, name FROM classrooms WHERE teacher_id = ? ORDER BY id",
        (g.user["id"],),
    ).fetchall()
    payload = []
    for classroom in classrooms:
        students = connection.execute(
            """
            SELECT users.*
            FROM classroom_students
            JOIN users ON users.id = classroom_students.student_id
            WHERE classroom_students.classroom_id = ?
            ORDER BY users.name
            """,
            (classroom["id"],),
        ).fetchall()
        payload.append(
            {
                "id": classroom["id"],
                "name": classroom["name"],
                "students": [_student_card(connection, student) for student in students],
            }
        )
    drafts = connection.execute(
        """
        SELECT id, title, difficulty, topic, statement, source, created_at
        FROM drafts WHERE teacher_id = ? ORDER BY id DESC
        """,
        (g.user["id"],),
    ).fetchall()
    return jsonify(
        {
            "classrooms": payload,
            "heatmap": _heatmap(connection, g.user["id"]),
            "drafts": [dict(item) for item in drafts],
        }
    )


@portal_bp.post("/api/teacher/classrooms")
@roles_required("teacher")
def create_classroom():
    get_db, json_error = _tools()
    body = request.get_json(silent=True) or {}
    name = str(body.get("name") or "").strip()
    if len(name) < 2:
        return json_error("Сынып атауын жазыңыз.", 400)
    connection = get_db()
    cursor = connection.execute(
        "INSERT INTO classrooms (teacher_id, name) VALUES (?, ?)",
        (g.user["id"], name),
    )
    write_log(connection, "info", f"Сынып құрылды: {name}", g.user["id"])
    connection.commit()
    return jsonify({"id": cursor.lastrowid, "name": name}), 201


@portal_bp.post("/api/teacher/classrooms/<int:classroom_id>/students")
@roles_required("teacher")
def add_student(classroom_id):
    get_db, json_error = _tools()
    body = request.get_json(silent=True) or {}
    email = str(body.get("email") or "").strip().lower()
    connection = get_db()
    classroom = connection.execute(
        "SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?",
        (classroom_id, g.user["id"]),
    ).fetchone()
    if classroom is None:
        return json_error("Сынып табылмады.", 404)
    student = connection.execute(
        "SELECT id, role FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    if student is None or student["role"] != "student":
        return json_error("Оқушы табылмады.", 404)
    connection.execute(
        """
        INSERT INTO classroom_students (classroom_id, student_id) VALUES (?, ?)
        ON CONFLICT(classroom_id, student_id) DO NOTHING
        """,
        (classroom_id, student["id"]),
    )
    write_log(connection, "info", f"Оқушы қосылды: {email}", g.user["id"])
    connection.commit()
    return jsonify({"ok": True})


@portal_bp.post("/api/teacher/drafts")
@roles_required("teacher")
def create_draft():
    get_db, json_error = _tools()
    body = request.get_json(silent=True) or {}
    topic = str(body.get("topic") or "loops").strip()
    difficulty = str(body.get("difficulty") or "easy").strip()
    note = str(body.get("note") or "").strip()
    if difficulty not in POINTS:
        return json_error("Қиындық: easy, medium немесе hard.", 400)
    reply = draft_reply(topic, difficulty, note)
    connection = get_db()
    cursor = connection.execute(
        """
        INSERT INTO drafts (
            teacher_id, title, difficulty, topic, statement, starter_code, sample_input, sample_output, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            g.user["id"],
            reply["title"],
            difficulty,
            topic,
            reply["statement"],
            reply["starter_code"],
            reply["sample_input"],
            reply["sample_output"],
            reply["source"],
        ),
    )
    write_log(connection, "info", f"Есеп жобасы: {reply['title']} ({reply['source']})", g.user["id"])
    connection.commit()
    return jsonify({"id": cursor.lastrowid, **reply}), 201


@portal_bp.get("/api/parent/home")
@roles_required("parent")
def parent_home():
    get_db, _json_error = _tools()
    connection = get_db()
    children = connection.execute(
        """
        SELECT users.*
        FROM parent_children
        JOIN users ON users.id = parent_children.child_id
        WHERE parent_children.parent_id = ?
        ORDER BY users.name
        """,
        (g.user["id"],),
    ).fetchall()
    payload = []
    for child in children:
        strength, weakness = _topic_mastery(connection, child["id"])
        weekly = _weekly_xp(connection, child["id"])
        report = parent_reply(child["name"], weekly, child["streak"], strength, weakness)
        card = _student_card(connection, child)
        card.update(
            {
                "weekly_xp": weekly,
                "strength": strength,
                "weakness": weakness,
                "summary": report["text"],
                "summary_source": report["source"],
            }
        )
        payload.append(card)
    return jsonify({"children": payload})


@portal_bp.get("/api/admin/users")
@roles_required("admin")
def admin_users():
    get_db, _json_error = _tools()
    connection = get_db()
    rows = connection.execute(
        "SELECT id, name, email, role, xp, level, streak FROM users ORDER BY id"
    ).fetchall()
    return jsonify({"users": [dict(row) for row in rows]})


@portal_bp.post("/api/admin/users")
@roles_required("admin")
def admin_create_user():
    from werkzeug.security import generate_password_hash

    get_db, json_error = _tools()
    body = request.get_json(silent=True) or {}
    name = str(body.get("name") or "").strip()
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    role = str(body.get("role") or "student").strip()
    if len(name) < 2 or "@" not in email or len(password) < 6 or role not in ROLES:
        return json_error("Аты, email, кемінде 6 таңбалы құпия сөз және рөл керек.", 400)
    connection = get_db()
    exists = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if exists:
        return json_error("Бұл email бұрын тіркелген.", 409)
    connection.execute(
        """
        INSERT INTO users (name, email, password_hash, xp, level, streak, role)
        VALUES (?, ?, ?, 0, 1, 0, ?)
        """,
        (name, email, generate_password_hash(password), role),
    )
    write_log(connection, "info", f"Қолданушы құрылды: {email} ({role})", g.user["id"])
    connection.commit()
    return jsonify({"ok": True}), 201


@portal_bp.patch("/api/admin/users/<int:user_id>")
@roles_required("admin")
def admin_update_user(user_id):
    get_db, json_error = _tools()
    body = request.get_json(silent=True) or {}
    role = str(body.get("role") or "").strip()
    name = str(body.get("name") or "").strip()
    if role and role not in ROLES:
        return json_error("Рөл қате.", 400)
    connection = get_db()
    row = connection.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return json_error("Қолданушы табылмады.", 404)
    if name:
        connection.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    if role:
        connection.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    write_log(connection, "info", f"Қолданушы жаңартылды: {user_id}", g.user["id"])
    connection.commit()
    return jsonify({"ok": True})


@portal_bp.delete("/api/admin/users/<int:user_id>")
@roles_required("admin")
def admin_delete_user(user_id):
    get_db, json_error = _tools()
    if user_id == g.user["id"]:
        return json_error("Өз аккаунтыңызды өшіруге болмайды.", 400)
    connection = get_db()
    row = connection.execute("SELECT id, email FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return json_error("Қолданушы табылмады.", 404)
    connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
    write_log(connection, "warn", f"Қолданушы өшірілді: {row['email']}", g.user["id"])
    connection.commit()
    return jsonify({"ok": True})


@portal_bp.get("/api/admin/problems")
@roles_required("admin")
def admin_problems():
    get_db, _json_error = _tools()
    connection = get_db()
    problems = connection.execute(
        "SELECT id, title, difficulty, topic, statement FROM problems ORDER BY sort_order, id"
    ).fetchall()
    drafts = connection.execute(
        """
        SELECT drafts.*, users.name AS teacher_name
        FROM drafts JOIN users ON users.id = drafts.teacher_id
        ORDER BY drafts.id DESC
        """
    ).fetchall()
    return jsonify({"problems": [dict(item) for item in problems], "drafts": [dict(item) for item in drafts]})


@portal_bp.patch("/api/admin/problems/<int:problem_id>")
@roles_required("admin")
def admin_update_problem(problem_id):
    get_db, json_error = _tools()
    body = request.get_json(silent=True) or {}
    title = str(body.get("title") or "").strip()
    statement = str(body.get("statement") or "").strip()
    difficulty = str(body.get("difficulty") or "").strip()
    if not title:
        return json_error("Атауы керек.", 400)
    if difficulty and difficulty not in POINTS:
        return json_error("Қиындық қате.", 400)
    connection = get_db()
    row = connection.execute("SELECT id FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if row is None:
        return json_error("Есеп табылмады.", 404)
    connection.execute(
        """
        UPDATE problems
        SET title = ?,
            statement = CASE WHEN ? != '' THEN ? ELSE statement END,
            difficulty = CASE WHEN ? != '' THEN ? ELSE difficulty END
        WHERE id = ?
        """,
        (title, statement, statement, difficulty, difficulty, problem_id),
    )
    write_log(connection, "info", f"Есеп жаңартылды: {title}", g.user["id"])
    connection.commit()
    return jsonify({"ok": True})


@portal_bp.delete("/api/admin/problems/<int:problem_id>")
@roles_required("admin")
def admin_delete_problem(problem_id):
    get_db, json_error = _tools()
    connection = get_db()
    row = connection.execute("SELECT title FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if row is None:
        return json_error("Есеп табылмады.", 404)
    connection.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
    write_log(connection, "warn", f"Есеп өшірілді: {row['title']}", g.user["id"])
    connection.commit()
    return jsonify({"ok": True})


@portal_bp.post("/api/admin/drafts/<int:draft_id>/publish")
@roles_required("admin")
def publish_draft(draft_id):
    get_db, json_error = _tools()
    connection = get_db()
    draft = connection.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    if draft is None:
        return json_error("Жоба табылмады.", 404)
    order = connection.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 AS next FROM problems").fetchone()["next"]
    cursor = connection.execute(
        """
        INSERT INTO problems (
            title, difficulty, theory, statement, starter_code, input_format, output_format,
            topic, olympiad_level, sort_order, coach_hint
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            draft["title"],
            draft["difficulty"],
            "Мұғалім дайындаған есеп. Кірісті input() арқылы оқып, жауапты print() арқылы шығарыңыз.",
            draft["statement"],
            draft["starter_code"],
            "Бір бүтін сан.",
            "Бір бүтін сан.",
            draft["topic"] if draft["topic"] in dict(TOPICS) else "io",
            level_of(draft["topic"] if draft["topic"] in dict(TOPICS) else "io"),
            order,
            "Мысалды қолыңызбен есептеп, print ішіндегі өрнекті тексеріңіз.",
        ),
    )
    connection.execute(
        """
        INSERT INTO tests (problem_id, input_data, output_data, is_sample)
        VALUES (?, ?, ?, 1)
        """,
        (cursor.lastrowid, draft["sample_input"] or "1\n", draft["sample_output"] or "1\n"),
    )
    connection.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    write_log(connection, "info", f"Жоба жарияланды: {draft['title']}", g.user["id"])
    connection.commit()
    return jsonify({"id": cursor.lastrowid})


@portal_bp.get("/api/admin/logs")
@roles_required("admin")
def admin_logs():
    get_db, _json_error = _tools()
    connection = get_db()
    rows = connection.execute(
        """
        SELECT system_logs.id, system_logs.level, system_logs.message, system_logs.created_at,
               users.email AS actor
        FROM system_logs
        LEFT JOIN users ON users.id = system_logs.actor_id
        ORDER BY system_logs.id DESC
        LIMIT 80
        """
    ).fetchall()
    return jsonify({"logs": [dict(row) for row in rows]})
