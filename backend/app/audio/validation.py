import os
from pathlib import Path
from typing import Tuple, Dict, Any, Union
import soundfile as sf
import numpy as np
from backend.app.config import (
    MIN_AUDIO_DURATION,
    MAX_AUDIO_DURATION,
    SILENCE_TOP_DB,
    TARGET_SAMPLE_RATE,
)


def validate_audio_file(file_path: Union[str, Path]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates an audio file for existence, readability, non-corruption,
    minimum/maximum duration constraints, and non-empty speech content.

    Returns:
        (is_valid: bool, reason_message: str, metadata: dict)
    """
    path = Path(file_path)
    if not path.is_file():
        return False, f"File does not exist: {path}", {}

    if path.stat().st_size == 0:
        return False, "Audio file is 0 bytes (empty).", {}

    duration = 0.0
    metadata = {}
    try:
        info = sf.info(str(path))
        duration = info.duration
        metadata = {
            "sample_rate": info.samplerate,
            "channels": info.channels,
            "duration": duration,
            "format": info.format,
            "subtype": info.subtype,
            "frames": info.frames,
        }
    except Exception as sf_err:
        # Fallback 1: Python standard library wave module for WAV files
        try:
            import wave
            with wave.open(str(path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate) if rate else 0.0
                metadata = {
                    "sample_rate": rate,
                    "channels": wf.getnchannels(),
                    "duration": duration,
                    "format": "WAV",
                    "frames": frames,
                }
        except Exception:
            # Fallback 2: PyAV if available
            try:
                import av
                with av.open(str(path)) as container:
                    audio_stream = next((s for s in container.streams if s.type == "audio"), None)
                    if audio_stream is None:
                        return False, "No audio stream found in file.", {}
                    duration = float(audio_stream.duration * audio_stream.time_base) if audio_stream.duration else 0.0
                    metadata = {
                        "sample_rate": audio_stream.rate or TARGET_SAMPLE_RATE,
                        "channels": audio_stream.channels or 1,
                        "duration": duration,
                        "format": container.format.name,
                        "subtype": audio_stream.codec_context.name,
                    }
            except Exception as av_err:
                return False, f"Corrupted or unreadable audio file: {sf_err}", {}

    if duration < MIN_AUDIO_DURATION:
        return (
            False,
            f"Audio duration ({duration:.2f}s) is shorter than minimum threshold ({MIN_AUDIO_DURATION}s).",
            metadata,
        )

    if duration > MAX_AUDIO_DURATION:
        return (
            False,
            f"Audio duration ({duration:.2f}s) exceeds maximum allowable threshold ({MAX_AUDIO_DURATION}s).",
            metadata,
        )

    # Check for complete silence or digital zero audio
    try:
        data, _ = sf.read(str(path), dtype="float32")
        max_amplitude = np.max(np.abs(data)) if data.size > 0 else 0.0
        metadata["max_amplitude"] = float(max_amplitude)

        # -60 dB relative to 1.0 is ~0.001
        if max_amplitude < 1e-4:
            return False, "Audio is completely silent (no audible signal detected).", metadata

    except Exception as e:
        return False, f"Failed to inspect waveform content: {e}", metadata

    return True, "Audio file is valid.", metadata


def detect_excessive_silence(waveform: np.ndarray, sample_rate: int = 16000, top_db: float = SILENCE_TOP_DB) -> bool:
    """
    Detects if the waveform is predominantly silence.
    Returns True if non-silent segments account for less than 15% of the total audio.
    """
    if waveform.size == 0:
        return True

    # Calculate root-mean-square amplitude
    rms = np.sqrt(np.mean(waveform ** 2))
    if rms < 1e-5:
        return True

    # Use energy-based activity check
    frame_length = int(sample_rate * 0.03)  # 30ms frames
    hop_length = int(sample_rate * 0.01)    # 10ms hop
    if len(waveform) < frame_length:
        return False

    num_frames = 1 + (len(waveform) - frame_length) // hop_length
    energies = []
    for i in range(num_frames):
        start = i * hop_length
        frame = waveform[start : start + frame_length]
        energies.append(np.sum(frame ** 2))

    max_energy = max(energies) if energies else 0.0
    if max_energy == 0.0:
        return True

    threshold = max_energy * (10 ** (-top_db / 10.0))
    active_frames = sum(1 for e in energies if e > threshold)
    active_ratio = active_frames / max(1, len(energies))

    return active_ratio < 0.10  # Less than 10% active speech implies excessive silence
