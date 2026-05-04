from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement description logic
        return "Description placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file."""
    import csv
    songs = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert numeric fields
            row['id'] = int(row['id'])
            row['energy'] = float(row['energy'])
            row['tempo_bpm'] = float(row['tempo_bpm'])
            row['valence'] = float(row['valence'])
            row['danceability'] = float(row['danceability'])
            row['acousticness'] = float(row['acousticness'])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a song against user preferences."""
    score = 0.0
    reasons = []

    # Genre match
    if song.get('genre', '').lower() == user_prefs.get('favorite_genre', '').lower():
        score += 2.0
        reasons.append("genre match (+2.0)")

    # Mood match
    if song.get('mood', '').lower() == user_prefs.get('favorite_mood', '').lower():
        score += 1.0
        reasons.append("mood match (+1.0)")

    # Artist match (optional, only if user_prefs has favorite_artist)
    if 'favorite_artist' in user_prefs and user_prefs['favorite_artist']:
        if song.get('artist', '').lower() == user_prefs['favorite_artist'].lower():
            score += 1.0
            reasons.append("artist match (+1.0)")

    # Helper for closeness
    def close(val, target, threshold):
        return abs(val - target) <= threshold

    # Tempo close (within 10 bpm)
    if 'target_tempo' in user_prefs and user_prefs['target_tempo'] is not None:
        if close(float(song['tempo_bpm']), float(user_prefs['target_tempo']), 10):
            score += 1.0
            reasons.append("tempo close (+1.0)")

    # Danceability close (within 0.15)
    if 'target_danceability' in user_prefs and user_prefs['target_danceability'] is not None:
        if close(float(song['danceability']), float(user_prefs['target_danceability']), 0.15):
            score += 1.0
            reasons.append("danceability close (+1.0)")

    # Acousticness close (within 0.15)
    if 'target_acousticness' in user_prefs and user_prefs['target_acousticness'] is not None:
        if close(float(song['acousticness']), float(user_prefs['target_acousticness']), 0.15):
            score += 1.0
            reasons.append("acousticness close (+1.0)")

    # Valence close (within 0.15)
    if 'target_valence' in user_prefs and user_prefs['target_valence'] is not None:
        if close(float(song['valence']), float(user_prefs['target_valence']), 0.15):
            score += 1.0
            reasons.append("valence close (+1.0)")

    # Energy similarity (1 - abs diff)
    if 'target_energy' in user_prefs and user_prefs['target_energy'] is not None:
        similarity = 1.0 - abs(float(song['energy']) - float(user_prefs['target_energy']))
        score += similarity
        reasons.append(f"energy similarity (+{similarity:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Recommend top k songs for a user."""
    # Score each song and collect (song, score, description)
    scored = [
        (song, score, "; ".join(reasons))
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]
    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    # Return top k
    return scored[:k]


def recommend_songs_with_descriptions(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    use_llm: bool = True
) -> List[Tuple[Dict, float, str]]:
    """
    Recommend top k songs for a user with LLM-generated song descriptions.
    
    This function:
    1. Uses the same scoring logic as recommend_songs() (rule-based, unchanged)
    2. Finalizes top-N recommendations
    3. Invokes LLM ONLY to generate lyrical and artist descriptions for each recommendation
    
    The LLM descriptions focus on:
    - What the song's lyrics are generally about (themes, narrative, emotional message)
    - The artist or band's musical style and artistic identity
    
    Args:
        user_prefs: User preference dictionary (used ONLY for scoring, NOT for LLM)
        songs: List of song dictionaries
        k: Number of recommendations to return
        use_llm: Whether to use LLM for descriptions (True) or fallback (False)
    
    Returns:
        List of (song, score, description) tuples
    """
    from .llm_engine import get_llm_engine
    from .logger import recommender_logger
    
    # Step 1: Get base recommendations using rule-based scoring (unchanged)
    recommendations = recommend_songs(user_prefs, songs, k)
    
    # Step 2: Enhance descriptions with LLM if enabled
    if not use_llm:
        return recommendations
    
    try:
        llm_engine = get_llm_engine()
        enhanced_recommendations = []
        
        for song, score, base_description in recommendations:
            # Generate LLM description based ONLY on song metadata, not user preferences or scores
            description, success = llm_engine.generate_song_description(
                song_title=song.get('title', 'Unknown'),
                artist=song.get('artist', 'Unknown'),
                metadata={
                    'genre': song.get('genre', 'Unknown'),
                    'mood': song.get('mood', 'Unknown'),
                    'energy': song.get('energy', 'N/A'),
                    'tempo_bpm': song.get('tempo_bpm', 'N/A'),
                    'valence': song.get('valence', 'N/A'),
                    'danceability': song.get('danceability', 'N/A'),
                    'acousticness': song.get('acousticness', 'N/A')
                }
            )
            
            enhanced_recommendations.append((song, score, description))
        
        return enhanced_recommendations
    
    except Exception as e:
        recommender_logger.log_error(
            "description_generation_failed",
            str(e),
            {"num_songs": len(recommendations), "use_llm": use_llm}
        )
        # Fallback to base recommendations
        return recommendations

