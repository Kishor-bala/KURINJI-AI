from collections import defaultdict
from typing import List, Dict, Any, Optional
import numpy as np
from backend.app.config import RECOGNITION_AGGREGATION_METHOD, USE_EMBEDDING_CENTERING
from backend.app.matching.cosine_similarity import compute_cosine_similarity


def aggregate_reference_scores(
    scores: List[float],
    method: str = RECOGNITION_AGGREGATION_METHOD,
) -> float:
    """
    Aggregates similarity scores across multiple reference clips for a single Word ID.

    Methods:
        - 'max': Maximum reference similarity (picks closest exemplar).
        - 'average': Average across all reference clips for this word.
        - 'top3_average': Average of up to 3 highest scoring reference clips.
    """
    if not scores:
        return 0.0

    scores_arr = np.array(scores, dtype=np.float32)

    if method == "max":
        return float(np.max(scores_arr))
    elif method == "average":
        return float(np.mean(scores_arr))
    elif method == "top3_average":
        top_k = min(3, len(scores_arr))
        # Top-k largest values
        partitioned = np.partition(scores_arr, -top_k)[-top_k:]
        return float(np.mean(partitioned))
    else:
        raise ValueError(f"Unknown aggregation method: {method}")


def rank_candidates(
    query_vector: np.ndarray,
    reference_entries: List[Dict[str, Any]],
    aggregation_method: str = RECOGNITION_AGGREGATION_METHOD,
    use_centering: bool = USE_EMBEDDING_CENTERING,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    Compares query vector against all reference entries, groups by Word ID,
    computes the aggregated similarity score, and returns sorted candidates.

    Args:
        query_vector: 1D array of shape (1024,).
        reference_entries: List of dicts, each containing:
            {'clip_id', 'word_id', 'language', 'tamil_meaning', 'english_meaning', 'speaker_id', 'vector'}
        aggregation_method: 'max', 'average', or 'top3_average'.
        use_centering: If True, centers representations by subtracting the reference centroid.
        top_n: Number of candidates to return.

    Returns:
        Sorted list of candidate dicts with ranked scores.
    """
    if not reference_entries:
        return []

    # Stack reference vectors into a 2D matrix
    ref_vectors = np.stack([entry["vector"] for entry in reference_entries], axis=0)

    if use_centering and len(reference_entries) > 1:
        # Subtract reference centroid to eliminate Transformer anisotropy cone
        centroid = np.mean(ref_vectors, axis=0)
        centered_refs = ref_vectors - centroid
        ref_norms = np.linalg.norm(centered_refs, axis=1, keepdims=True)
        centered_refs = centered_refs / np.maximum(ref_norms, 1e-8)

        centered_query = query_vector - centroid
        query_norm = np.linalg.norm(centered_query)
        centered_query = centered_query / max(query_norm, 1e-8)

        raw_similarities = compute_cosine_similarity(centered_query, centered_refs)
    else:
        raw_similarities = compute_cosine_similarity(query_vector, ref_vectors)

    # Group scores by canonical Word ID
    word_groups = defaultdict(lambda: {
        "word_id": None,
        "language": None,
        "tamil_meaning": None,
        "english_meaning": None,
        "clip_matches": [],
    })

    for idx, entry in enumerate(reference_entries):
        word_id = entry["word_id"]
        group = word_groups[word_id]
        if group["word_id"] is None:
            group["word_id"] = word_id
            group["language"] = entry["language"]
            group["tamil_meaning"] = entry["tamil_meaning"]
            group["english_meaning"] = entry["english_meaning"]

        group["clip_matches"].append({
            "clip_id": entry["clip_id"],
            "speaker_id": entry.get("speaker_id"),
            "similarity": float(raw_similarities[idx]),
        })

    # Compute aggregated score for each word candidate
    ranked_list = []
    for word_id, group in word_groups.items():
        all_sims = [m["similarity"] for m in group["clip_matches"]]
        agg_score = aggregate_reference_scores(all_sims, method=aggregation_method)

        # Sort clip matches descending by individual similarity
        group["clip_matches"].sort(key=lambda x: x["similarity"], reverse=True)
        group["score"] = round(agg_score, 4)
        group["best_clip_similarity"] = round(float(np.max(all_sims)), 4)
        ranked_list.append(group)

    # Sort candidates descending by aggregated score
    ranked_list.sort(key=lambda x: x["score"], reverse=True)

    return ranked_list[:top_n]
