import sqlite3
from typing import List, Optional, Dict, Any
from backend.app.database.connection import get_db_connection


def insert_recording_entry(
    clip_id: str,
    word_id: str,
    speaker_id: str,
    clip_file: str,
    original_file: Optional[str] = None,
    start_timestamp: float = 0.0,
    end_timestamp: Optional[float] = None,
    sample_rate: int = 16000,
    duration: Optional[float] = None,
    review_status: str = "reviewed",
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Inserts or updates a recording record in the database."""
    query = """
    INSERT INTO recordings (
        clip_id, word_id, speaker_id, original_file, clip_file,
        start_timestamp, end_timestamp, sample_rate, duration, review_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(clip_id) DO UPDATE SET
        word_id = excluded.word_id,
        speaker_id = excluded.speaker_id,
        original_file = excluded.original_file,
        clip_file = excluded.clip_file,
        start_timestamp = excluded.start_timestamp,
        end_timestamp = excluded.end_timestamp,
        sample_rate = excluded.sample_rate,
        duration = excluded.duration,
        review_status = excluded.review_status;
    """
    params = (
        clip_id, word_id, speaker_id, original_file, clip_file,
        start_timestamp, end_timestamp, sample_rate, duration, review_status
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

    return get_recording_by_id(clip_id)


def get_recording_by_id(clip_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single recording record by Clip ID."""
    query = "SELECT * FROM recordings WHERE clip_id = ?;"
    with get_db_connection() as conn:
        row = conn.execute(query, (clip_id,)).fetchone()
        if row:
            return dict(row)
    return None


def list_recordings_for_word(word_id: str) -> List[Dict[str, Any]]:
    """Retrieves all recordings associated with a specific Word ID."""
    query = "SELECT * FROM recordings WHERE word_id = ? ORDER BY created_at ASC;"
    with get_db_connection() as conn:
        rows = conn.execute(query, (word_id,)).fetchall()
        return [dict(r) for r in rows]


def list_all_recordings(review_status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists all recordings with optional filter by review status."""
    query = "SELECT * FROM recordings"
    params = []
    if review_status:
        query += " WHERE review_status = ?"
        params.append(review_status)
    query += " ORDER BY word_id, clip_id ASC;"

    with get_db_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]
