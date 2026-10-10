PENALTY = {1: 10, 2: 25, 3: 45}


def independence_score(connection, user_id):
    rows = connection.execute(
        "SELECT level FROM hint_unlocks WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    penalty = sum(PENALTY.get(row["level"], 0) for row in rows)
    return max(0, 100 - penalty)


def scaffold_state(connection, user_id, problem_id):
    row = connection.execute(
        "SELECT level FROM hint_unlocks WHERE user_id = ? AND problem_id = ?",
        (user_id, problem_id),
    ).fetchone()
    return {
        "unlocked_level": row["level"] if row else 0,
        "independence": independence_score(connection, user_id),
    }


def unlock_hint(connection, user_id, problem, level, verdict="WA", lang="kk"):
    current = connection.execute(
        "SELECT level FROM hint_unlocks WHERE user_id = ? AND problem_id = ?",
        (user_id, problem["id"]),
    ).fetchone()
    opened = max(level, current["level"] if current else 0)
    connection.execute(
        """
        INSERT INTO hint_unlocks (user_id, problem_id, level)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, problem_id) DO UPDATE SET
            level = excluded.level,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, problem["id"], opened),
    )
    from ai_service import scaffold_reply

    reply = scaffold_reply(verdict, level, problem["title"], problem["statement"], lang, problem["topic"])
    return {
        "level": level,
        "hint": reply["text"],
        "source": reply["source"],
        "unlocked_level": opened,
        "independence": independence_score(connection, user_id),
    }
