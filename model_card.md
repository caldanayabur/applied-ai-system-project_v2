# Music Recommender Model Card

## 1. Model Name

BeatBuddy, a rule-based music recommender with optional Copilot-generated song descriptions.

---

## 2. Intended Use

This project is designed for classroom exploration and small-scale experimentation, not for production music recommendation.

The current code recommends songs from a fixed 20-song CSV catalog using interpretable scoring rules. After ranking, it can generate a short natural-language description for each recommended song using GitHub Copilot's managed LLM. If Copilot is unavailable, disabled, or fails, the system falls back to rule-based descriptions and still returns output.

The CLI currently runs three built-in user profiles to exercise edge cases and show the different output paths.

---

## 3. How the System Works

### Data Loading

`load_songs` reads `data/songs.csv` into dictionaries with these fields: `id`, `title`, `artist`, `genre`, `mood`, `energy`, `tempo_bpm`, `valence`, `danceability`, and `acousticness`.

### Scoring

`score_song` compares each song to the user profile and adds points for:

- matching `favorite_genre` (+2.0)
- matching `favorite_mood` (+1.0)
- matching `favorite_artist` when provided (+1.0)
- closeness to `target_tempo` (+1.0)
- closeness to `target_danceability` (+1.0)
- closeness to `target_acousticness` (+1.0)
- closeness to `target_valence` (+1.0)
- energy similarity computed as `1 - abs(song_energy - target_energy)`

`recommend_songs` ranks songs by total score and returns the top `k` results.

### Description Generation

`recommend_songs_with_descriptions` first computes the same deterministic ranking, then calls `LLMEngine.generate_song_description` for each selected song.

The LLM description path uses song title, artist, and metadata only. It does not use user preferences to write the description, and it does not fetch lyrics from an external corpus. The prompt asks for a brief description of the song's themes and the artist's style, and the engine normalizes the output into a fixed `Title – Artist Description: ...` format.

If the Copilot SDK is not available, or if `LLM_FORCE_FALLBACK=1` is set, the system uses a rule-based description built from genre and mood.

### Supporting Utilities

`rag_context.py` builds context from the selected song, user preferences, and match reasons. The recommendation pipeline sends this context to the LLM prompt, grounding the generated description in the local catalog. This is context-based RAG without a separate vector database.

The `Song`, `UserProfile`, and `Recommender` classes remain in `recommender.py` for compatibility with tests and examples, but the functional API is the main implementation used by the CLI.

---

## 4. Data

The catalog contains 20 songs spanning genres such as pop, rock, jazz, lofi, ambient, synthwave, and chip tune. Each song has a small set of audio features rather than lyrics, popularity, or listening-history signals.

The dataset is intentionally small and uneven. That makes it useful for demonstrating explainable scoring, but it also limits coverage of real-world music taste.

---

## 5. Strengths

The system is easy to reason about because the ranking logic is explicit and reproducible. A user can see why a song was recommended through the score and the logged reasons.

The description layer improves presentation without changing the recommendation order. When Copilot is available, it produces more natural text; when it is not, the fallback still keeps the app usable.

The logging layer is also a strength. It records recommendation requests, scoring completion, LLM calls, generated descriptions, and errors in structured JSON for debugging.

---

## 6. Limitations and Bias

The recommender is only as good as the 20-song catalog. If a user prefers a genre or mood that is not present, the system will still return a nearest match rather than a truly good recommendation.

The score is based on a limited feature set and does not use lyrics, listening history, popularity, or user feedback. That creates bias toward songs that fit the available fields instead of songs that would actually satisfy a real listener.

The optional LLM descriptions can still be generic because they are generated from metadata and widely known facts only. The prompt reduces hallucination risk, but it cannot eliminate it completely.

Also, if you try running the system with the default model (GPT-4.1), it will take a very long time to generate each description. This can make the user experience slow and frustrating.

---

## 7. Evaluation

The repository includes 15 tests across three test modules. Those tests verify song loading, rule-based scoring, recommendation ordering, description generation, fallback behavior, prompt construction, and context formatting.

The main behaviors validated by the tests are:

- recommendation scores stay the same with or without the LLM description layer
- fallback descriptions are returned when the LLM path is unavailable
- prompt text includes the required constraints and song metadata
- the context helper functions format song and user information correctly

The current CLI also serves as a lightweight end-to-end check because it runs three profiles that stress different preference combinations.

---

## 8. Future Work

If this project were extended, the next practical steps would be:

- integrate the existing context builder into the runtime prompt path
- add caching for repeated song descriptions
- expand the catalog with more songs and richer metadata
- add user feedback so the scoring weights can be tuned
- build a web interface on top of the current CLI workflow

---

## 9. Personal Reflection

This project shows the value of separating deterministic ranking from generative text. The ranking is easy to verify, while the LLM layer improves the user-facing explanation without affecting the core recommendation order.

It also shows the trade-off between simplicity and personalization. A small, interpretable scoring function is easy to test, but it cannot capture the complexity of real listening behavior.

---

## 10. Responsible AI Reflection

### What are the limitations or biases in your system?

The dataset bias is the biggest limitation. A 20-song catalog cannot represent the range of real music preferences, so the system tends to overfit to the songs it already has.

The feature bias is also important. The recommender assumes preferences can be expressed as numbers such as energy or valence, which is not how most people naturally describe music taste.

The description layer is intentionally constrained, but it still depends on a general-purpose LLM. That means the output can sound confident even when it is only a high-level interpretation.

### Could your AI be misused, and how would you prevent that?

If the scoring rules or catalog were edited without review, the system could be skewed toward certain songs or artists. The fix is to keep the scoring transparent and the dataset under version control.

The LLM output should not be treated as factual biography. The prompt and fallback logic help, but the interface should still label descriptions as AI-generated.

### What surprised you while testing your AI's reliability?

**"Reliable" errors:** I was surprised that the system could technically "work" but still give a bad result. For example, it suggested Megadeth (Heavy Metal) to a user looking for melancholy K-Pop. The code didn't crash, but the recommendation was wrong.

### Collaboration with AI

**One instance when AI gave a helpful suggestion:**

The AI flagged that some songs in the dataset appeared to be fictional, which led me to replace them with real tracks; otherwise the system might have generated inaccurate "lyrics" explanations.

**One instance where AI's suggestion was flawed or incorrect:**

Copilot suggested using a generic OpenAI or Claude API, but I preferred the GitHub Copilot SDK because it provides free GPT access for students.

---
