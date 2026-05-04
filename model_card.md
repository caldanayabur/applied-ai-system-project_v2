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
For each recommended song, the system retrieves song metadata and user preferences to build a RAG context. This context is sent to GitHub Copilot CLI, which generates a personalized explanation. If the CLI is unavailable or fails, the system gracefully falls back to rule-based explanations.

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
- ✅ Falls back gracefully when Copilot CLI unavailable or fails
- ✅ Logs all CLI interactions for transparency and debugging
- ✅ Works with diverse user profiles (extreme, contradictory, and realistic preferences)

I found that CLI-generated explanations make the system feel more helpful and personalized, even though the underlying scores remain unchanged. The fallback mechanism ensures reliability even without Copilot CLI access.

---

## 8. Future Work  


If I extended this project, I would swap out all the songs in the dataset for tracks from my own music library. This would let me test the recommender with my real preferences and see if it can actually give good suggestions. I would also look for ways to add more features, handle more complex or specific user tastes, and improve the diversity of recommendations so users don’t always get the same types of songs.

---

## 9. Personal Reflection  


Building this recommender showed me how complex real music apps like Spotify must be, since they serve millions of users and use far more features than my simple system. I learned it’s hard to recommend music to people with very specific tastes. For example, users with extreme preferences only got low-scoring, generic results, which made the system feel unhelpful for them. I also realized how much human judgment still matters, because the model can only use the features it has and might miss what really makes a song enjoyable for someone. I was surprised that even a simple scoring system could still feel somewhat personalized. I also found it important to double-check the changes suggested by AI tools, to make sure the code still made sense.

---

## 10. Responsible AI Reflection

### What are the limitations or biases in your system?

**Data Bias:** The 20-song catalog is small and non-representative of music diversity. It underrepresents many genres (only 1-2 songs per genre in some cases) and lacks diversity in artist representation. This means the system will inherently favor the represented genres and moods, potentially introducing filter bubbles.

**Preference Bias:** The system assumes users can articulate their preferences numerically (e.g., "I want energy 0.85"). Many people don't think about music this way, so the system may not work well for users with intuitive, emotional, or trend-based preferences.

**Feature Limitations:** The system only considers 8 audio features (energy, tempo, valence, danceability, acousticness, genre, mood, artist). It ignores lyrics, cultural context, artist identity, production quality, and listening history. A user might hate a song despite perfect audio feature matches.

**Filter Bubble Risk:** By emphasizing genre matching (+2 points), the system can create filter bubbles—users with narrow preferences will only see songs from that genre.

### Could your AI be misused, and how would you prevent that?

**Potential Misuse:**
1. **Recommendation Manipulation:** If someone could modify the song catalog or features, they could artificially promote/suppress certain music for commercial gain.
2. **Over-reliance on LLM Explanations:** Users might trust AI explanations uncritically without realizing they can hallucinate or oversimplify.
3. **Surveillance:** If expanded to track preferences over time, the system could create detailed listening profiles for manipulation or discrimination.

**Prevention Strategies:**
- Keep transparent: Show scoring logic alongside LLM explanations
- Educate users: Label LLM outputs as "AI-generated" and encourage critical thinking
- Audit outputs: Log all LLM calls and test for bias/hallucination
- Limit scope: Keep as a learning tool, not a commercial engine
- No tracking: Don't store listening history or build user profiles

### What surprised you while testing your AI's reliability?

1. **LLM Hallucinations:** Even with clean context, the LLM sometimes invented details ("perfect for working out" when energy wasn't high). This taught me that LLM outputs need validation.

2. **Graceful Degradation Works Better Than Expected:** Rule-based explanations like "genre match; mood match" are actually more trustworthy than an LLM sometimes making things up.

3. **Importance of Logging:** Structured JSON logs of every LLM call were invaluable for debugging. When explanations were weird, I could trace exactly what context the LLM received.

4. **Reliability > Perfection:** The system's resilience (3x retries, graceful fallback) mattered more than perfect LLM explanations. Users prefer a working system with imperfect explanations to a broken one with no explanations.

### Collaboration with AI

**One instance when AI gave a helpful suggestion:**

When designing the RAG context builder, I asked Copilot to review my prompt structure. It suggested breaking the context into clearly labeled sections (Song Information, User Preferences, Match Analysis) instead of a paragraph blob. This simple change significantly improved LLM explanation quality because the model could clearly distinguish different information types.

**One instance where AI's suggestion was flawed or incorrect:**

Copilot suggested using async/await for the LLM API calls to improve performance. I started implementing this, but it turned out to be overkill for a CLI tool processing 5 recommendations sequentially. The complexity wasn't worth the marginal speedup, and it made error handling harder. I reverted to simple synchronous calls with retry logic.

---

**Key Takeaway:** AI responsibility means:
- Admitting when you don't know (graceful fallback)
- Showing your work (logging, transparent context)
- Staying humble about limitations (documenting biases)
- Prioritizing reliability over perfection
