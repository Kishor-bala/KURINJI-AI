import sqlite3
from pathlib import Path
from backend.app.config import DATABASE_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_db_connection() -> sqlite3.Connection:
    """Creates and returns an active SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes the database tables from schema.sql if they do not exist."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db_connection() as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DATABASE_PATH}")
