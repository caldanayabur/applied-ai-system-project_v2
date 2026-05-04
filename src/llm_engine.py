"""
LLM Engine for generating song descriptions focused on lyrics and artist identity.

This module handles all interactions with the LLM via GitHub Copilot Python SDK
to generate high-level lyrical themes and artist musical style descriptions
for real songs only. Prevents hallucination by constraining output to widely-known
information and avoiding fabricated facts.
"""

import os
from typing import Optional, Dict, Tuple, Any
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
        # For now, always use fallback since SDK is not properly available
        # This ensures the system works reliably while we resolve SDK setup
        fallback_description = self._fallback_description(song_title, artist, metadata)
        
        recommender_logger.log_song_description_generated(
            song_title=song_title,
            artist=artist,
            source="fallback",
            description_length=len(fallback_description)
        )
        
        return fallback_description, False
    
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
