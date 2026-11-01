import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import time
import numpy as np
from backend.app.config import (
    ENCODER_MODEL_NAME,
    DEFAULT_POOLING_METHOD,
    TARGET_SAMPLE_RATE,
)
from backend.app.database.connection import get_db_connection
from backend.app.audio.preprocessing import load_and_standardize_audio
from backend.app.embeddings.extraction import extract_audio_embedding
from backend.app.embeddings.storage import (
    save_embedding_with_metadata,
    get_embedding_file_path,
)


def extract_all_reference_embeddings(force_recompute: bool = False):
    """
    Processes all reference recordings in the database, extracts XLS-R 1024-d embeddings,
    and stores them as .npy files linked to SQLite metadata.
    Resumable: skips recordings that already have valid embeddings unless force_recompute=True.
    """
    print("=" * 65)
    print("EXTRACTING REFERENCE AUDIO EMBEDDINGS (XLS-R 300M)")
    print(f"Model: {ENCODER_MODEL_NAME} | Pooling: {DEFAULT_POOLING_METHOD}")
    print("=" * 65)

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT clip_id, word_id, clip_file, speaker_id FROM recordings ORDER BY word_id, clip_id ASC;"
        ).fetchall()

    total_clips = len(rows)
    print(f"Total reference recordings to process: {total_clips}")

    processed_count = 0
    skipped_count = 0
    failed_clips = []
    start_time = time.time()

    with get_db_connection() as conn:
        for idx, row in enumerate(rows, start=1):
            clip_id = row["clip_id"]
            word_id = row["word_id"]
            clip_file = row["clip_file"]

            npy_path = get_embedding_file_path(clip_id)

            # Check if already processed
            if not force_recompute and npy_path.is_file():
                # Verify SQLite record exists
                exists = conn.execute(
                    "SELECT 1 FROM embeddings WHERE clip_id = ?;", (clip_id,)
                ).fetchone()
                if exists:
                    skipped_count += 1
                    continue

            audio_path = Path(clip_file)
            if not audio_path.is_file():
                failed_clips.append((clip_id, f"Audio file not found: {clip_file}"))
                continue

            try:
                # Load audio standardized to 16 kHz mono float32
                waveform, sr = load_and_standardize_audio(audio_path, target_sr=TARGET_SAMPLE_RATE)

                # Extract normalized 1024-d XLS-R embedding
                embedding, _ = extract_audio_embedding(
                    waveform=waveform,
                    sample_rate=sr,
                    pooling_method=DEFAULT_POOLING_METHOD,
                )

                # Save .npy file and record in SQLite
                save_embedding_with_metadata(
                    clip_id=clip_id,
                    word_id=word_id,
                    vector=embedding,
                    encoder_name=ENCODER_MODEL_NAME,
                    encoder_version="facebook/wav2vec2-xls-r-300m@main",
                    layer_name="last_hidden_state",
                    pooling_method=DEFAULT_POOLING_METHOD,
                    conn=conn,
                )
                processed_count += 1

                if processed_count % 20 == 0 or idx == total_clips:
                    conn.commit()
                    elapsed = time.time() - start_time
                    fps = processed_count / max(1.0, elapsed)
                    print(
                        f"[{idx}/{total_clips}] Processed: {processed_count} | "
                        f"Skipped: {skipped_count} | Speed: {fps:.2f} clips/s"
                    )

            except Exception as e:
                failed_clips.append((clip_id, str(e)))

        conn.commit()

    total_time = time.time() - start_time
    print("\n--- EMBEDDING EXTRACTION SUMMARY ---")
    print(f"Total Clips in Database: {total_clips}")
    print(f"Newly Generated Embeddings: {processed_count}")
    print(f"Previously Cached / Skipped: {skipped_count}")
    print(f"Failed Extractions: {len(failed_clips)}")
    if failed_clips:
        print("Sample failures:", failed_clips[:5])
    print(f"Total Execution Time: {total_time:.2f}s")
    print("=" * 65)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    force = "--force" in sys.argv
    extract_all_reference_embeddings(force_recompute=force)
