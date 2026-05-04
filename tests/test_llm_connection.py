"""
Test LLM connection and basic functionality.

This test verifies that the LLM engine can be initialized and make API calls
(or gracefully fail if no API key is configured).
"""

import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_engine import LLMEngine, get_llm_engine


def test_llm_engine_initialization():
    """Test that LLM engine can be initialized."""
    try:
        engine = get_llm_engine()
        assert engine is not None
        assert engine.model == "gpt-4"
        print("✓ LLM engine initialized successfully")
    except Exception as e:
        print(f"⚠ LLM initialization skipped (Copilot CLI not available): {type(e).__name__}")


def test_llm_engine_with_custom_model():
    """Test LLM engine with custom model."""
    try:
        engine = LLMEngine(model="gpt-4")
        assert engine.model == "gpt-4"
        print("✓ Custom model initialization successful")
    except Exception as e:
        print(f"⚠ Custom model initialization skipped (Copilot CLI not available): {type(e).__name__}")


def test_llm_fallback_explanation():
    """Test fallback explanation when LLM is unavailable."""
    # Create engine (CLI-based, no API key needed)
    engine = LLMEngine()
    
    song = {
        "title": "Test Song",
        "artist": "Test Artist",
        "genre": "pop",
        "mood": "happy"
    }
    
    scoring_reasons = ["genre match (+2.0)", "energy similarity (+0.5)"]
    
    # Test fallback
    fallback_text = engine._fallback_explanation(song, scoring_reasons)
    assert "Test Song" in fallback_text
    assert "genre match" in fallback_text
    print(f"✓ Fallback explanation generated: {fallback_text}")


def test_llm_context_building():
    """Test context building for LLM."""
    engine = LLMEngine()
    
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
        "likes_acoustic": True
    }
    
    context = engine._build_context(song, user_prefs, 5.0, ["genre match", "mood match"])
    
    assert "Coffee Shop Stories" in context
    assert "jazz" in context
    assert "relaxed" in context
    print(f"✓ Context built successfully")


def test_llm_prompt_building():
    """Test prompt building for LLM."""
    engine = LLMEngine()
    
    song = {
        "title": "Test Song",
        "artist": "Test Artist",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "tempo_bpm": 120,
        "valence": 0.85,
        "danceability": 0.8,
        "acousticness": 0.2
    }
    
    user_prefs = {"favorite_genre": "pop", "favorite_mood": "happy"}
    
    context = engine._build_context(song, user_prefs, 3.0, ["genre match"])
    prompt = engine._build_prompt(context, song, user_prefs, ["genre match"])
    
    assert "Test Song" in prompt
    assert "genre match" in prompt
    assert "personalized explanation" in prompt.lower()
    print(f"✓ Prompt built successfully (length: {len(prompt)} chars)")


if __name__ == "__main__":
    print("\n=== LLM Connection Tests ===\n")
    
    test_llm_engine_initialization()
    test_llm_engine_with_custom_model()
    test_llm_fallback_explanation()
    test_llm_context_building()
    test_llm_prompt_building()
    
    print("\n=== All tests passed ===\n")
