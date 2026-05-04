"""
LLM Engine for generating personalized music recommendation explanations.

This module handles all interactions with the LLM via GitHub Copilot CLI
to generate dynamic, contextual explanations for recommendations.
"""

import os
import subprocess
import json
import sys
from typing import Optional, Dict, Tuple, List, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from .logger import recommender_logger


class LLMEngine:
    """
    Handles LLM interactions for generating personalized recommendation explanations.
    
    Uses GitHub Copilot CLI for managed LLM access.
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
        
        # Verify Copilot CLI is available
        try:
            result = subprocess.run(
                ["gh", "copilot", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                recommender_logger.info(f"GitHub Copilot CLI detected: {result.stdout.strip()}")
            else:
                recommender_logger.info("GitHub Copilot CLI not available, will use fallback mode")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            recommender_logger.info("GitHub Copilot CLI not found, will use fallback mode")
        
        recommender_logger.info(f"LLM Engine initialized with GitHub Copilot CLI integration, model={model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _call_llm(self, prompt: str) -> Tuple[str, Dict[str, int]]:
        """
        Call the LLM via GitHub Copilot CLI with retry logic.
        
        Returns:
            Tuple of (response_text, token_usage_dict)
        
        Raises:
            Exception: If the CLI call fails after retries
        """
        try:
            recommender_logger.log_llm_call_start(
                prompt_tokens=len(prompt.split()),
                model=self.model
            )
            
            # Call GitHub Copilot CLI
            result = subprocess.run(
                ["gh", "copilot", "suggest", "-t", "shell"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Copilot CLI error: {result.stderr}")
            
            text = result.stdout.strip()
            
            # Estimate tokens (rough approximation)
            tokens = {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(text.split()),
                "total_tokens": len(prompt.split()) + len(text.split())
            }
            
            recommender_logger.log_llm_call_end(
                prompt_tokens=tokens["prompt_tokens"],
                completion_tokens=tokens["completion_tokens"],
                total_tokens=tokens["total_tokens"],
                success=True
            )
            
            return text, tokens
        
        except Exception as e:
            recommender_logger.log_error(
                "llm_cli_error",
                str(e),
                {"model": self.model}
            )
            raise
    
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
            If LLM fails, returns rule-based explanation with success=False
        """
        # Build context for the LLM
        context = self._build_context(song, user_prefs, score, scoring_reasons)
        prompt = self._build_prompt(context, song, user_prefs, scoring_reasons)
        
        try:
            explanation, tokens = self._call_llm(prompt)
            recommender_logger.log_explanation_generated(
                song_title=song.get("title", "Unknown"),
                source="llm",
                explanation_length=len(explanation)
            )
            return explanation, True
        
        except Exception as e:
            recommender_logger.log_error(
                "llm_explanation_failed",
                str(e),
                {"song_title": song.get("title", "Unknown")}
            )
            # Fall back to rule-based explanation
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
        Generate a rule-based explanation when LLM fails.
        
        This ensures the system degrades gracefully.
        """
        reasons_text = "; ".join(scoring_reasons) if scoring_reasons else "matches your preferences"
        return f"We picked '{song.get('title', 'Unknown')}' because it {reasons_text}."


def get_llm_engine(model: Optional[str] = None) -> LLMEngine:
    """
    Factory function to get an LLM engine instance.
    
    Uses environment variables if not explicitly provided:
    - LLM_MODEL: Model name (default: gpt-4)
    
    Requires GitHub CLI and Copilot CLI to be installed and authenticated.
    """
    model = model or os.getenv("LLM_MODEL", "gpt-4")
    return LLMEngine(model=model)
