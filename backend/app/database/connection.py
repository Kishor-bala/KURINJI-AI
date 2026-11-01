import os
import shutil
import sqlite3
from pathlib import Path
from backend.app.config import DATABASE_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _resolve_working_db_path() -> str:
    """
    On serverless environments (Vercel / AWS Lambda), the deployment directory is strictly read-only.
    Copy vocabulary.db to /tmp so SQLite has full read/write and journal access without crashing.
    """
    if os.name != "nt" and os.path.exists("/tmp"):
        tmp_db = Path("/tmp/vocabulary.db")
        if not tmp_db.is_file() and DATABASE_PATH.is_file():
            try:
                shutil.copy2(str(DATABASE_PATH), str(tmp_db))
            except Exception:
                pass
        if tmp_db.is_file():
            return str(tmp_db)
    return str(DATABASE_PATH)


def get_db_connection() -> sqlite3.Connection:
    """Creates and returns an active SQLite database connection with row factory enabled."""
    db_file = _resolve_working_db_path()
    try:
        conn = sqlite3.connect(db_file, timeout=30.0)
    except sqlite3.OperationalError:
        # Fallback to URI read-only immutable if directory write fails
        conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True, timeout=30.0)

    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout = 30000;")
        conn.execute("PRAGMA foreign_keys = ON;")
    except Exception:
        pass
    return conn


def init_db():
    """Initializes the database tables from schema.sql if they do not exist."""
    db_file = _resolve_working_db_path()
    with get_db_connection() as conn:
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
        except Exception:
            pass
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DATABASE_PATH}")
