import numpy as np
import pytest
from backend.app.matching.cosine_similarity import compute_cosine_similarity
from backend.app.matching.candidate_ranking import (
    aggregate_reference_scores,
    rank_candidates,
)
from backend.app.matching.rejection import evaluate_recognition_decision
from backend.app.embeddings.extraction import pool_frame_representations
import torch


def test_cosine_similarity_properties():
    """Verify exact mathematical properties of cosine similarity."""
    # 1. Identical vectors -> 1.0
    v1 = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    assert np.isclose(compute_cosine_similarity(v1, v1), 1.0, atol=1e-5)

    # 2. Opposite vectors -> -1.0
    v2 = -v1
    assert np.isclose(compute_cosine_similarity(v1, v2), -1.0, atol=1e-5)

    # 3. Orthogonal vectors -> 0.0
    v_orth1 = np.array([1.0, 0.0], dtype=np.float32)
    v_orth2 = np.array([0.0, 1.0], dtype=np.float32)
    assert np.isclose(compute_cosine_similarity(v_orth1, v_orth2), 0.0, atol=1e-5)

    # 4. Matrix of reference vectors
    matrix = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]], dtype=np.float32)
    sims = compute_cosine_similarity(v_orth1, matrix)
    assert len(sims) == 3
    assert np.isclose(sims[0], 1.0, atol=1e-5)
    assert np.isclose(sims[1], 0.0, atol=1e-5)
    assert np.isclose(sims[2], -1.0, atol=1e-5)


def test_score_aggregation_methods():
    """Verify max, average, and top3_average aggregation across multiple exemplars."""
    scores = [0.60, 0.90, 0.70, 0.80]

    # Max should be 0.90
    assert np.isclose(aggregate_reference_scores(scores, method="max"), 0.90)

    # Average should be 0.75
    assert np.isclose(aggregate_reference_scores(scores, method="average"), 0.75)

    # Top-3 average (0.90 + 0.80 + 0.70) / 3 = 0.80
    assert np.isclose(aggregate_reference_scores(scores, method="top3_average"), 0.80)


def test_candidate_ranking_and_grouping():
    """Verify that multiple recordings for the same word are grouped and ranked correctly."""
    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)

    refs = [
        # Word A: 2 clips
        {
            "clip_id": "clip_A1",
            "word_id": "BDG_W0001",
            "language": "Badaga",
            "tamil_meaning": "தலை",
            "english_meaning": "head",
            "speaker_id": "S01",
            "vector": np.array([0.95, 0.05, 0.0], dtype=np.float32),
        },
        {
            "clip_id": "clip_A2",
            "word_id": "BDG_W0001",
            "language": "Badaga",
            "tamil_meaning": "தலை",
            "english_meaning": "head",
            "speaker_id": "S02",
            "vector": np.array([0.80, 0.20, 0.0], dtype=np.float32),
        },
        # Word B: 1 clip
        {
            "clip_id": "clip_B1",
            "word_id": "BDG_W0002",
            "language": "Badaga",
            "tamil_meaning": "கண்",
            "english_meaning": "eye",
            "speaker_id": "S01",
            "vector": np.array([0.10, 0.90, 0.0], dtype=np.float32),
        },
    ]

    ranked = rank_candidates(query, refs, aggregation_method="max")
    assert len(ranked) == 2
    assert ranked[0]["word_id"] == "BDG_W0001"
    assert ranked[0]["score"] > 0.90
    assert len(ranked[0]["clip_matches"]) == 2

    assert ranked[1]["word_id"] == "BDG_W0002"
    assert ranked[1]["score"] < 0.20


def test_unknown_word_rejection_and_uncertainty():
    """Verify rejection of low-similarity audio and detection of uncertain margins."""
    threshold = 0.70
    margin_req = 0.05

    # 1. Recognized case
    recog_candidates = [
        {"word_id": "BDG_W0001", "score": 0.88},
        {"word_id": "BDG_W0002", "score": 0.65},
    ]
    res1 = evaluate_recognition_decision(recog_candidates, threshold, margin_req)
    assert res1["status"] == "recognized"
    assert res1["top_candidate"]["word_id"] == "BDG_W0001"

    # 2. Unknown word case (best score below threshold)
    unknown_candidates = [
        {"word_id": "BDG_W0001", "score": 0.52},
        {"word_id": "BDG_W0002", "score": 0.48},
    ]
    res2 = evaluate_recognition_decision(unknown_candidates, threshold, margin_req)
    assert res2["status"] == "unknown"
    assert res2["best_score"] == 0.52

    # 3. Uncertain case (score >= threshold, but margin < margin_req)
    uncertain_candidates = [
        {"word_id": "BDG_W0001", "score": 0.78},
        {"word_id": "BDG_W0002", "score": 0.76},  # margin = 0.02 < 0.05
    ]
    res3 = evaluate_recognition_decision(uncertain_candidates, threshold, margin_req)
    assert res3["status"] == "uncertain"
    assert res3["margin"] == 0.02


def test_mean_pooling_and_l2_normalization():
    """Verify mean pooling over valid frames and unit L2 length."""
    # 2 time frames, hidden dim = 4
    hidden = torch.tensor([[[2.0, 0.0, 0.0, 0.0], [4.0, 0.0, 0.0, 0.0]]], dtype=torch.float32)
    mask = torch.tensor([[1, 1]], dtype=torch.long)

    pooled = pool_frame_representations(hidden, valid_mask=mask, method="mean")
    assert pooled.shape == (4,)
    # Norm must be 1.0
    assert np.isclose(np.linalg.norm(pooled), 1.0, atol=1e-5)
    # Mean of 2.0 and 4.0 is 3.0, normalized -> [1.0, 0, 0, 0]
    assert np.isclose(pooled[0], 1.0, atol=1e-5)
