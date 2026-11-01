from typing import List, Dict, Any, Optional
from backend.app.config import DEFAULT_SIMILARITY_THRESHOLD, DEFAULT_MARGIN_THRESHOLD


def evaluate_recognition_decision(
    ranked_candidates: List[Dict[str, Any]],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
) -> Dict[str, Any]:
    """
    Applies calibrated acceptance, uncertainty, and unknown-word rejection logic.

    Rules:
        - If candidates is empty -> 'unknown'
        - If best_score < similarity_threshold -> 'unknown'
        - If best_score >= similarity_threshold and margin >= margin_threshold -> 'recognized'
        - If best_score >= similarity_threshold and margin < margin_threshold -> 'uncertain'
          (Ambiguous match between top two words: requests another recording).

    Returns:
        Structured recognition decision dictionary.
    """
    if not ranked_candidates:
        return {
            "status": "unknown",
            "message": "No vocabulary candidates found for comparison.",
            "top_candidate": None,
            "best_score": 0.0,
            "second_score": 0.0,
            "margin": 0.0,
            "ranked_candidates": [],
        }

    top_candidate = ranked_candidates[0]
    best_score = float(top_candidate["score"])

    second_score = 0.0
    if len(ranked_candidates) > 1:
        second_score = float(ranked_candidates[1]["score"])

    margin = round(best_score - second_score, 4)

    # Condition 1: Unknown word rejection
    if best_score < similarity_threshold:
        return {
            "status": "unknown",
            "message": (
                f"Audio not recognized as a known word. "
                f"Best similarity ({best_score:.3f}) is below threshold ({similarity_threshold:.3f})."
            ),
            "top_candidate": None,
            "best_score": best_score,
            "second_score": second_score,
            "margin": margin,
            "ranked_candidates": ranked_candidates[:3],
        }

    # Condition 2: Uncertain result (margin between top-1 and top-2 is too narrow)
    if len(ranked_candidates) > 1 and margin < margin_threshold:
        return {
            "status": "uncertain",
            "message": (
                f"Ambiguous match between '{top_candidate['word_id']}' and "
                f"'{ranked_candidates[1]['word_id']}' (margin {margin:.3f} < {margin_threshold:.3f}). "
                "Please provide another recording to confirm pronunciation."
            ),
            "top_candidate": top_candidate,
            "second_candidate": ranked_candidates[1],
            "best_score": best_score,
            "second_score": second_score,
            "margin": margin,
            "ranked_candidates": ranked_candidates[:3],
        }

    # Condition 3: Confidently recognized
    return {
        "status": "recognized",
        "message": "Word identified successfully with verified vocabulary entry.",
        "top_candidate": top_candidate,
        "second_candidate": ranked_candidates[1] if len(ranked_candidates) > 1 else None,
        "best_score": best_score,
        "second_score": second_score,
        "margin": margin,
        "ranked_candidates": ranked_candidates[:5],
    }
