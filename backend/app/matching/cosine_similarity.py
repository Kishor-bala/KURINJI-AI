import numpy as np
from typing import Union


def compute_cosine_similarity(
    query_vec: np.ndarray,
    ref_vecs: np.ndarray,
) -> np.ndarray:
    """
    Computes true cosine similarity between a single query vector
    and one or more reference vectors:
        similarity(A, B) = dot(A, B) / (||A|| * ||B||)

    Args:
        query_vec: 1D array of shape (D,).
        ref_vecs: 1D array of shape (D,) or 2D array of shape (N, D).

    Returns:
        1D array of shape (N,) containing cosine similarity scores in [-1.0, 1.0].
        Scores are NOT treated as percentage probabilities.
    """
    if query_vec.ndim != 1:
        query_vec = query_vec.flatten()

    is_single_ref = ref_vecs.ndim == 1
    if is_single_ref:
        ref_matrix = ref_vecs.reshape(1, -1)
    else:
        ref_matrix = ref_vecs

    # Compute norms
    query_norm = np.linalg.norm(query_vec)
    ref_norms = np.linalg.norm(ref_matrix, axis=1)

    # Guard against zero-division
    if query_norm < 1e-10:
        return np.zeros(ref_matrix.shape[0], dtype=np.float32)

    ref_norms = np.where(ref_norms < 1e-10, 1e-10, ref_norms)

    # Dot products
    dot_products = np.dot(ref_matrix, query_vec)

    # Cosine similarities
    similarities = dot_products / (ref_norms * query_norm)

    # Clamp numerical precision to [-1.0, 1.0]
    similarities = np.clip(similarities, -1.0, 1.0).astype(np.float32)

    return similarities[0] if is_single_ref else similarities
