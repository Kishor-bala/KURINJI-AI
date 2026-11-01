from pathlib import Path
from typing import Tuple, Union, Optional
import numpy as np
import soundfile as sf
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    librosa = None
    HAS_LIBROSA = False
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
    3. Resamples signal strictly to target_sr (16,000 Hz) using librosa.resample.
    4. Trims leading and trailing silence to isolate the spoken word pronunciation.
    5. Validates that waveform is finite (no NaNs or Infs).
    6. Returns (waveform_1d, sample_rate).
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    data = None
    sr = None

    # Load audio data using soundfile first (faster, reliable PCM decoding)
    try:
        data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    except Exception:
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

        # Fallback 2: librosa
        if data is None:
            data, sr = librosa.load(str(path), sr=None, mono=False)
            data = data.astype(np.float32)

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
        if HAS_LIBROSA:
            waveform = librosa.resample(waveform, orig_sr=sr, target_sr=target_sr, res_type="soxr_hq")
        else:
            new_len = int(round(len(waveform) * (float(target_sr) / float(sr))))
            old_indices = np.linspace(0, len(waveform) - 1, len(waveform))
            new_indices = np.linspace(0, len(waveform) - 1, new_len)
            waveform = np.interp(new_indices, old_indices, waveform).astype(np.float32)
        sr = target_sr

    # Ensure waveform values are valid numbers
    if not np.all(np.isfinite(waveform)):
        waveform = np.nan_to_num(waveform, nan=0.0, posinf=1.0, neginf=-1.0)

    # Trim leading and trailing silence (top_db=SILENCE_TOP_DB) with safety padding so phonemes aren't clipped
    if trim_silence and len(waveform) > int(target_sr * 0.4):
        try:
            if HAS_LIBROSA:
                _, index = librosa.effects.trim(waveform, top_db=SILENCE_TOP_DB, frame_length=512, hop_length=128)
                pad = int(target_sr * 0.08)  # 80ms acoustic margin
                start_idx = max(0, int(index[0]) - pad)
                end_idx = min(len(waveform), int(index[1]) + pad)
                extracted = waveform[start_idx:end_idx]
                if len(extracted) >= int(target_sr * 0.25):
                    waveform = extracted
            else:
                abs_signal = np.abs(waveform)
                threshold = max(float(np.max(abs_signal) * 0.02), 1e-4)
                non_silent = np.where(abs_signal > threshold)[0]
                if len(non_silent) > 0:
                    pad = int(target_sr * 0.08)
                    start_idx = max(0, non_silent[0] - pad)
                    end_idx = min(len(waveform), non_silent[-1] + pad)
                    extracted = waveform[start_idx:end_idx]
                    if len(extracted) >= int(target_sr * 0.25):
                        waveform = extracted
        except Exception:
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
    sf.write(str(out_path), clipped, sample_rate, subtype="PCM_16")
    return out_path
