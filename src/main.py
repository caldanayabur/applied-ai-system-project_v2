"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import os
from .recommender import load_songs, recommend_songs_with_descriptions


def main() -> None:
    # Get the data path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "songs.csv")
    
    songs = load_songs(data_path)

    # Diverse user taste profiles for adversarial/edge-case testing
    user_prefs = [
        # 1. Impossible match: genre and mood not in dataset, extreme energy
        {
            "favorite_genre": "k-pop",
            "favorite_mood": "melancholy",
            "target_energy": 1.5,  # Out of normal range
            "likes_acoustic": True
        },
        # 2. Contradictory: likes acoustic but wants high energy and danceability
        {
            "favorite_genre": "jazz",
            "favorite_mood": "relaxed",
            "target_energy": 0.95,
            "target_danceability": 0.95,
            "target_acousticness": 0.95,
            "likes_acoustic": True
        },
        # 3. Diverse: prefers high valence, moderate tempo, and relaxed mood
        {
            "favorite_genre": "jazz",
            "favorite_mood": "relaxed",
            "target_valence": 0.7,
            "target_tempo": 90,
            "likes_acoustic": True
        }
    ]

    for i, profile in enumerate(user_prefs, 1):
        print(f"\n{'#' * 12} User Profile {i} {'#' * 12}")
        print("Profile:")
        for k, v in profile.items():
            print(f"  {k}: {v}")
        
        # Try to use LLM-enhanced recommendations, fall back to regular if LLM unavailable
        try:
            recommendations = recommend_songs_with_descriptions(profile, songs, k=5, use_llm=True)
            llm_status = "[LLM Enhanced]"
        except Exception as e:
            # Fallback without LLM
            from .recommender import recommend_songs
            recommendations = recommend_songs(profile, songs, k=5)
            llm_status = "[Fallback: No LLM]"
        
        print(f"\nTop recommendations ({llm_status}):\n")
        for idx, rec in enumerate(recommendations, 1):
            song, score, description = rec
            print("=" * 40)
            print(f"{idx}. Title      : {song['title']}")
            print(f"   Artist     : {song['artist']}")
            print(f"   Score      : {score:.2f}")
            print(f"   Description: {description}")
        print("=" * 40)


if __name__ == "__main__":
    main()
