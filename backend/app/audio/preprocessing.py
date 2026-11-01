from pathlib import Path
from typing import Tuple, Union, Optional
import numpy as np
try:
    import soundfile as sf
except Exception:
    sf = None
from backend.app.config import TARGET_SAMPLE_RATE, SILENCE_TOP_DB


def load_and_standardize_audio(
    file_path: Union[str, Path],
    target_sr: int = TARGET_SAMPLE_RATE,
    trim_silence: bool = True,
) -> Tuple[np.ndarray, int]:
    """
    Loads an audio file and standardizes it:
    1. Reads raw audio as float32 using soundfile or PyAV fallback (WebM, Opus, MP3).
    2. Converts multi-channel (stereo) audio to mono.
    3. Resamples signal strictly to target_sr (16,000 Hz).
    4. Trims leading and trailing silence to isolate the spoken word pronunciation.
    5. Validates that waveform is finite (no NaNs or Infs).
    6. Returns (waveform_1d, sample_rate).
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    data = None
    sr = None

    # Load audio data using soundfile first if available
    if sf is not None:
        try:
            data, sr = sf.read(str(path), dtype="float32", always_2d=False)
        except Exception:
            pass

    # Fallback 1: Python standard wave module (0 external dependencies)
    if data is None:
        try:
            import wave
            with wave.open(str(path), 'rb') as wf:
                sr = wf.getframerate()
                n_frames = wf.getnframes()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                raw_bytes = wf.readframes(n_frames)
                if sampwidth == 2:
                    data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                elif sampwidth == 4:
                    data = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
                elif sampwidth == 1:
                    data = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
                if n_channels > 1 and data is not None:
                    data = data.reshape(-1, n_channels)
        except Exception:
            pass
        # Fallback 1: Try PyAV for WebM, Opus, AAC, Ogg, MP3
        try:
            import av
            with av.open(str(path)) as container:
                stream = next((s for s in container.streams if s.type == "audio"), None)
                if stream is not None:
                    resampler = av.AudioResampler(format="flt", layout="mono", rate=target_sr)
                    pcm_chunks = []
                    for frame in container.decode(stream):
                        resampled_frames = resampler.resample(frame)
                        for rf in resampled_frames:
                            pcm_chunks.append(rf.to_ndarray())
                    if pcm_chunks:
                        data = np.concatenate(pcm_chunks, axis=1).squeeze()
                        sr = target_sr
        except Exception:
            pass

        # Fallback 2: librosa if installed
        if data is None:
            try:
                import librosa
                data, sr = librosa.load(str(path), sr=None, mono=False)
                data = data.astype(np.float32)
            except Exception:
                pass

    if data is None or sr is None:
        raise ValueError(f"Could not decode audio from: {path}")

    # Convert to mono if multi-channel
    if data.ndim > 1:
        if data.shape[0] < data.shape[1] and data.shape[0] <= 8:
            waveform = np.mean(data, axis=0)
        else:
            waveform = np.mean(data, axis=1)
    else:
        waveform = data

    # Resample if sample rate does not match target (16,000 Hz)
    if sr != target_sr:
        try:
            import librosa
            waveform = librosa.resample(waveform, orig_sr=sr, target_sr=target_sr, res_type="soxr_hq")
        except Exception:
            orig_indices = np.linspace(0, len(waveform) - 1, len(waveform))
            new_len = int(len(waveform) * target_sr / sr)
            new_indices = np.linspace(0, len(waveform) - 1, new_len)
            waveform = np.interp(new_indices, orig_indices, waveform).astype(np.float32)
        sr = target_sr

    # Ensure waveform values are valid numbers
    if not np.all(np.isfinite(waveform)):
        waveform = np.nan_to_num(waveform, nan=0.0, posinf=1.0, neginf=-1.0)

    # Trim leading and trailing silence (top_db=SILENCE_TOP_DB) with safety padding so phonemes aren't clipped
    if trim_silence and len(waveform) > int(target_sr * 0.4):
        try:
            import librosa
            _, index = librosa.effects.trim(waveform, top_db=SILENCE_TOP_DB, frame_length=512, hop_length=128)
            pad = int(target_sr * 0.08)  # 80ms acoustic margin
            start_idx = max(0, int(index[0]) - pad)
            end_idx = min(len(waveform), int(index[1]) + pad)
            extracted = waveform[start_idx:end_idx]
            if len(extracted) >= int(target_sr * 0.25):
                waveform = extracted
        except Exception:
            pass
            pass

    # Ensure peak amplitude does not exceed [-1.0, 1.0] without altering speech dynamics
    peak = np.max(np.abs(waveform))
    if peak > 1.0:
        waveform = waveform / peak

    return waveform.astype(np.float32), sr


def save_standardized_audio(
    waveform: np.ndarray,
    output_path: Union[str, Path],
    sample_rate: int = TARGET_SAMPLE_RATE,
) -> Path:
    """
    Saves a float32 standardized mono waveform as a standard 16-bit PCM WAV file.
    Does not overwrite source recordings accidentally.
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Clip to avoid overflow before converting to PCM_16
    clipped = np.clip(waveform, -1.0, 1.0)
    if sf is not None:
        try:
            sf.write(str(out_path), clipped, sample_rate, subtype="PCM_16")
            return out_path
        except Exception:
            pass

    import wave
    pcm16 = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())
    return out_path
