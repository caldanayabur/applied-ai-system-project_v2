"""
LLM Engine for generating personalized music recommendation explanations.

This module handles all interactions with the LLM (via OpenAI API or Copilot's
managed LLM access) to generate dynamic, contextual explanations for recommendations.
"""

import os
from typing import Optional, Dict, Tuple, List, Any
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential
from .logger import recommender_logger


class LLMEngine:
    """
    Handles LLM interactions for generating personalized recommendation explanations.
    
    Supports both OpenAI API and Copilot's managed LLM access (via environment config).
    """
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = 200
    ):
        """
        Initialize the LLM engine.
        
        Args:
            model: LLM model to use (default: gpt-3.5-turbo)
            api_key: API key (uses OPENAI_API_KEY env var if not provided)
            base_url: Custom API endpoint (for Copilot or Azure integrations)
            max_tokens: Maximum tokens for each LLM response
        """
        self.model = model
        self.max_tokens = max_tokens
        
        # Determine API configuration
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        # Initialize OpenAI client
        kwargs = {"api_key": api_key} if api_key else {}
        if base_url:
            kwargs["base_url"] = base_url
        
        self.client = OpenAI(**kwargs)
        recommender_logger.info(f"LLM Engine initialized with model={model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _call_llm(self, prompt: str) -> Tuple[str, Dict[str, int]]:
        """
        Call the LLM with retry logic.
        
        Returns:
            Tuple of (response_text, token_usage_dict)
        
        Raises:
            APIError: If the API call fails after retries
        """
        try:
            recommender_logger.log_llm_call_start(
                prompt_tokens=len(prompt.split()),  # Rough estimate
                model=self.model
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful music recommendation assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            text = response.choices[0].message.content.strip()
            tokens = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            recommender_logger.log_llm_call_end(
                prompt_tokens=tokens["prompt_tokens"],
                completion_tokens=tokens["completion_tokens"],
                total_tokens=tokens["total_tokens"],
                success=True
            )
            
            return text, tokens
        
        except (RateLimitError, APIConnectionError) as e:
            recommender_logger.log_error(
                "llm_api_error",
                str(e),
                {"model": self.model}
            )
            raise
        except APIError as e:
            recommender_logger.log_error(
                "llm_api_error",
                str(e),
                {"model": self.model, "error_type": type(e).__name__}
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


def get_llm_engine(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> LLMEngine:
    """
    Factory function to get an LLM engine instance.
    
    Uses environment variables if not explicitly provided:
    - LLM_MODEL: Model name (default: gpt-3.5-turbo)
    - OPENAI_API_KEY: OpenAI API key
    - OPENAI_BASE_URL: Custom API endpoint (e.g., for Copilot or Azure)
    """
    model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    return LLMEngine(model=model, api_key=api_key, base_url=base_url)
