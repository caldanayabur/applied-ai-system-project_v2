"""
End-to-end tests for the RAG recommendation pipeline.

These tests verify that the full recommendation flow works correctly,
including RAG context building and LLM integration.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.recommender import load_songs, recommend_songs, recommend_songs_with_rag
from src.rag_context import RAGContextBuilder, build_rag_context
from src.llm_engine import LLMEngine


def test_load_songs():
    """Test that songs can be loaded from CSV."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "songs.csv")
    
    songs = load_songs(data_path)
    assert len(songs) == 20
    assert all("title" in song for song in songs)
    assert all("genre" in song for song in songs)
    print(f"✓ Loaded {len(songs)} songs successfully")


def test_baseline_recommendations():
    """Test that baseline recommendations work."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "songs.csv")
    
    songs = load_songs(data_path)
    user_prefs = {
        "favorite_genre": "jazz",
        "favorite_mood": "relaxed",
        "target_energy": 0.4,
        "likes_acoustic": True
    }
    
    recommendations = recommend_songs(user_prefs, songs, k=5)
    
    assert len(recommendations) == 5
    assert all(len(rec) == 3 for rec in recommendations)  # (song, score, explanation)
    assert recommendations[0][1] >= recommendations[1][1]  # Sorted by score
    print(f"✓ Baseline recommendations generated (top score: {recommendations[0][1]:.2f})")


def test_rag_context_building():
    """Test that RAG context is built correctly."""
    song = {
        "title": "Test Song",
        "artist": "Test Artist",
        "genre": "jazz",
        "mood": "relaxed",
        "energy": 0.4,
        "tempo_bpm": 90,
        "valence": 0.7,
        "danceability": 0.5,
        "acousticness": 0.8
    }
    
    user_prefs = {
        "favorite_genre": "jazz",
        "favorite_mood": "relaxed",
        "target_energy": 0.4,
        "likes_acoustic": True
    }
    
    context = build_rag_context(song, user_prefs, 5.0, ["genre match", "mood match"])
    
    assert "Test Song" in context
    assert "jazz" in context
    assert "relaxed" in context
    assert "genre match" in context
    print(f"✓ RAG context built successfully (length: {len(context)} chars)")


def test_rag_context_builder_methods():
    """Test individual RAG context builder methods."""
    song = {
        "title": "Coffee Shop Stories",
        "artist": "Slow Stereo",
        "genre": "jazz",
        "mood": "relaxed",
        "energy": 0.37,
        "tempo_bpm": 90,
        "valence": 0.71,
        "danceability": 0.54,
        "acousticness": 0.89
    }
    
    user_prefs = {
        "favorite_genre": "jazz",
        "favorite_mood": "relaxed",
        "target_energy": 0.4,
        "target_tempo": 90,
        "likes_acoustic": True
    }
    
    # Test song context
    song_context = RAGContextBuilder.build_song_context(song)
    assert "Coffee Shop Stories" in song_context
    assert "Slow Stereo" in song_context
    print("✓ Song context builder works")
    
    # Test user prefs context
    prefs_context = RAGContextBuilder.build_user_prefs_context(user_prefs)
    assert "jazz" in prefs_context
    assert "relaxed" in prefs_context
    print("✓ User preferences context builder works")
    
    # Test match context
    match_context = RAGContextBuilder.build_match_context(
        song, user_prefs, 5.0, ["genre match", "mood match", "tempo close"]
    )
    assert "Match Score" in match_context
    assert "Reasons for Match" in match_context
    print("✓ Match context builder works")


def test_llm_fallback_with_rag():
    """Test that LLM fallback works when API key is missing."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "songs.csv")
    
    songs = load_songs(data_path)
    user_prefs = {
        "favorite_genre": "jazz",
        "favorite_mood": "relaxed",
        "target_energy": 0.4,
        "likes_acoustic": True
    }
    
    # Call with LLM enabled (should gracefully fallback)
    recommendations = recommend_songs_with_rag(user_prefs, songs, k=3, use_llm=True)
    
    assert len(recommendations) == 3
    assert all(len(rec) == 3 for rec in recommendations)
    print(f"✓ RAG-enhanced recommendations work with fallback (top score: {recommendations[0][1]:.2f})")


def test_llm_engine_initialization():
    """Test that LLM engine can be initialized with dummy key."""
    engine = LLMEngine(api_key="sk-test-dummy-key")
    assert engine.model == "gpt-3.5-turbo"
    assert engine.max_tokens == 200
    print("✓ LLM engine initialization successful")


def test_llm_fallback_explanation():
    """Test LLM fallback explanation generation."""
    engine = LLMEngine(api_key="sk-test-dummy-key")
    
    song = {
        "title": "Test Song",
        "artist": "Test Artist",
        "genre": "jazz",
        "mood": "relaxed"
    }
    
    explanation, success = engine.generate_explanation(
        song=song,
        user_prefs={"favorite_genre": "jazz"},
        score=5.0,
        scoring_reasons=["genre match"]
    )
    
    # Should return fallback explanation
    assert "Test Song" in explanation
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    print(f"✓ LLM fallback explanation: {explanation[:80]}...")


def test_recommendation_scores_unchanged():
    """Verify that scores don't change with RAG enhancement."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "songs.csv")
    
    songs = load_songs(data_path)
    user_prefs = {
        "favorite_genre": "jazz",
        "favorite_mood": "relaxed",
        "target_energy": 0.4,
        "likes_acoustic": True
    }
    
    # Get baseline recommendations
    baseline_recs = recommend_songs(user_prefs, songs, k=5)
    baseline_scores = [rec[1] for rec in baseline_recs]
    
    # Get RAG recommendations (will use fallback)
    rag_recs = recommend_songs_with_rag(user_prefs, songs, k=5, use_llm=True)
    rag_scores = [rec[1] for rec in rag_recs]
    
    # Scores should be identical
    for i, (baseline_score, rag_score) in enumerate(zip(baseline_scores, rag_scores)):
        assert abs(baseline_score - rag_score) < 0.001
    
    print(f"✓ Scores unchanged after RAG enhancement: {baseline_scores[:3]}")


if __name__ == "__main__":
    print("\n=== E2E RAG Pipeline Tests ===\n")
    
    test_load_songs()
    test_baseline_recommendations()
    test_rag_context_building()
    test_rag_context_builder_methods()
    test_llm_engine_initialization()
    test_llm_fallback_explanation()
    test_llm_fallback_with_rag()
    test_recommendation_scores_unchanged()
    
    print("\n=== All E2E tests passed ===\n")
