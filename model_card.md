# 🎧 Model Card: Music Recommender with RAG Enhancement

## 1. Model Name  

BeatBuddy (enhanced with Retrieval-Augmented Generation)

---

## 2. Intended Use  

This recommender is designed for classroom exploration and learning, not for real-world music streaming. It generates song recommendations from a small, fixed catalog based on a user's stated preferences for genre, mood, energy, and other features. The system assumes users know what they like and can specify their favorite genre, mood, and target values for features like tempo or valence. 

**New RAG Feature:** The system now uses an LLM to generate personalized, natural-language explanations for why each song was recommended, moving beyond static rule-based reasons. This makes recommendations feel more human and contextual.

It is not intended for commercial use or for users with highly complex or evolving tastes.

---

## 3. How the Model Works  

**Scoring Phase:**
The model looks at each song's features (like genre, mood, energy, tempo, valence, danceability, and acousticness) and compares them to what the user says they like. If a song matches the user's favorite genre or mood, it gets extra points. The model also checks if the song's numeric features (like tempo or valence) are close to the user's targets, and adds points if they are. For energy, it gives a higher score the closer the song's energy is to the user's target. After scoring all songs, it sorts them and recommends the top ones.

**Explanation Generation Phase (New with RAG):**
For each recommended song, the system retrieves song metadata and user preferences to build a RAG context. This context is sent to GitHub Copilot's managed LLM (via Python SDK), which generates a personalized explanation. If the SDK is unavailable or fails, the system gracefully falls back to rule-based explanations.

---

## 4. Data  

The dataset contains 20 songs, each with features like genre, mood, artist, energy, tempo, valence, danceability, and acousticness. Genres include pop, rock, jazz, lofi, synthwave, and more, with a variety of moods such as happy, intense, relaxed, and chill. No songs were added or removed from the starter set. Some genres and moods are underrepresented, and there are no songs with extremely high or low values for some features. The catalog is small, so it does not cover the full range of musical tastes or diversity found in real music libraries.

---

## 5. Strengths  

The system works well for users whose preferences match the genres and moods in the dataset. It gives clear, explainable recommendations, and the reasons for each pick are easy to understand. The model is good at finding songs that are close to the user's target energy, tempo, or valence. It is transparent, so users can see exactly why a song was recommended.

---

## 6. Limitations and Bias 

The model struggles with users whose preferences are outside the range of the dataset, such as those who want a genre or mood that isn't present, or an energy level higher than any song in the catalog. It can create "filter bubbles" by always recommending songs from the user's favorite genre or mood, ignoring other good matches. The system does not consider lyrics, artist popularity, or user listening history. One weakness found during experiments is that users with extreme or rare preferences (like very high energy) get only low-scoring, generic recommendations, making the system feel unresponsive for them. The model also does not promote diversity or surprise in its recommendations, so users may see the same types of songs repeatedly.

---


## 7. Evaluation

**Original Recommender:**
I tested the recommender using three different user profiles: one with impossible preferences (genre and mood not in the dataset, extreme energy), one with contradictory preferences (high acousticness, high energy, high danceability), and one with realistic but specific preferences (jazz, relaxed mood, high valence, moderate tempo, likes acoustic). For each profile, I checked if the top recommendations matched the user's stated preferences and if the explanations made sense. I also experimented with changing the genre weight, adding tempo and valence to the score, and disabling the mood check to see how the results changed.

**RAG Enhancement:**
I verified that the RAG feature:
- ✅ Generates unique, contextual explanations for each song and user profile
- ✅ Preserves recommendation scores (identical to rule-based scoring)
- ✅ Falls back gracefully when Copilot SDK unavailable or fails
- ✅ Logs all LLM interactions for transparency and debugging
- ✅ Works with diverse user profiles (extreme, contradictory, and realistic preferences)

I found that LLM-generated explanations make the system feel more helpful and personalized, even though the underlying scores remain unchanged. The fallback mechanism ensures reliability even without SDK access.

---

## 8. Future Work  


If I extended this project, I would swap out all the songs in the dataset for tracks from my own music library. This would let me test the recommender with my real preferences and see if it can actually give good suggestions. I would also look for ways to add more features, handle more complex or specific user tastes, and improve the diversity of recommendations so users don’t always get the same types of songs.

---

## 9. Personal Reflection  


Building this recommender showed me how complex real music apps like Spotify must be, since they serve millions of users and use far more features than my simple system. I learned it’s hard to recommend music to people with very specific tastes. For example, users with extreme preferences only got low-scoring, generic results, which made the system feel unhelpful for them. I also realized how much human judgment still matters, because the model can only use the features it has and might miss what really makes a song enjoyable for someone. I was surprised that even a simple scoring system could still feel somewhat personalized. I also found it important to double-check the changes suggested by AI tools, to make sure the code still made sense.

---

## 10. Responsible AI Reflection (RAG extension)

### What are the limitations or biases in your system?

**Data Bias:** The 20-song catalog is too small to represent the real world of music. With only 1–2 songs per genre, the system is biased toward its own limited library. If a user likes a genre that isn't included, the system will force a "best fit" that might be a terrible match.

**Preference Bias:** The system assumes people can describe their taste with numbers (like "0.85 energy"). Most people don't think this way. This creates a bias against users who choose music based on feelings, memories, or current trends rather than technical stats.

**Feature Limitations:** We only look at 8 basic audio features. The system ignores lyrics, the singer’s voice, and history. Because of this, it might suggest a heavy metal song to a K-pop fan just because they both have "high energy," even though the styles are completely different.

**Filter Bubble Risk:** Because the system gives extra points for matching the user's favorite genre, it creates a "bubble." Users will keep seeing the same type of music and will never be introduced to new styles that they might actually enjoy.

### Could your AI be misused, and how would you prevent that?

**Potential Misuse:**

- **Manipulating Results:** Someone could change the song data to unfairly promote certain artists or hide others for profit.

- **False Trust:** Users might believe the AI's explanations are "facts," even when the AI is just making up a creative story about why a song matches.

- **Hidden Tracking:** If this system saved every search, it could build a private profile of a user's moods and emotions, which could be used for invasive advertising.

**Prevention Strategies:**

- **Be Clear:** Show the actual math (the score) next to the AI's explanation so the user sees how it works.

- **Use Labels:** Clearly mark descriptions as "AI-generated" so users know they might not be 100% accurate.

- **Check the Logs:** Regularly review system logs to find where the AI is making mistakes or showing bias.

- **Privacy First:** Don't save a user's history or build a personal profile.

### What surprised you while testing your AI's reliability?

**"Reliable" errors:** I was surprised that the system could technically "work" but still give a bad result. For example, it suggested Megadeth (Heavy Metal) to a user looking for melancholy K-Pop. The code didn't crash, but the recommendation was wrong.

### Collaboration with AI

**One instance when AI gave a helpful suggestion:**

The AI flagged that some songs in the dataset appeared to be fictional, which led me to replace them with real tracks; otherwise the system might have generated inaccurate "lyrics" explanations.

**One instance where AI's suggestion was flawed or incorrect:**

Copilot suggested using a generic OpenAI or Claude API, but I preferred the GitHub Copilot SDK because it provides free GPT access for students.

---
