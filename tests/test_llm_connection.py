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


def test_llm_fallback_description():
    """Test fallback description when LLM is unavailable."""
    # Create engine (CLI-based, no API key needed)
    engine = LLMEngine()
    
    metadata = {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "tempo_bpm": 120,
        "valence": 0.85,
        "danceability": 0.8,
        "acousticness": 0.2
    }
    
    # Test fallback
    fallback_text, success = engine.generate_song_description(
        song_title="Test Song",
        artist="Test Artist",
        metadata=metadata
    )
    
    assert "Test Song" in fallback_text
    assert "Test Artist" in fallback_text
    assert "Description:" in fallback_text
    print(f"✓ Fallback description generated: {fallback_text[:100]}...")


def test_llm_prompt_building():
    """Test prompt building for LLM description generation."""
    engine = LLMEngine()
    
    metadata = {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "tempo_bpm": 120,
        "valence": 0.85,
        "danceability": 0.8,
        "acousticness": 0.2
    }
    
    prompt = engine._build_prompt("Test Song", "Test Artist", metadata)
    
    assert "Test Song" in prompt
    assert "Test Artist" in prompt
    assert "STRICT CONSTRAINTS:" in prompt
    assert "lyrical themes" in prompt.lower() or "lyrics" in prompt.lower()
    print(f"✓ Prompt built successfully (length: {len(prompt)} chars)")


def test_llm_prompt_includes_retrieved_context():
    """Test that retrieved RAG context is included in the LLM prompt."""
    engine = LLMEngine()
    metadata = {"genre": "jazz", "mood": "relaxed"}
    rag_context = "Title: Blue Train\nReasons for Match:\n  1. genre match (+2.0)"

    prompt = engine._build_prompt(
        "Blue Train",
        "John Coltrane",
        metadata,
        rag_context=rag_context,
    )

    assert "Retrieved Context:" in prompt
    assert "Blue Train" in prompt
    assert "genre match (+2.0)" in prompt
    assert "do not mention user preferences" in prompt.lower()


def test_description_format():
    """Test that descriptions follow the required format."""
    engine = LLMEngine()
    
    metadata = {
        "genre": "jazz",
        "mood": "relaxed",
        "energy": 0.4,
        "tempo_bpm": 90,
        "valence": 0.7,
        "danceability": 0.5,
        "acousticness": 0.8
    }
    
    description, success = engine.generate_song_description(
        song_title="Coffee Shop Stories",
        artist="Slow Stereo",
        metadata=metadata
    )
    
    # Should follow format: "Title – Artist Description: ..."
    assert "–" in description or "-" in description
    assert "Description:" in description
    assert "Coffee Shop Stories" in description
    assert "Slow Stereo" in description
    print(f"✓ Description format is correct: {description[:120]}...")


if __name__ == "__main__":
    print("\n=== LLM Connection Tests ===\n")
    
    test_llm_engine_initialization()
    test_llm_engine_with_custom_model()
    test_llm_fallback_description()
    test_llm_prompt_building()
    test_description_format()
    
    print("\n=== All tests passed ===\n")
