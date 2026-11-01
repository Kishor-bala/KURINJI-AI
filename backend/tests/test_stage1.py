import os
import tempfile
import sqlite3
import numpy as np
import soundfile as sf
import pytest
from pathlib import Path

from backend.app.config import TARGET_SAMPLE_RATE
from backend.app.database.connection import get_db_connection, init_db
from backend.app.database.vocabulary import (
    insert_vocabulary_entry,
    get_vocabulary_by_id,
    list_vocabulary,
)
from backend.app.database.recordings import (
    insert_recording_entry,
    get_recording_by_id,
    list_recordings_for_word,
)
from backend.app.audio.validation import validate_audio_file, detect_excessive_silence
from backend.app.audio.preprocessing import load_and_standardize_audio, save_standardized_audio
from backend.app.audio.segmentation import (
    slice_audio_segment,
    suggest_speech_segments_vad,
    create_segment_clip,
)


def test_database_init_and_crud():
    """Verify database initialization, schema integrity, and CRUD operations."""
    init_db()

    # Test Vocabulary Insertion
    vocab = insert_vocabulary_entry(
        word_id="TEST_W0001",
        language="Badaga",
        tamil_meaning="தலை",
        english_meaning="head",
        notes="Automated test entry",
        verification_status="verified",
    )
    assert vocab is not None
    assert vocab["word_id"] == "TEST_W0001"
    assert vocab["tamil_meaning"] == "தலை"
    assert vocab["english_meaning"] == "head"

    # Test Recording Insertion
    rec = insert_recording_entry(
        clip_id="TEST_W0001_S01_01",
        word_id="TEST_W0001",
        speaker_id="S01",
        clip_file="/path/to/test.wav",
        original_file="/path/to/orig.wav",
        start_timestamp=0.5,
        end_timestamp=1.8,
        sample_rate=16000,
        duration=1.3,
        review_status="reviewed",
    )
    assert rec is not None
    assert rec["clip_id"] == "TEST_W0001_S01_01"
    assert rec["duration"] == 1.3

    # Test Retrieval
    fetched_vocab = get_vocabulary_by_id("TEST_W0001")
    assert fetched_vocab["english_meaning"] == "head"

    word_recs = list_recordings_for_word("TEST_W0001")
    assert len(word_recs) == 1
    assert word_recs[0]["speaker_id"] == "S01"

    # Clean up test records
    with get_db_connection() as conn:
        conn.execute("DELETE FROM vocabulary WHERE word_id = 'TEST_W0001';")
        conn.commit()


def test_audio_validation_and_preprocessing():
    """Verify audio file validation, mono conversion, and 16kHz resampling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sr_orig = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr_orig * duration), endpoint=False)
        # Create a stereo signal at 22050 Hz (440 Hz tone)
        left = 0.5 * np.sin(2 * np.pi * 440 * t)
        right = 0.3 * np.sin(2 * np.pi * 880 * t)
        stereo_waveform = np.stack([left, right], axis=1)

        test_file = tmp_path / "stereo_22k.wav"
        sf.write(str(test_file), stereo_waveform, sr_orig)

        # 1. Validation test
        is_valid, msg, meta = validate_audio_file(test_file)
        assert is_valid is True
        assert meta["channels"] == 2
        assert meta["sample_rate"] == 22050
        assert round(meta["duration"], 1) == 2.0

        # 2. Standardization test
        std_waveform, std_sr = load_and_standardize_audio(test_file, target_sr=16000)
        assert std_sr == 16000
        assert std_waveform.ndim == 1  # Converted to mono
        assert len(std_waveform) == 16000 * 2  # Exactly 2.0s at 16kHz

        # 3. Save standardized audio
        out_file = tmp_path / "mono_16k.wav"
        save_standardized_audio(std_waveform, out_file, sample_rate=16000)
        out_info = sf.info(str(out_file))
        assert out_info.samplerate == 16000
        assert out_info.channels == 1
        assert out_info.subtype == "PCM_16"


def test_audio_segmentation_and_vad_suggestion():
    """Verify slicing and VAD boundary suggestions on a simulated multi-utterance waveform."""
    sr = 16000
    # Create 4-second audio: [0.5s silence, 1s speech, 1s silence, 1s speech, 0.5s silence]
    audio = np.zeros(sr * 4, dtype=np.float32)
    t1 = np.linspace(0, 1.0, sr, endpoint=False)
    t2 = np.linspace(0, 1.0, sr, endpoint=False)
    # First utterance at 0.5s - 1.5s
    audio[int(0.5 * sr) : int(1.5 * sr)] = 0.5 * np.sin(2 * np.pi * 300 * t1)
    # Second utterance at 2.5s - 3.5s
    audio[int(2.5 * sr) : int(3.5 * sr)] = 0.5 * np.sin(2 * np.pi * 300 * t2)

    # Test precise slicing
    first_slice = slice_audio_segment(audio, sr, start_time=0.5, end_time=1.5)
    assert len(first_slice) == sr
    assert np.max(np.abs(first_slice)) > 0.4

    # Test VAD suggestions
    suggestions = suggest_speech_segments_vad(audio, sample_rate=sr, top_db=20.0)
    assert len(suggestions) >= 2
    # Verify candidate bounds align with speech intervals
    first_cand = suggestions[0]
    second_cand = suggestions[1]
    assert 0.3 <= first_cand[0] <= 0.6
    assert 2.3 <= second_cand[0] <= 2.6


def test_ingested_dataset_integrity():
    """Verify that the SQLite database contains all 495 words and 619 recordings."""
    with get_db_connection() as conn:
        vocab_count = conn.execute("SELECT COUNT(*) FROM vocabulary;").fetchone()[0]
        rec_count = conn.execute("SELECT COUNT(*) FROM recordings;").fetchone()[0]
        badaga_vocab = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE language='Badaga';").fetchone()[0]
        marwari_vocab = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE language='Marwari';").fetchone()[0]

        assert vocab_count == 495
        assert rec_count == 619
        assert badaga_vocab == 284
        assert marwari_vocab == 211

        # Check a known Badaga entry
        head_bdg = conn.execute("SELECT * FROM vocabulary WHERE word_id = 'BDG_W0001';").fetchone()
        assert head_bdg is not None
        assert head_bdg["english_meaning"] == "head"
        assert head_bdg["tamil_meaning"] == "தலை"

        # Check a known Marwari entry
        head_mwr = conn.execute("SELECT * FROM vocabulary WHERE word_id = 'MWR_W0001';").fetchone()
        assert head_mwr is not None
        assert head_mwr["english_meaning"] == "head"
        assert head_mwr["tamil_meaning"] == "தலை"

