"""
db.py — PostgreSQL persistence via psycopg2.

Schema (run once on your DB):

    CREATE TABLE players (
        id       SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL
    );

    CREATE TABLE game_sessions (
        id            SERIAL PRIMARY KEY,
        player_id     INTEGER REFERENCES players(id),
        score         INTEGER   NOT NULL,
        level_reached INTEGER   NOT NULL,
        played_at     TIMESTAMP DEFAULT NOW()
    );

Connection settings are read from DB_CONFIG below — edit to match your setup.
If psycopg2 is not installed or the DB is unreachable, all functions degrade
gracefully (return [] / None / 0) so the game still runs offline.
"""

import traceback

# ── Connection config — edit these ───────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "snake_game",
    "user":     "postgres",
    "password": "postgres",   # ← change to your password
}

# ── Internal helpers ──────────────────────────────────────────────────────────
_conn = None   # module-level cached connection

def _get_conn():
    """Return a live psycopg2 connection, or None if unavailable."""
    global _conn
    try:
        import psycopg2
        if _conn is None or _conn.closed:
            _conn = psycopg2.connect(**DB_CONFIG)
            _conn.autocommit = False
        return _conn
    except Exception:
        return None


def _execute(sql: str, params=(), fetch: str = "none"):
    """
    Run SQL with params.
    fetch: 'none' | 'one' | 'all'
    Returns fetched rows, or None on error.
    """
    conn = _get_conn()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        result = None
        if fetch == "one":
            result = cur.fetchone()
        elif fetch == "all":
            result = cur.fetchall()
        conn.commit()
        return result
    except Exception:
        traceback.print_exc()
        try:
            conn.rollback()
        except Exception:
            pass
        return None


# ── Schema creation ───────────────────────────────────────────────────────────
def ensure_schema() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    _execute("""
        CREATE TABLE IF NOT EXISTS players (
            id       SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL
        )
    """)
    _execute("""
        CREATE TABLE IF NOT EXISTS game_sessions (
            id            SERIAL PRIMARY KEY,
            player_id     INTEGER REFERENCES players(id),
            score         INTEGER   NOT NULL,
            level_reached INTEGER   NOT NULL,
            played_at     TIMESTAMP DEFAULT NOW()
        )
    """)


# ── Player helpers ────────────────────────────────────────────────────────────
def get_or_create_player(username: str) -> int | None:
    """Return player id (creates row if username is new)."""
    row = _execute(
        "SELECT id FROM players WHERE username = %s",
        (username,), fetch="one"
    )
    if row:
        return row[0]
    row = _execute(
        "INSERT INTO players (username) VALUES (%s) RETURNING id",
        (username,), fetch="one"
    )
    return row[0] if row else None


# ── Session helpers ───────────────────────────────────────────────────────────
def save_session(username: str, score: int, level_reached: int) -> None:
    """Insert a game session for the given username."""
    pid = get_or_create_player(username)
    if pid is None:
        return
    _execute(
        "INSERT INTO game_sessions (player_id, score, level_reached) "
        "VALUES (%s, %s, %s)",
        (pid, score, level_reached)
    )


def personal_best(username: str) -> int:
    """Return the player's all-time best score, or 0 if none."""
    row = _execute(
        """
        SELECT MAX(gs.score)
        FROM game_sessions gs
        JOIN players p ON p.id = gs.player_id
        WHERE p.username = %s
        """,
        (username,), fetch="one"
    )
    if row and row[0] is not None:
        return int(row[0])
    return 0


def top10() -> list[dict]:
    """
    Return the top-10 all-time scores.
    Each item: {rank, username, score, level, date}
    """
    rows = _execute(
        """
        SELECT p.username, gs.score, gs.level_reached,
               TO_CHAR(gs.played_at, 'YYYY-MM-DD') AS played_at
        FROM game_sessions gs
        JOIN players p ON p.id = gs.player_id
        ORDER BY gs.score DESC
        LIMIT 10
        """,
        fetch="all"
    )
    if not rows:
        return []
    return [
        {"rank": i + 1, "username": r[0], "score": r[1],
         "level": r[2], "date": r[3]}
        for i, r in enumerate(rows)
    ]