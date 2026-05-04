"""
LLM Engine for generating song descriptions focused on lyrics and artist identity.

This module handles all interactions with the LLM via GitHub Copilot Python SDK
to generate high-level lyrical themes and artist musical style descriptions
for real songs only. Prevents hallucination by constraining output to widely-known
information and avoiding fabricated facts.
"""

import asyncio
import os
import re
from typing import Optional, Dict, Tuple, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from .logger import recommender_logger

try:
    from copilot import CopilotClient
    from copilot.session import PermissionRequestResult
    COPILOT_AVAILABLE = True
except ImportError:
    COPILOT_AVAILABLE = False
    recommender_logger.warning("Copilot SDK not available, will use fallback mode only")


def _approve_all_permissions(request: Any, invocation: Dict[str, str]) -> Any:
    """Approve Copilot permission requests without user interaction."""
    return PermissionRequestResult(kind="approve-once")


class LLMEngine:
    """
    Handles LLM interactions for generating song descriptions.
    
    Focuses on lyrical themes and artist musical identity for REAL songs only.
    Uses GitHub Copilot Python SDK for managed LLM access.
    If SDK is not available, gracefully falls back to rule-based descriptions.
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
        self.force_fallback = os.getenv("LLM_FORCE_FALLBACK", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self._resolved_model: Optional[str] = None
        
        if COPILOT_AVAILABLE:
            recommender_logger.info(f"LLM Engine initialized with Copilot SDK, model={model}")
        else:
            recommender_logger.info("LLM Engine initialized in fallback mode (Copilot SDK unavailable)")
    
    def generate_song_description(
        self,
        song_title: str,
        artist: str,
        metadata: Dict[str, Any]
    ) -> Tuple[str, bool]:
        """
        Generate a description of a song's lyrical themes and artist style.
        
        CONSTRAINTS (strictly enforced):
        - Descriptions are for REAL songs and artists only
        - Do NOT claim exact lyrics or quote specific verses
        - Do NOT invent release dates, awards, chart rankings, or career history
        - Keep to high-level, widely-known thematic interpretations
        - Do NOT mention recommendation logic, scores, similarity metrics, or user preferences
        
        Args:
            song_title: Title of the song (e.g., "Shut Up and Dance")
            artist: Artist or band name (e.g., "Walk The Moon")
            metadata: Dictionary with dataset fields (genre, mood, energy, tempo_bpm, etc.)
        
        Returns:
            Tuple of (description_text, success_flag)
            Format: "<Song Title> – <Artist> Description: <2–3 sentence description>"
            If LLM fails or unavailable, returns rule-based description with success=False
        """
        if not self.copilot_available or self.force_fallback:
            fallback_description = self._fallback_description(song_title, artist, metadata)
            recommender_logger.log_song_description_generated(
                song_title=song_title,
                artist=artist,
                source="fallback",
                description_length=len(fallback_description)
            )
            return fallback_description, False

        try:
            description = asyncio.run(
                self._generate_song_description_async(song_title, artist, metadata)
            )
            recommender_logger.log_song_description_generated(
                song_title=song_title,
                artist=artist,
                source="llm",
                description_length=len(description)
            )
            return description, True
        except Exception as exc:
            recommender_logger.log_error(
                "llm_description_generation_failed",
                str(exc),
                {"song_title": song_title, "artist": artist, "model": self.model}
            )
            fallback_description = self._fallback_description(song_title, artist, metadata)
            recommender_logger.log_song_description_generated(
                song_title=song_title,
                artist=artist,
                source="fallback",
                description_length=len(fallback_description)
            )
            return fallback_description, False

    async def _generate_song_description_async(
        self,
        song_title: str,
        artist: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate a description via the Copilot SDK."""
        if self.force_fallback:
            return self._fallback_description(song_title, artist, metadata)

        prompt = self._build_prompt(song_title, artist, metadata)
        prompt_tokens = len(prompt.split())
        recommender_logger.log_llm_call_start(prompt_tokens=prompt_tokens, model=self.model)

        description, completion_tokens = await self._request_copilot_description(prompt, song_title, artist)
        recommender_logger.log_llm_call_end(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            success=True,
            error=None,
        )
        return description

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4), reraise=True)
    async def _request_copilot_description(
        self,
        prompt: str,
        song_title: str,
        artist: str,
    ) -> Tuple[str, int]:
        """Send the prompt to Copilot and normalize the response text."""
        client = CopilotClient()
        await client.start()
        try:
            model = await self._resolve_model(client)
            session = await client.create_session(
                on_permission_request=_approve_all_permissions,
                model=model,
                client_name="beatbuddy-music-recommender",
                streaming=False,
            )
            event = await session.send_and_wait(prompt, timeout=60.0)
        finally:
            await client.stop()

        response_text = self._extract_response_text(event)
        if not response_text:
            raise ValueError("Copilot returned an empty response")

        normalized = self._normalize_response_text(response_text, song_title, artist)
        completion_tokens = int(getattr(getattr(event, "data", None), "output_tokens", 0) or 0)
        return normalized, completion_tokens

    async def _resolve_model(self, client: Any) -> str:
        """Choose a Copilot model that is actually available in this environment."""
        if self._resolved_model:
            return self._resolved_model

        requested_model = (self.model or "").strip()
        available_models = await client.list_models()

        by_id = {getattr(model, "id", "").lower(): getattr(model, "id", "") for model in available_models}
        by_name = {getattr(model, "name", "").lower(): getattr(model, "id", "") for model in available_models}

        def resolve(candidate: str) -> str:
            lowered = candidate.lower()
            return by_id.get(lowered) or by_name.get(lowered) or ""

        preference_order = [
            requested_model,
            os.getenv("LLM_MODEL", "").strip(),
            "gpt-5.4-mini",
            "gpt-5-mini",
            "gpt-4.1",
            "auto",
        ]

        for candidate in preference_order:
            if not candidate:
                continue
            selected = resolve(candidate)
            if selected:
                self._resolved_model = selected
                if requested_model and selected.lower() != requested_model.lower():
                    recommender_logger.warning(
                        f'Copilot model "{requested_model}" is unavailable; using "{selected}" instead.'
                    )
                return selected

        if available_models:
            fallback_model = getattr(available_models[0], "id", requested_model or "auto")
            self._resolved_model = fallback_model
            recommender_logger.warning(
                f'Copilot model "{requested_model or self.model}" is unavailable; using "{fallback_model}" instead.'
            )
            return fallback_model

        self._resolved_model = requested_model or "auto"
        return self._resolved_model

    @staticmethod
    def _extract_response_text(event: Any) -> str:
        """Extract plain assistant text from a Copilot session event."""
        data = getattr(event, "data", None)
        content = getattr(data, "content", None)
        if isinstance(content, str):
            return content.strip()
        if isinstance(event, str):
            return event.strip()
        return ""

    @staticmethod
    def _normalize_response_text(response_text: str, song_title: str, artist: str) -> str:
        """Ensure the response matches the expected description format."""
        cleaned = re.sub(r"\s+", " ", response_text).strip()
        expected_prefix = f"{song_title} – {artist} Description:"
        lower_cleaned = cleaned.lower()
        if lower_cleaned.startswith(song_title.lower()) and "description:" in lower_cleaned:
            return cleaned
        return f"{expected_prefix} {cleaned}"
    
    def _build_prompt(
        self,
        song_title: str,
        artist: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Build a constrained prompt for the LLM to generate song descriptions.
        
        The prompt explicitly prohibits hallucination and focuses on:
        1. What the song's lyrics are generally about (themes, narrative, emotional message)
        2. The artist or band's musical style and artistic identity
        """
        metadata_str = "\n".join([
            f"  - Genre: {metadata.get('genre', 'Unknown')}",
            f"  - Mood: {metadata.get('mood', 'Unknown')}",
            f"  - Energy: {metadata.get('energy', 'N/A')}",
            f"  - Tempo: {metadata.get('tempo_bpm', 'N/A')} BPM",
            f"  - Valence: {metadata.get('valence', 'N/A')}",
            f"  - Danceability: {metadata.get('danceability', 'N/A')}",
            f"  - Acousticness: {metadata.get('acousticness', 'N/A')}"
        ])
        
        prompt = f"""Generate a brief description of "{song_title}" by {artist} based ONLY on widely-known information about this real song and artist.

STRICT CONSTRAINTS:
- Do NOT claim exact lyrics or quote specific verses
- Do NOT invent release dates, awards, or chart rankings
- Do NOT fabricate career history or personal details
- Do NOT mention recommendation scores or user preferences
- Focus on: (1) What the lyrics are generally about (themes, narrative, mood), and (2) The artist's musical style and identity
- Output exactly 2-3 sentences in a neutral, informative tone
- NO bullet points, NO emojis

Song Metadata:
{metadata_str}

Output format (must match exactly):
{song_title} – {artist} Description: [Your 2-3 sentence description here]"""
        
        return prompt
    
    def _fallback_description(
        self,
        song_title: str,
        artist: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate a rule-based description when LLM fails or is unavailable.
        
        Uses only dataset metadata (genre, mood) to infer a generic description.
        Ensures the system degrades gracefully.
        """
        genre = metadata.get('genre', 'Unknown').lower()
        mood = metadata.get('mood', 'Unknown').lower()
        
        # Genre-based musical style hint
        genre_styles = {
            'pop': 'contemporary pop with catchy melodies',
            'rock': 'rock music with energetic instrumentation',
            'jazz': 'jazz with complex harmonies and improvisation',
            'lofi': 'lo-fi beats with a relaxing, chill atmosphere',
            'ambient': 'ambient soundscapes with minimal instrumentation',
            'indie pop': 'indie pop with alternative sensibilities',
            'blues': 'blues with soulful vocals and emotional depth',
            'country': 'country music with storytelling elements',
            'synthwave': 'synthwave with electronic and retro influences',
            'chip tune': 'chip tune music with playful, video game-style sounds',
        }
        
        # Mood-based thematic hint
        mood_themes = {
            'happy': 'uplifting and positive themes',
            'chill': 'relaxed and peaceful atmosphere',
            'melancholic': 'introspective and emotional themes',
            'intense': 'high-energy and powerful emotions',
            'exotic': 'world music influences and cultural themes',
            'focused': 'concentration and productivity themes',
            'moody': 'atmospheric and contemplative tones',
            'relaxed': 'laid-back and soothing qualities',
            'nostalgic': 'themes of longing and memory',
            'playful': 'fun and lighthearted character',
        }
        
        artist_style = genre_styles.get(genre, f'{genre} music')
        thematic_focus = mood_themes.get(mood, f'{mood} mood')
        
        return (f"{song_title} – {artist} Description: "
                f"This song showcases {artist_style} with a {thematic_focus}. "
                f"The track combines elements of {genre} with a {mood} sensibility, "
                f"creating an engaging listening experience.")


def get_llm_engine(model: Optional[str] = None) -> LLMEngine:
    """
    Factory function to get an LLM engine instance.
    
    Uses environment variables if not explicitly provided:
    - LLM_MODEL: Model name (default: gpt-4)
    
    Note: Requires GitHub Copilot Python SDK to be installed and configured.
    If SDK is not available, falls back to rule-based descriptions.
    """
    model = model or os.getenv("LLM_MODEL", "gpt-4")
    return LLMEngine(model=model)
