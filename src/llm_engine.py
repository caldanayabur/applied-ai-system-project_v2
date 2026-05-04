"""
LLM Engine for generating personalized music recommendation explanations.

This module handles all interactions with the LLM via GitHub Copilot Python SDK
to generate dynamic, contextual explanations for recommendations.
Falls back to rule-based explanations if the SDK is not available.
"""

import os
import json
from typing import Optional, Dict, Tuple, List, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from .logger import recommender_logger

try:
    from copilot import CopilotClient, PermissionHandler
    COPILOT_AVAILABLE = True
except ImportError:
    COPILOT_AVAILABLE = False
    recommender_logger.warning("Copilot SDK not available, will use fallback mode only")


class LLMEngine:
    """
    Handles LLM interactions for generating personalized recommendation explanations.
    
    Uses GitHub Copilot Python SDK for managed LLM access.
    If SDK is not available, gracefully falls back to rule-based explanations.
    """
    
    def __init__(
        self,
        model: str = "gpt-4",
        max_tokens: int = 200
    ):
        """
        Initialize the LLM engine.
        
        Args:
            model: LLM model to use (default: gpt-4)
            max_tokens: Maximum tokens for each LLM response
        """
        self.model = model
        self.max_tokens = max_tokens
        self.copilot_available = COPILOT_AVAILABLE
        
        if COPILOT_AVAILABLE:
            recommender_logger.info(f"LLM Engine initialized with Copilot SDK, model={model}")
        else:
            recommender_logger.info("LLM Engine initialized in fallback mode (Copilot SDK unavailable)")
    
    def generate_explanation(
        self,
        song: Dict[str, Any],
        user_prefs: Dict[str, Any],
        score: float,
        scoring_reasons: List[str]
    ) -> Tuple[str, bool]:
        """
        Generate a personalized explanation for why a song was recommended.
        
        Args:
            song: Song dictionary with metadata
            user_prefs: User preference dictionary
            score: Recommendation score
            scoring_reasons: List of scoring reasons (from score_song)
        
        Returns:
            Tuple of (explanation_text, success_flag)
            If LLM fails or unavailable, returns rule-based explanation with success=False
        """
        # For now, always use fallback since SDK is not properly available
        # This ensures the system works reliably while we resolve SDK setup
        fallback_explanation = self._fallback_explanation(song, scoring_reasons)
        
        recommender_logger.log_explanation_generated(
            song_title=song.get("title", "Unknown"),
            source="fallback",
            explanation_length=len(fallback_explanation)
        )
        
        return fallback_explanation, False
    
    def _build_context(
        self,
        song: Dict[str, Any],
        user_prefs: Dict[str, Any],
        score: float,
        scoring_reasons: List[str]
    ) -> str:
        """Build a concise context document for the LLM."""
        context_parts = [
            f"Song: '{song.get('title', 'Unknown')}' by {song.get('artist', 'Unknown Artist')}",
            f"Genre: {song.get('genre', 'Unknown')}, Mood: {song.get('mood', 'Unknown')}",
            f"Audio Features: Energy={song.get('energy', 'N/A')}, Tempo={song.get('tempo_bpm', 'N/A')} BPM, "
            f"Valence={song.get('valence', 'N/A')}, Danceability={song.get('danceability', 'N/A')}, "
            f"Acousticness={song.get('acousticness', 'N/A')}",
            "",
            f"User Preferences: {user_prefs}",
            f"Match Score: {score:.2f}",
            f"Matching Reasons: {', '.join(scoring_reasons) if scoring_reasons else 'None'}"
        ]
        return "\n".join(context_parts)
    
    def _build_prompt(
        self,
        context: str,
        song: Dict[str, Any],
        user_prefs: Dict[str, Any],
        scoring_reasons: List[str]
    ) -> str:
        """Build a prompt for the LLM."""
        prompt = f"""Based on the following information, write a brief, personalized explanation 
(1-2 sentences) for why this song is recommended to the user. 
Be conversational and reference specific audio features or user preferences.

{context}

Explanation:"""
        return prompt
    
    def _fallback_explanation(self, song: Dict[str, Any], scoring_reasons: List[str]) -> str:
        """
        Generate a rule-based explanation when LLM fails or is unavailable.
        
        This ensures the system degrades gracefully.
        """
        reasons_text = "; ".join(scoring_reasons) if scoring_reasons else "matches your preferences"
        return f"We picked '{song.get('title', 'Unknown')}' because it {reasons_text}."


def get_llm_engine(model: Optional[str] = None) -> LLMEngine:
    """
    Factory function to get an LLM engine instance.
    
    Uses environment variables if not explicitly provided:
    - LLM_MODEL: Model name (default: gpt-4)
    
    Note: Requires GitHub Copilot Python SDK to be installed and configured.
    If SDK is not available, falls back to rule-based explanations.
    """
    model = model or os.getenv("LLM_MODEL", "gpt-4")
    return LLMEngine(model=model)
