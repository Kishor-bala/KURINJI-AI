import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import TARGET_SAMPLE_RATE
from backend.app.database.connection import get_db_connection

client = TestClient(app)


def test_health_endpoint():
    """Verify that /api/health responds with healthy status and metadata counts."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "facebook/wav2vec2-xls-r-300m" in data["encoder"]
    assert data["counts"]["vocabulary"] >= 495
    assert data["counts"]["recordings"] >= 619


def test_vocabulary_list_and_filter():
    """Verify listing and filtering vocabulary by language."""
    # List all
    res_all = client.get("/api/vocabulary?limit=10")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["total"] >= 495
    assert len(data_all["entries"]) == 10

    # Filter Badaga
    res_bdg = client.get("/api/vocabulary?language=Badaga&limit=5")
    assert res_bdg.status_code == 200
    data_bdg = res_bdg.json()
    assert data_bdg["total"] == 284
    assert all(e["language"] == "Badaga" for e in data_bdg["entries"])

    # Filter Marwari
    res_mwr = client.get("/api/vocabulary?language=Marwari&limit=5")
    assert res_mwr.status_code == 200
    data_mwr = res_mwr.json()
    assert data_mwr["total"] == 211
    assert all(e["language"] == "Marwari" for e in data_mwr["entries"])


def test_add_and_retrieve_vocabulary():
    """Verify adding a verified entry and retrieving its detail."""
    new_entry = {
        "word_id": "BDG_TEST_W9999",
        "language": "Badaga",
        "tamil_meaning": "சோதனை",
        "english_meaning": "test",
        "notes": "Automated API test word",
        "verification_status": "verified",
    }
    post_res = client.post("/api/vocabulary", json=new_entry)
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "success"

    # Retrieve
    get_res = client.get("/api/vocabulary/BDG_TEST_W9999")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["vocabulary"]["english_meaning"] == "test"
    assert detail["vocabulary"]["tamil_meaning"] == "சோதனை"


def test_audio_upload_and_vad_suggestions():
    """Verify uploading an audio file and receiving VAD segment suggestions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a 2-second WAV file with two distinct tone pulses
        sr = 16000
        audio = np.zeros(sr * 2, dtype=np.float32)
        audio[int(0.2 * sr) : int(0.7 * sr)] = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, int(0.5 * sr)))
        audio[int(1.2 * sr) : int(1.7 * sr)] = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, int(0.5 * sr)))

        temp_wav = Path(tmpdir) / "sample_speech.wav"
        sf.write(str(temp_wav), audio, sr)

        with open(temp_wav, "rb") as f:
            upload_res = client.post(
                "/api/audio/upload",
                files={"file": ("sample_speech.wav", f, "audio/wav")},
            )

        assert upload_res.status_code == 200
        data = upload_res.json()
        assert data["status"] == "success"
        assert data["sample_rate"] == 16000
        assert "vad_suggestions" in data
        assert len(data["vad_suggestions"]) >= 1

        # Test segmenting the uploaded audio
        segment_req = {
            "file_path": data["file_path"],
            "start_time": 0.2,
            "end_time": 0.7,
            "clip_id": "API_TEST_SEGMENT_01",
            "word_id": "BDG_TEST_W9999",
            "speaker_id": "S_TEST",
        }
        seg_res = client.post("/api/audio/segment", json=segment_req)
        assert seg_res.status_code == 200
        seg_data = seg_res.json()
        assert seg_data["status"] == "success"
        assert seg_data["recording"]["clip_id"] == "API_TEST_SEGMENT_01"

        # Clean up test records
        with get_db_connection() as conn:
            conn.execute("DELETE FROM recordings WHERE clip_id = 'API_TEST_SEGMENT_01';")
            conn.execute("DELETE FROM vocabulary WHERE word_id = 'BDG_TEST_W9999';")
            conn.commit()
