import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import glob
import openpyxl
from backend.app.config import (
    DATASET_LOG_FILE,
    DATASET_BADAGA_DIR,
    DATASET_MARWARI_DIR,
    DATABASE_PATH,
)
from backend.app.database.connection import init_db, get_db_connection
from backend.app.database.vocabulary import insert_vocabulary_entry
from backend.app.database.recordings import insert_recording_entry
from backend.app.audio.validation import validate_audio_file


def build_audio_file_index() -> dict:
    """Indexes all audio files in the dataset by filename to locate full relative paths."""
    index = {}
    for p in DATASET_BADAGA_DIR.glob("**/*.wav"):
        index[p.name] = p
    for p in DATASET_MARWARI_DIR.glob("**/*.wav"):
        index[p.name] = p
    return index


def format_canonical_word_id(language: str, raw_word_id: str) -> str:
    """Formats canonical Word ID as BDG_W0001 or MWR_W0001."""
    clean_id = str(raw_word_id).strip()
    prefix = "BDG" if language.lower() == "badaga" else "MWR"
    if clean_id.startswith("BDG_") or clean_id.startswith("MWR_"):
        return clean_id
    if not clean_id.startswith("W"):
        clean_id = f"W{clean_id.zfill(4)}"
    return f"{prefix}_{clean_id}"


def ingest_dataset():
    """Reads dataset Excel log and WAV files, populating SQLite database."""
    print("=" * 60)
    print("STARTING DATASET INGESTION FOR BADAGA & MARWARI")
    print("=" * 60)

    init_db()
    audio_index = build_audio_file_index()
    print(f"Discovered {len(audio_index)} audio WAV files on disk.")

    if not DATASET_LOG_FILE.is_file():
        raise FileNotFoundError(f"Dataset log not found: {DATASET_LOG_FILE}")

    wb = openpyxl.load_workbook(str(DATASET_LOG_FILE), data_only=True)
    rec_sheet = wb["Recordings"]
    rows = list(rec_sheet.iter_rows(values_only=True))
    if not rows:
        print("Log sheet is empty.")
        return

    header = rows[0]
    data_rows = rows[1:]

    vocab_count = 0
    recording_count = 0
    missing_audio = []
    invalid_audio = []

    with get_db_connection() as conn:
        for idx, row in enumerate(data_rows):
            lang = row[1]
            raw_word_id = row[3]
            english = row[4]
            tamil = row[5]
            speaker_id = row[6]
            fname = row[8]
            seconds = row[10]
            note = row[12]

            if not lang or not raw_word_id or not fname:
                continue

            lang_clean = "Badaga" if "badaga" in str(lang).lower() else "Marwari"
            canonical_word_id = format_canonical_word_id(lang_clean, raw_word_id)
            clip_id = Path(fname).stem

            # Insert verified vocabulary entry
            insert_vocabulary_entry(
                word_id=canonical_word_id,
                language=lang_clean,
                tamil_meaning=str(tamil).strip() if tamil else "",
                english_meaning=str(english).strip() if english else "",
                notes=str(note) if note else None,
                verification_status="verified",
                conn=conn,
            )

            # Check matching audio file on disk
            audio_path = audio_index.get(fname)
            if not audio_path:
                missing_audio.append((canonical_word_id, fname))
                continue

            # Validate audio properties
            is_valid, msg, meta = validate_audio_file(audio_path)
            if not is_valid:
                invalid_audio.append((fname, msg))

            duration = meta.get("duration", float(seconds) if seconds else 0.0)
            sample_rate = meta.get("sample_rate", 16000)

            # Insert recording entry
            insert_recording_entry(
                clip_id=clip_id,
                word_id=canonical_word_id,
                speaker_id=str(speaker_id).strip() if speaker_id else "UNKNOWN",
                clip_file=str(audio_path),
                original_file=str(audio_path),
                start_timestamp=0.0,
                end_timestamp=duration,
                sample_rate=sample_rate,
                duration=duration,
                review_status="reviewed",
                conn=conn,
            )
            recording_count += 1

        conn.commit()

    # Query distinct counts
    with get_db_connection() as conn:
        total_vocab = conn.execute("SELECT COUNT(*) FROM vocabulary;").fetchone()[0]
        badaga_vocab = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE language='Badaga';").fetchone()[0]
        marwari_vocab = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE language='Marwari';").fetchone()[0]
        total_recs = conn.execute("SELECT COUNT(*) FROM recordings;").fetchone()[0]
        badaga_recs = conn.execute(
            "SELECT COUNT(*) FROM recordings r JOIN vocabulary v ON r.word_id = v.word_id WHERE v.language='Badaga';"
        ).fetchone()[0]
        marwari_recs = conn.execute(
            "SELECT COUNT(*) FROM recordings r JOIN vocabulary v ON r.word_id = v.word_id WHERE v.language='Marwari';"
        ).fetchone()[0]

    print("\n--- INGESTION REPORT ---")
    print(f"Total Unique Vocabulary Entries: {total_vocab} (Badaga: {badaga_vocab}, Marwari: {marwari_vocab})")
    print(f"Total Reference Recordings Ingested: {total_recs} (Badaga: {badaga_recs}, Marwari: {marwari_recs})")
    print(f"Missing audio files: {len(missing_audio)}")
    print(f"Audio files failing validation: {len(invalid_audio)}")
    if invalid_audio:
        print("Sample validation warnings:", invalid_audio[:5])
    print("=" * 60)


if __name__ == "__main__":
    ingest_dataset()
