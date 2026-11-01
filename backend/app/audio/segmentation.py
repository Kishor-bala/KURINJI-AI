from pathlib import Path
from typing import List, Tuple, Union, Optional
import numpy as np
from backend.app.config import TARGET_SAMPLE_RATE
from backend.app.audio.preprocessing import load_and_standardize_audio, save_standardized_audio


def slice_audio_segment(
    waveform: np.ndarray,
    sample_rate: int,
    start_time: float,
    end_time: Optional[float] = None,
) -> np.ndarray:
    """
    Slices a waveform segment between start_time and end_time (in seconds).
    Ensures safe boundary checks and non-cropping of audio samples.
    """
    start_sample = max(0, int(round(start_time * sample_rate)))
    total_samples = len(waveform)

    if end_time is not None:
        end_sample = min(total_samples, int(round(end_time * sample_rate)))
    else:
        end_sample = total_samples

    if start_sample >= end_sample:
        raise ValueError(
            f"Invalid slice range: start ({start_time}s -> sample {start_sample}) "
            f"must be less than end ({end_time}s -> sample {end_sample})"
        )

    return waveform[start_sample:end_sample]


def suggest_speech_segments_vad(
    waveform: np.ndarray,
    sample_rate: int = TARGET_SAMPLE_RATE,
    top_db: float = 25.0,
    min_speech_duration: float = 0.35,
    min_silence_duration: float = 0.25,
) -> List[Tuple[float, float]]:
    """
    Optional helper: analyzes speech activity using energy/envelope thresholds
    to propose candidate start and end timestamps.

    NOTE per Section 2.3: This provides SUGGESTIONS only.
    It does not automatically commit splits without manual review.
    """
    if len(waveform) == 0:
        return []

    try:
        import librosa
        hop_length = int(sample_rate * 0.01)  # 10ms
        frame_length = int(sample_rate * 0.025)  # 25ms

        intervals = librosa.effects.split(
            waveform,
            top_db=top_db,
            frame_length=frame_length,
            hop_length=hop_length,
        )
    except Exception:
        duration = len(waveform) / sample_rate
        return [(0.0, duration)]

    if len(intervals) == 0:
        # Fallback to entire duration if no distinct silent split detected
        duration = len(waveform) / sample_rate
        return [(0.0, duration)]

    # Merge intervals separated by less than min_silence_duration
    min_silence_samples = int(min_silence_duration * sample_rate)
    min_speech_samples = int(min_speech_duration * sample_rate)

    merged = []
    current_start, current_end = intervals[0]

    for next_start, next_end in intervals[1:]:
        silence_gap = next_start - current_end
        if silence_gap < min_silence_samples:
            # Merge intervals
            current_end = next_end
        else:
            if (current_end - current_start) >= min_speech_samples:
                merged.append((current_start, current_end))
            current_start, current_end = next_start, next_end

    if (current_end - current_start) >= min_speech_samples:
        merged.append((current_start, current_end))

    # If all merged intervals were filtered out, fallback to entire range
    if not merged:
        merged = [(0, len(waveform))]

    # Convert sample indices to timestamps in seconds with small padding (50ms)
    padding_samples = int(sample_rate * 0.05)
    suggestions = []
    for s_idx, e_idx in merged:
        padded_start = max(0, s_idx - padding_samples) / sample_rate
        padded_end = min(len(waveform), e_idx + padding_samples) / sample_rate
        suggestions.append((round(padded_start, 3), round(padded_end, 3)))

    return suggestions


def create_segment_clip(
    original_audio_path: Union[str, Path],
    start_time: float,
    end_time: float,
    output_clip_path: Union[str, Path],
    target_sr: int = TARGET_SAMPLE_RATE,
) -> Tuple[Path, float]:
    """
    Loads original audio, standardizes to 16 kHz mono, extracts the exact timestamp slice,
    and writes the segmented clip to output_clip_path.
    Returns (saved_clip_path, duration_seconds).
    """
    waveform, sr = load_and_standardize_audio(original_audio_path, target_sr=target_sr)
    segment_waveform = slice_audio_segment(waveform, sr, start_time, end_time)
    duration = len(segment_waveform) / float(sr)

    saved_path = save_standardized_audio(segment_waveform, output_clip_path, sample_rate=sr)
    return saved_path, duration
