import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
import pytest

from backend.app.config import DATASET_BADAGA_DIR, TARGET_SAMPLE_RATE
from backend.app.services.recognition import recognize_spoken_word


def test_real_audio_recognition_lookup():
    """
    Tests recognition of a real Badaga audio file against the verified reference wordbank.
    Verifies that the predicted Word ID and human-verified Tamil and English meanings match.
    """
    sample_wav = DATASET_BADAGA_DIR / "P01" / "BDG_P01_W0001_S01.wav"
    assert sample_wav.is_file(), f"Sample audio missing: {sample_wav}"

    result = recognize_spoken_word(
        audio_input=sample_wav,
        language="Badaga",
        similarity_threshold=0.80,
        margin_threshold=0.05,
    )

    assert result["status"] == "recognized"
    assert result["word_id"] == "BDG_W0001"
    assert result["language"] == "Badaga"
    assert result["tamil_meaning"] == "தலை"
    assert result["english_meaning"] == "head"
    assert result["similarity"] > 0.85
    assert len(result["ranked_candidates"]) > 0


def test_unknown_audio_rejection():
    """
    Tests that non-word audio (random Gaussian noise) is correctly rejected as 'unknown'
    and does not produce a false positive match.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        noise_wav = Path(tmpdir) / "synthetic_noise.wav"
        # 1.5 seconds of Gaussian white noise
        sr = TARGET_SAMPLE_RATE
        np.random.seed(42)
        noise = (0.02 * np.random.randn(int(1.5 * sr))).astype(np.float32)
        sf.write(str(noise_wav), noise, sr)

        result = recognize_spoken_word(
            audio_input=noise_wav,
            language="Badaga",
            similarity_threshold=0.80,
        )

        # White noise must be rejected as unknown (or excessive silence if low amplitude)
        assert result["status"] in ("unknown", "excessive_silence")
        assert result["word_id"] is None
        assert result["tamil_meaning"] is None
        assert result["english_meaning"] is None
