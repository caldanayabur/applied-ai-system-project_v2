"""
RAG Context Builder for Music Recommender.

This module builds retrieval contexts from user preferences and song metadata
to provide rich context for the LLM explanation generation.
"""

from typing import Dict, List, Any, Optional


class RAGContextBuilder:
    """
    Builds retrieval-augmented generation (RAG) contexts from songs and user preferences.
    
    The context is formatted as a structured document that helps the LLM understand
    why a particular song was recommended to a user.
    """
    
    @staticmethod
    def build_song_context(song: Dict[str, Any]) -> str:
        """
        Build a formatted context string for a single song.
        
        Args:
            song: Song dictionary with metadata
        
        Returns:
            Formatted context string with song details
        """
        parts = [
            f"Title: {song.get('title', 'Unknown')}",
            f"Artist: {song.get('artist', 'Unknown')}",
            f"Genre: {song.get('genre', 'Unknown')}",
            f"Mood: {song.get('mood', 'Unknown')}",
            "",
            "Audio Features:",
            f"  - Energy: {song.get('energy', 'N/A')} (0-1 scale)",
            f"  - Tempo: {song.get('tempo_bpm', 'N/A')} BPM",
            f"  - Valence: {song.get('valence', 'N/A')} (musicality, 0-1)",
            f"  - Danceability: {song.get('danceability', 'N/A')} (0-1)",
            f"  - Acousticness: {song.get('acousticness', 'N/A')} (0-1)"
        ]
        return "\n".join(parts)
    
    @staticmethod
    def build_user_prefs_context(user_prefs: Dict[str, Any]) -> str:
        """
        Build a formatted context string for user preferences.
        
        Args:
            user_prefs: User preference dictionary
        
        Returns:
            Formatted context string with user preferences
        """
        parts = ["User Preferences:"]
        
        if "favorite_genre" in user_prefs:
            parts.append(f"  - Favorite Genre: {user_prefs['favorite_genre']}")
        
        if "favorite_mood" in user_prefs:
            parts.append(f"  - Favorite Mood: {user_prefs['favorite_mood']}")
        
        if "favorite_artist" in user_prefs and user_prefs.get("favorite_artist"):
            parts.append(f"  - Favorite Artist: {user_prefs['favorite_artist']}")
        
        if "target_energy" in user_prefs and user_prefs.get("target_energy") is not None:
            parts.append(f"  - Target Energy: {user_prefs['target_energy']}")
        
        if "target_tempo" in user_prefs and user_prefs.get("target_tempo") is not None:
            parts.append(f"  - Target Tempo: {user_prefs['target_tempo']} BPM")
        
        if "target_valence" in user_prefs and user_prefs.get("target_valence") is not None:
            parts.append(f"  - Target Valence: {user_prefs['target_valence']}")
        
        if "target_danceability" in user_prefs and user_prefs.get("target_danceability") is not None:
            parts.append(f"  - Target Danceability: {user_prefs['target_danceability']}")
        
        if "target_acousticness" in user_prefs and user_prefs.get("target_acousticness") is not None:
            parts.append(f"  - Target Acousticness: {user_prefs['target_acousticness']}")
        
        if "likes_acoustic" in user_prefs:
            acoustic_text = "Yes" if user_prefs["likes_acoustic"] else "No"
            parts.append(f"  - Likes Acoustic Music: {acoustic_text}")
        
        return "\n".join(parts)
    
    @staticmethod
    def build_match_context(
        song: Dict[str, Any],
        user_prefs: Dict[str, Any],
        score: float,
        scoring_reasons: List[str]
    ) -> str:
        """
        Build a formatted context string for why a song matched.
        
        Args:
            song: Song dictionary
            user_prefs: User preference dictionary
            score: Recommendation score
            scoring_reasons: List of reasons why the song matched
        
        Returns:
            Formatted context string explaining the match
        """
        parts = [
            f"Match Score: {score:.2f}/10",
            "",
            "Reasons for Match:",
        ]
        
        if scoring_reasons:
            for i, reason in enumerate(scoring_reasons, 1):
                parts.append(f"  {i}. {reason}")
        else:
            parts.append("  (No specific matching reasons)")
        
        # Add feature similarity explanations
        parts.extend(RAGContextBuilder._get_feature_explanations(song, user_prefs))
        
        return "\n".join(parts)
    
    @staticmethod
    def _get_feature_explanations(
        song: Dict[str, Any],
        user_prefs: Dict[str, Any]
    ) -> List[str]:
        """
        Generate explanations for how song features match user preferences.
        
        Args:
            song: Song dictionary
            user_prefs: User preference dictionary
        
        Returns:
            List of feature explanation strings
        """
        explanations = ["", "Feature Alignment:"]
        
        # Energy comparison
        if "target_energy" in user_prefs and user_prefs.get("target_energy") is not None:
            song_energy = float(song.get("energy", 0.5))
            target_energy = float(user_prefs["target_energy"])
            diff = abs(song_energy - target_energy)
            alignment = "High" if diff < 0.2 else "Moderate" if diff < 0.4 else "Low"
            explanations.append(f"  - Energy: {alignment} ({song_energy:.2f} vs target {target_energy:.2f})")
        
        # Tempo comparison
        if "target_tempo" in user_prefs and user_prefs.get("target_tempo") is not None:
            song_tempo = float(song.get("tempo_bpm", 100))
            target_tempo = float(user_prefs["target_tempo"])
            diff = abs(song_tempo - target_tempo)
            alignment = "High" if diff < 10 else "Moderate" if diff < 25 else "Low"
            explanations.append(f"  - Tempo: {alignment} ({song_tempo:.0f} vs target {target_tempo:.0f} BPM)")
        
        # Acousticness check
        if user_prefs.get("likes_acoustic") and user_prefs.get("target_acousticness"):
            acousticness = float(song.get("acousticness", 0))
            if acousticness > 0.7:
                explanations.append(f"  - Acousticness: High (matches preference)")
            elif acousticness > 0.4:
                explanations.append(f"  - Acousticness: Moderate (somewhat matches)")
            else:
                explanations.append(f"  - Acousticness: Low (may not match preference)")
        
        return explanations
    
    @staticmethod
    def build_full_rag_context(
        song: Dict[str, Any],
        user_prefs: Dict[str, Any],
        score: float,
        scoring_reasons: List[str]
    ) -> str:
        """
        Build a complete RAG context combining all information.
        
        Args:
            song: Song dictionary
            user_prefs: User preference dictionary
            score: Recommendation score
            scoring_reasons: List of scoring reasons
        
        Returns:
            Complete formatted context
        """
        sections = [
            "=== SONG INFORMATION ===",
            RAGContextBuilder.build_song_context(song),
            "",
            "=== USER PREFERENCES ===",
            RAGContextBuilder.build_user_prefs_context(user_prefs),
            "",
            "=== MATCH ANALYSIS ===",
            RAGContextBuilder.build_match_context(song, user_prefs, score, scoring_reasons)
        ]
        
        return "\n".join(sections)


def build_rag_context(
    song: Dict[str, Any],
    user_prefs: Dict[str, Any],
    score: float,
    scoring_reasons: List[str]
) -> str:
    """
    Convenience function to build RAG context.
    
    Args:
        song: Song dictionary
        user_prefs: User preference dictionary
        score: Recommendation score
        scoring_reasons: List of scoring reasons
    
    Returns:
        Complete formatted context
    """
    return RAGContextBuilder.build_full_rag_context(song, user_prefs, score, scoring_reasons)
