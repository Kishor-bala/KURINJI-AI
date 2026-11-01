import sqlite3
from typing import List, Optional, Dict, Any
from backend.app.database.connection import get_db_connection


def insert_vocabulary_entry(
    word_id: str,
    language: str,
    tamil_meaning: str,
    english_meaning: str,
    optional_romanised_pronunciation: Optional[str] = None,
    notes: Optional[str] = None,
    verification_status: str = "verified",
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Inserts or updates a vocabulary record in the database."""
    query = """
    INSERT INTO vocabulary (
        word_id, language, tamil_meaning, english_meaning,
        optional_romanised_pronunciation, notes, verification_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(word_id) DO UPDATE SET
        language = excluded.language,
        tamil_meaning = excluded.tamil_meaning,
        english_meaning = excluded.english_meaning,
        optional_romanised_pronunciation = excluded.optional_romanised_pronunciation,
        notes = excluded.notes,
        verification_status = excluded.verification_status;
    """
    params = (
        word_id, language, tamil_meaning, english_meaning,
        optional_romanised_pronunciation, notes, verification_status
    )
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    try:
        conn.execute(query, params)
        if should_close:
            conn.commit()
    finally:
        if should_close:
            conn.close()

    return get_vocabulary_by_id(word_id)


def get_vocabulary_by_id(word_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single vocabulary record by its unique Word ID."""
    query = "SELECT * FROM vocabulary WHERE word_id = ?;"
    with get_db_connection() as conn:
        row = conn.execute(query, (word_id,)).fetchone()
        if row:
            return dict(row)
    return None


def list_vocabulary(language: Optional[str] = None, limit: int = 500, offset: int = 0) -> List[Dict[str, Any]]:
    """Lists vocabulary entries with optional filtering by language."""
    query = "SELECT * FROM vocabulary"
    params = []
    if language:
        query += " WHERE language = ?"
        params.append(language)
    query += " ORDER BY word_id ASC LIMIT ? OFFSET ?;"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]


def get_vocabulary_count(language: Optional[str] = None) -> int:
    """Returns total count of vocabulary entries, optionally by language."""
    query = "SELECT COUNT(*) FROM vocabulary"
    params = []
    if language:
        query += " WHERE language = ?"
        params.append(language)
    with get_db_connection() as conn:
        return conn.execute(query, tuple(params)).fetchone()[0]


def search_vocabulary_text(text: str, language: Optional[str] = None, exact_only: bool = False) -> List[Dict[str, Any]]:
    """Searches vocabulary by exact (or optional partial) match on English meaning, Romanised pronunciation, or Word ID."""
    clean_text = text.strip().lower()
    if not clean_text:
        return []

    # 1. Exact match (or exact token match in comma-separated pronunciations)
    query_exact = """
    SELECT * FROM vocabulary
    WHERE (
        LOWER(word_id) = ?
        OR LOWER(english_meaning) = ?
        OR LOWER(tamil_meaning) = ?
        OR LOWER(optional_romanised_pronunciation) = ?
        OR (', ' || LOWER(optional_romanised_pronunciation) || ', ') LIKE ?
    )
    """
    token_param = f"%, {clean_text}, %"
    params_exact = [clean_text, clean_text, clean_text, clean_text, token_param]
    if language:
        query_exact += " AND language = ?"
        params_exact.append(language)

    query_exact += " ORDER BY CASE WHEN LOWER(english_meaning) = ? THEN 1 WHEN LOWER(word_id) = ? THEN 2 ELSE 3 END, word_id ASC LIMIT 10;"
    params_exact.extend([clean_text, clean_text])

    with get_db_connection() as conn:
        rows = conn.execute(query_exact, tuple(params_exact)).fetchall()
        if rows:
            return [dict(r) for r in rows]

    if exact_only:
        return []

    # 2. Substring/prefix match fallback for vocabulary browsing
    query_like = """
    SELECT * FROM vocabulary
    WHERE (
        LOWER(english_meaning) LIKE ?
        OR LOWER(optional_romanised_pronunciation) LIKE ?
    )
    """
    params_like = [f"%{clean_text}%", f"%{clean_text}%"]
    if language:
        query_like += " AND language = ?"
        params_like.append(language)
    query_like += " ORDER BY word_id ASC LIMIT 10;"

    with get_db_connection() as conn:
        rows = conn.execute(query_like, tuple(params_like)).fetchall()
        return [dict(r) for r in rows]

