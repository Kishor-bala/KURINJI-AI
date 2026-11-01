import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from backend.app.config import (
    EMBEDDINGS_DIR,
    ENCODER_MODEL_NAME,
    DEFAULT_POOLING_METHOD,
    ENCODER_REPRESENTATION_DIM,
)
from backend.app.database.connection import get_db_connection


def get_embedding_file_path(clip_id: str) -> Path:
    """Returns the .npy file path for a given Clip ID."""
    return EMBEDDINGS_DIR / f"{clip_id}.npy"


def save_embedding_with_metadata(
    clip_id: str,
    word_id: str,
    vector: np.ndarray,
    encoder_name: str = ENCODER_MODEL_NAME,
    encoder_version: str = "facebook/wav2vec2-xls-r-300m@main",
    layer_name: str = "last_hidden_state",
    pooling_method: str = DEFAULT_POOLING_METHOD,
    conn: Optional[sqlite3.Connection] = None,
) -> Path:
    """
    Saves an embedding array as a .npy file and records complete metadata
    in the SQLite embeddings table. Never stores an embedding without vocabulary linkage.
    """
    if vector.ndim != 1 or vector.shape[0] != ENCODER_REPRESENTATION_DIM:
        raise ValueError(
            f"Expected embedding dimension ({ENCODER_REPRESENTATION_DIM},), got {vector.shape}"
        )

    # Ensure output directory exists
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = get_embedding_file_path(clip_id)

    # Save vector as NumPy .npy file
    np.save(str(file_path), vector.astype(np.float32))

    embedding_id = f"emb_{clip_id}"
    query = """
    INSERT INTO embeddings (
        embedding_id, clip_id, word_id, encoder_name, encoder_version,
        layer_name, pooling_method, embedding_file, embedding_dimension
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(embedding_id) DO UPDATE SET
        word_id = excluded.word_id,
        encoder_name = excluded.encoder_name,
        encoder_version = excluded.encoder_version,
        layer_name = excluded.layer_name,
        pooling_method = excluded.pooling_method,
        embedding_file = excluded.embedding_file,
        embedding_dimension = excluded.embedding_dimension,
        creation_timestamp = CURRENT_TIMESTAMP;
    """
    params = (
        embedding_id,
        clip_id,
        word_id,
        encoder_name,
        encoder_version,
        layer_name,
        pooling_method,
        str(file_path),
        vector.shape[0],
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

    return file_path


def load_embedding_vector(file_path_or_clip_id: str) -> Optional[np.ndarray]:
    """Loads a 1024-d NumPy embedding array from disk."""
    path = Path(file_path_or_clip_id)
    if not path.is_file():
        path = get_embedding_file_path(file_path_or_clip_id)

    if not path.is_file():
        return None

    return np.load(str(path)).astype(np.float32)


def load_all_reference_embeddings(
    language: Optional[str] = None,
    encoder_name: str = ENCODER_MODEL_NAME,
    pooling_method: str = DEFAULT_POOLING_METHOD,
) -> List[Dict[str, Any]]:
    """
    Loads all active reference embeddings and their vocabulary/recording metadata.
    Guarantees consistent encoder and pooling method versions.
    """
    query = """
    SELECT 
        e.embedding_id,
        e.clip_id,
        e.word_id,
        e.embedding_file,
        e.embedding_dimension,
        v.language,
        v.tamil_meaning,
        v.english_meaning,
        r.speaker_id,
        r.clip_file
    FROM embeddings e
    JOIN vocabulary v ON e.word_id = v.word_id
    JOIN recordings r ON e.clip_id = r.clip_id
    WHERE e.encoder_name = ? AND e.pooling_method = ?
    """
    params = [encoder_name, pooling_method]
    if language:
        query += " AND v.language = ?"
        params.append(language)

    entries = []
    with get_db_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
        for row in rows:
            record = dict(row)
            vec = load_embedding_vector(record["embedding_file"])
            if vec is not None:
                record["vector"] = vec
                entries.append(record)

    return entries
