import torch
import numpy as np
from typing import Optional, Tuple
from backend.app.models.xlsr_encoder import XLSREncoder
from backend.app.config import TARGET_SAMPLE_RATE, DEFAULT_POOLING_METHOD


def pool_frame_representations(
    hidden_states: torch.Tensor,
    valid_mask: Optional[torch.Tensor] = None,
    method: str = DEFAULT_POOLING_METHOD,
) -> np.ndarray:
    """
    Performs pooling over valid audio frames to generate a single representation vector.
    Applies L2 normalization.

    Args:
        hidden_states: Tensor of shape (batch_size, T, hidden_dim).
        valid_mask: Tensor of shape (batch_size, T) indicating unpadded frames.
        method: Pooling method, currently 'mean' baseline.

    Returns:
        1D numpy array of shape (hidden_dim,) with L2 norm = 1.0.
    """
    # Ensure shapes: (1, T, D)
    if hidden_states.ndim == 2:
        hidden_states = hidden_states.unsqueeze(0)

    batch_size, time_steps, hidden_dim = hidden_states.shape

    if valid_mask is None:
        valid_mask = torch.ones((batch_size, time_steps), device=hidden_states.device)

    # Expand mask to (batch_size, time_steps, 1) for broadcasting
    expanded_mask = valid_mask.unsqueeze(-1).float()

    if method == "mean":
        # Sum valid frames and divide by valid frame count
        summed = torch.sum(hidden_states * expanded_mask, dim=1)  # Shape: (batch_size, hidden_dim)
        counts = torch.sum(expanded_mask, dim=1).clamp(min=1.0)
        pooled = summed / counts
    else:
        raise ValueError(f"Unsupported pooling method: {method}. Baseline supported is 'mean'.")

    # Squeeze batch dimension for single utterance
    vector = pooled.squeeze(0).cpu().numpy().astype(np.float32)

    # Apply strict L2 Normalization
    norm = np.linalg.norm(vector)
    if norm > 1e-8:
        normalized_vector = vector / norm
    else:
        normalized_vector = vector

    return normalized_vector


def extract_audio_embedding(
    waveform: np.ndarray,
    sample_rate: int = TARGET_SAMPLE_RATE,
    pooling_method: str = DEFAULT_POOLING_METHOD,
    return_frame_representations: bool = False,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    End-to-end pipeline to compute a normalized XLS-R embedding from raw waveform.

    Returns:
        (pooled_embedding_1024d, optional_frame_representations)
    """
    encoder = XLSREncoder.get_instance()
    hidden_states, frame_mask = encoder.extract_hidden_states(waveform, sample_rate=sample_rate)

    pooled_embedding = pool_frame_representations(
        hidden_states=hidden_states,
        valid_mask=frame_mask,
        method=pooling_method,
    )

    frame_reps = None
    if return_frame_representations:
        frame_reps = hidden_states.squeeze(0).cpu().numpy().astype(np.float32)

    return pooled_embedding, frame_reps
