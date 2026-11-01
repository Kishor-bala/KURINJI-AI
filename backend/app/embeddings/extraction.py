import numpy as np
from typing import Optional, Tuple, Any
from backend.app.config import TARGET_SAMPLE_RATE, DEFAULT_POOLING_METHOD

try:
    import torch
    from backend.app.models.xlsr_encoder import XLSREncoder
    HAS_TORCH = True
except (ImportError, Exception):
    torch = None
    XLSREncoder = None
    HAS_TORCH = False


def pool_frame_representations(
    hidden_states: Any,
    valid_mask: Optional[Any] = None,
    method: str = DEFAULT_POOLING_METHOD,
) -> np.ndarray:
    """
    Performs pooling over valid audio frames to generate a single representation vector.
    Applies L2 normalization.
    """
    if not HAS_TORCH or torch is None:
        raise RuntimeError("PyTorch is not available.")

    # Ensure shapes: (1, T, D)
    if hidden_states.ndim == 2:
        hidden_states = hidden_states.unsqueeze(0)

    batch_size, time_steps, hidden_dim = hidden_states.shape

    if valid_mask is None:
        valid_mask = torch.ones((batch_size, time_steps), device=hidden_states.device)

    # Expand mask to (batch_size, time_steps, 1) for broadcasting
    expanded_mask = valid_mask.unsqueeze(-1).float()

    if method == "mean":
        summed = torch.sum(hidden_states * expanded_mask, dim=1)
        counts = torch.sum(expanded_mask, dim=1).clamp(min=1.0)
        pooled = summed / counts
    else:
        raise ValueError(f"Unsupported pooling method: {method}. Baseline supported is 'mean'.")

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
    """
    if not HAS_TORCH or XLSREncoder is None:
        raise RuntimeError(
            "Local XLS-R PyTorch encoder is not available in lightweight serverless mode. "
            "Please configure GEMINI_API_KEY in your Vercel environment variables for speech recognition."
        )

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
