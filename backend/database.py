import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

from curriculum import PROBLEMS, level_of

CONTENT_VERSION = "3"

DB_PATH = Path(__file__).resolve().parent / "olympiad.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    streak INTEGER NOT NULL DEFAULT 0,
    last_active TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    theory TEXT NOT NULL,
    statement TEXT NOT NULL,
    starter_code TEXT NOT NULL,
    input_format TEXT NOT NULL,
    output_format TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id INTEGER NOT NULL,
    input_data TEXT NOT NULL,
    output_data TEXT NOT NULL,
    is_sample INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS solves (
    user_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    solved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, problem_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    verdict TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    error_log TEXT NOT NULL DEFAULT '',
    coach TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quiz_answers (
    user_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    choice INTEGER NOT NULL,
    correct INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, problem_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS classrooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS classroom_students (
    classroom_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    PRIMARY KEY (classroom_id, student_id),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS parent_children (
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    actor_id INTEGER,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    topic TEXT NOT NULL,
    statement TEXT NOT NULL,
    starter_code TEXT NOT NULL,
    sample_input TEXT NOT NULL DEFAULT '',
    sample_output TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'mock',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hint_unlocks (
    user_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, problem_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
);
"""

PROBLEM_COLUMNS = {
    "topic": "ALTER TABLE problems ADD COLUMN topic TEXT NOT NULL DEFAULT 'io'",
    "sort_order": "ALTER TABLE problems ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0",
    "quiz_prompt": "ALTER TABLE problems ADD COLUMN quiz_prompt TEXT NOT NULL DEFAULT ''",
    "quiz_code": "ALTER TABLE problems ADD COLUMN quiz_code TEXT NOT NULL DEFAULT ''",
    "quiz_options": "ALTER TABLE problems ADD COLUMN quiz_options TEXT NOT NULL DEFAULT '[]'",
    "quiz_answer": "ALTER TABLE problems ADD COLUMN quiz_answer INTEGER NOT NULL DEFAULT 0",
    "quiz_why": "ALTER TABLE problems ADD COLUMN quiz_why TEXT NOT NULL DEFAULT ''",
    "explanation": "ALTER TABLE problems ADD COLUMN explanation TEXT NOT NULL DEFAULT ''",
    "solution_code": "ALTER TABLE problems ADD COLUMN solution_code TEXT NOT NULL DEFAULT ''",
    "coach_hint": "ALTER TABLE problems ADD COLUMN coach_hint TEXT NOT NULL DEFAULT ''",
    "olympiad_level": "ALTER TABLE problems ADD COLUMN olympiad_level INTEGER NOT NULL DEFAULT 1",
}


def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_user_columns(connection):
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
    if existing and "role" not in existing:
        connection.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")


def write_log(connection, level, message, actor_id=None):
    connection.execute(
        "INSERT INTO system_logs (level, actor_id, message) VALUES (?, ?, ?)",
        (level, actor_id, message[:500]),
    )


def seed_portals(connection):
    demos = [
        ("Кенжебай Арман", "arman@olymp.kz", "student"),
        ("Айгүл Сейітова", "teacher@olymp.kz", "teacher"),
        ("Нұрлан Кенжебай", "parent@olymp.kz", "parent"),
        ("Әкім Басқарма", "admin@olymp.kz", "admin"),
    ]
    ids = {}
    for name, email, role in demos:
        row = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row is None:
            connection.execute(
                """
                INSERT INTO users (name, email, password_hash, xp, level, streak, role)
                VALUES (?, ?, ?, 0, 1, 0, ?)
                """,
                (name, email, generate_password_hash("123456"), role),
            )
            row = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        else:
            connection.execute("UPDATE users SET role = ? WHERE id = ?", (role, row["id"]))
        ids[role] = row["id"]

    classroom = connection.execute(
        "SELECT id FROM classrooms WHERE teacher_id = ?",
        (ids["teacher"],),
    ).fetchone()
    if classroom is None:
        cursor = connection.execute(
            "INSERT INTO classrooms (teacher_id, name) VALUES (?, ?)",
            (ids["teacher"], "7-сынып"),
        )
        classroom_id = cursor.lastrowid
    else:
        classroom_id = classroom["id"]
    connection.execute(
        """
        INSERT INTO classroom_students (classroom_id, student_id) VALUES (?, ?)
        ON CONFLICT(classroom_id, student_id) DO NOTHING
        """,
        (classroom_id, ids["student"]),
    )
    connection.execute(
        """
        INSERT INTO parent_children (parent_id, child_id) VALUES (?, ?)
        ON CONFLICT(parent_id, child_id) DO NOTHING
        """,
        (ids["parent"], ids["student"]),
    )


def ensure_attempt_columns(connection):
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(attempts)")}
    if existing and "coach" not in existing:
        connection.execute("ALTER TABLE attempts ADD COLUMN coach TEXT NOT NULL DEFAULT ''")
    if existing and "runtime_ms" not in existing:
        connection.execute("ALTER TABLE attempts ADD COLUMN runtime_ms INTEGER")


def ensure_problem_columns(connection):
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(problems)")}
    for name, statement in PROBLEM_COLUMNS.items():
        if name not in existing:
            connection.execute(statement)


def seed_curriculum(connection):
    connection.execute("DELETE FROM hint_unlocks")
    connection.execute("DELETE FROM quiz_answers")
    connection.execute("DELETE FROM attempts")
    connection.execute("DELETE FROM solves")
    connection.execute("DELETE FROM tests")
    connection.execute("DELETE FROM problems")
    connection.execute("DELETE FROM sqlite_sequence WHERE name IN ('problems', 'tests', 'attempts')")
    for index, problem in enumerate(PROBLEMS):
        cursor = connection.execute(
            """
            INSERT INTO problems (
                title, difficulty, theory, statement, starter_code, input_format, output_format,
                topic, olympiad_level, sort_order, quiz_prompt, quiz_code, quiz_options, quiz_answer, quiz_why,
                explanation, solution_code, coach_hint
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                problem["title"],
                problem["difficulty"],
                problem["theory"],
                problem["statement"],
                problem["starter_code"],
                problem["input_format"],
                problem["output_format"],
                problem["topic"],
                level_of(problem["topic"]),
                index,
                problem["quiz_prompt"],
                problem["quiz_code"],
                json.dumps(problem["quiz_options"], ensure_ascii=False),
                problem["quiz_answer"],
                problem["quiz_why"],
                problem["explanation"],
                problem["solution_code"],
                problem["coach_hint"],
            ),
        )
        for input_data, output_data, is_sample in problem["tests"]:
            connection.execute(
                """
                INSERT INTO tests (problem_id, input_data, output_data, is_sample)
                VALUES (?, ?, ?, ?)
                """,
                (cursor.lastrowid, input_data, output_data, 1 if is_sample else 0),
            )
    connection.execute(
        """
        INSERT INTO meta (key, value) VALUES ('content', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (CONTENT_VERSION,),
    )


def init_db():
    connection = connect()
    connection.executescript(SCHEMA)
    ensure_user_columns(connection)
    ensure_problem_columns(connection)
    ensure_attempt_columns(connection)
    version = connection.execute("SELECT value FROM meta WHERE key = 'content'").fetchone()
    if version is None or version["value"] != CONTENT_VERSION:
        seed_curriculum(connection)
    demo = connection.execute("SELECT id FROM users WHERE email = ?", ("arman@olymp.kz",)).fetchone()
    if demo is None:
        connection.execute(
            """
            INSERT INTO users (name, email, password_hash, xp, level, streak, last_active)
            VALUES (?, ?, ?, 0, 1, 0, NULL)
            """,
            ("Кенжебай Арман", "arman@olymp.kz", generate_password_hash("123456")),
        )
    seed_portals(connection)
    connection.commit()
    connection.close()


def touch_streak(connection, user_id):
    row = connection.execute(
        "SELECT streak, last_active FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    today = date.today().isoformat()
    if row["last_active"] == today:
        return
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    streak = row["streak"] + 1 if row["last_active"] == yesterday else 1
    connection.execute(
        "UPDATE users SET streak = ?, last_active = ? WHERE id = ?",
        (streak, today, user_id),
    )


def award_xp(connection, user_id, problem_id, difficulty):
    already = connection.execute(
        "SELECT 1 FROM solves WHERE user_id = ? AND problem_id = ?",
        (user_id, problem_id),
    ).fetchone()
    if already:
        return 0
    points = {"easy": 10, "medium": 20, "hard": 30}.get(difficulty, 10)
    connection.execute(
        "INSERT INTO solves (user_id, problem_id) VALUES (?, ?)",
        (user_id, problem_id),
    )
    connection.execute(
        "UPDATE users SET xp = xp + ?, level = 1 + (xp + ?) / 100 WHERE id = ?",
        (points, points, user_id),
    )
    return points
