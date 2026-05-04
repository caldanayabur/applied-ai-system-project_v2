# 🎵 Music Recommender with RAG Enhancement

## Original Project Context

This project extends the **Music Recommender Simulation** (from Modules 1-3), which scored songs based on user preferences for genre, mood, energy, acousticness, and other audio features using rule-based weighted scoring. The original system ranked candidates by static point totals and returned explanations like "genre match (+2.0); mood match (+1.0)". This advanced version generalizes that pattern by integrating **Retrieval-Augmented Generation (RAG)** with GitHub Copilot's managed LLM to dynamically generate personalized, natural-language explanations that contextualize why each recommendation matches the user's taste.

## Project Summary

BeatBuddy-RAG is a Python music recommendation system that recommends songs from a catalog based on user preferences (genre, mood, energy, tempo, valence, danceability, acousticness) and generates AI-powered explanations via Retrieval-Augmented Generation using GitHub Copilot's managed LLM. The system gracefully falls back to rule-based explanations if the LLM is unavailable, ensuring reliability. It bridges traditional content-based filtering with modern LLM-powered natural language generation.

## Architecture Overview

BeatBuddy-RAG implements a **three-stage pipeline**:

1. **Scoring Engine** (`recommender.py`): Loads songs from CSV, scores each against user preferences using rule-based logic (+2 genre match, +1 mood match, +1 for feature closeness, +similarity for energy), and returns top-k recommendations sorted by score.

2. **RAG Context Builder** (`rag_context.py`): Constructs a rich context document from song metadata, user preferences, and scoring reasons. This context is formatted as a structured prompt for the LLM.

3. **LLM Explanation Generator** (`llm_engine.py`): Calls GitHub Copilot CLI (with 3x retry logic) to generate personalized explanations. Falls back to rule-based explanations if the CLI is unavailable, disabled, or fails.

The `main.py` orchestrator drives the flow: load songs → score → retrieve context → generate explanation via CLI → display results.

### Data Flow

```
User Preferences → Load Songs CSV → Score Each Song (rule-based)
                                           ↓
                                  Retrieve Top K
                                           ↓
                               Build RAG Context
                                           ↓
                          Query LLM for Explanation
                                           ↓
                        (Fallback to rule-based if LLM unavailable)
                                           ↓
                              Output Recommendations
```

## Folder Structure

```
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI orchestrator
│   ├── recommender.py          # Core scoring + RAG-enhanced recommendation
│   ├── llm_engine.py           # GitHub Copilot CLI integration with retry logic
│   ├── rag_context.py          # RAG context building utilities
│   └── logger.py               # Structured JSON logging
├── data/
│   └── songs.csv               # 20-song catalog with audio features
├── tests/
│   ├── test_recommender.py     # Original functionality tests
│   ├── test_llm_connection.py  # LLM engine tests
│   └── test_rag_pipeline.py    # End-to-end RAG pipeline tests
├── requirements.txt
├── README.md
└── model_card.md
```

### Setup

#### Prerequisites

- Python 3.8 or higher
- pip
- **GitHub CLI** installed and authenticated (for Copilot CLI access)
  - Install: https://cli.github.com/
  - Authenticate: `gh auth login`
  - Enable Copilot CLI: `gh copilot --version`

#### Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify GitHub Copilot CLI is available:**
   ```bash
   gh copilot --version
   ```
   If Copilot CLI is not available, the system will automatically fall back to rule-based explanations.

3. **Run the app:**
   ```bash
   python -m src.main
   ```

4. **Run tests:**
   ```bash
   pytest                                    # All tests
   pytest tests/test_rag_pipeline.py        # RAG tests only
   ```

## Sample Interactions

### Example 1: Jazz Lover with Relaxed Mood

**Input:**
```
User Profile:
  - favorite_genre: jazz
  - favorite_mood: relaxed
  - target_energy: 0.4
  - target_tempo: 90
  - likes_acoustic: True
```

**Rule-Based Output (Fallback):**
```
1. Coffee Shop Stories (Slow Stereo)
   Score: 5.00
   Reasons: genre match (+2.0); mood match (+1.0); tempo close (+1.0); valence close (+1.0)
```

**RAG-Enhanced Output (With LLM):**
```
1. Coffee Shop Stories (Slow Stereo)
   Score: 5.00
   Explanation: We picked 'Coffee Shop Stories' because it matches your love of jazz and relaxed vibes—the smooth acousticness (0.89) and moderate tempo (90 BPM) create the perfect focus music.
```

### Example 2: High-Energy Pop Fan

**Input:**
```
User Profile:
  - favorite_genre: pop
  - favorite_mood: happy
  - target_energy: 0.85
  - target_danceability: 0.8
```

**Rule-Based Output:**
```
1. Sunrise City (Neon Echo)
   Score: 3.65
   Reasons: genre match (+2.0); mood match (+1.0); energy similarity (+0.65)
```

**RAG-Enhanced Output:**
```
1. Sunrise City (Neon Echo)
   Score: 3.65
   Explanation: 'Sunrise City' is a perfect match for your pop preferences and upbeat mood—with high energy (0.82) and danceability (0.79), it'll keep you moving and energized.
```

### Example 3: Extreme Preferences (Edge Case)

**Input:**
```
User Profile:
  - favorite_genre: k-pop  # Not in catalog
  - favorite_mood: melancholy  # Not in catalog
  - target_energy: 1.5  # Out of range (max in catalog is 0.99)
```

**Output (Graceful Degradation):**
```
1. Quantum Leap (Future Logic)
   Score: 0.47
   Explanation: We couldn't find an exact match for k-pop or melancholy in our catalog, but 'Quantum Leap' has the highest energy (0.97) of available songs, getting as close as possible to your target.
```

## Design Decisions

### 1. **RAG for Explanation Generation**
**Decision:** Use LLM with retrieved context to generate personalized explanations rather than static rule-based text.  
**Trade-off:** Requires external API (cost + latency), but produces human-like, contextual explanations. Graceful fallback ensures the system works without it.

### 2. **Rule-Based Scoring (No ML Model)**
**Decision:** Keep the scoring logic simple and interpretable (weighted points) rather than training a ML model.  
**Trade-off:** More transparent and reproducible, but less adaptive to complex user preferences.

### 3. **GitHub Copilot SDK Integration with Retry Logic**
**Decision:** Use tenacity library for 3x exponential backoff retries on API failures.  
**Trade-off:** More resilient to transient failures, but adds latency and complexity.

### 4. **Structured JSON Logging**
**Decision:** Log all events (LLM calls, explanations, errors) as JSON for easy parsing and analysis.  
**Trade-off:** More verbose, but provides transparency and enables debugging.

### 5. **Fallback to Rule-Based Explanations**
**Decision:** If LLM fails or is unavailable, seamlessly degrade to rule-based explanations.  
**Trade-off:** Users always get recommendations, but explanations vary in quality.

## Testing Summary

**Test Coverage:** 15 unit and integration tests across 3 test modules.

### What Worked

- ✅ Song loading and CSV parsing correctly validated metadata
- ✅ Rule-based scoring is consistent and reproducible
- ✅ LLM engine initializes and integrates with retry logic
- ✅ RAG context builder correctly formats song/preference metadata
- ✅ Fallback mechanism works reliably when LLM unavailable
- ✅ Recommendation scores remain identical with/without LLM (only explanations change)
- ✅ All 15 tests pass (0 failures)

### What Didn't Work (and Fixes Applied)

- ❌ Initial Unicode encoding issue on Windows with emoji characters in status messages → Fixed by removing special characters
- ❌ LLM initialization without API key crashed → Added graceful exception handling and automatic fallback
- ❌ Import path issues in tests → Fixed with relative imports and __init__.py

### What We Learned

- **Graceful degradation is critical** in production AI systems. The system must provide value even when external services fail.
- **Structured logging is essential** for debugging LLM integrations and understanding system behavior.
- **Prompt engineering matters** — small changes to the LLM prompt significantly affect output quality.
- **Fallback mechanisms are not optional** — they're a core requirement for reliability.

## Reflection

**What This Project Taught About AI and Problem-Solving:**

1. **AI as Enhancement, Not Replacement:** Integrating an LLM showed that AI-generated explanations are more engaging than static text, but they also highlight the importance of good context. Poor context leads to poor explanations. This reinforced that AI works best when embedded in a well-designed system with clear data retrieval and fallbacks.

2. **Reliability Over Perfection:** Building the fallback mechanism taught me that a system that degrades gracefully is more valuable than one that tries to be perfect but crashes. Users prefer imperfect explanations to no recommendations at all.

3. **Logging as a First-Class Concern:** Adding structured JSON logging proved invaluable for debugging LLM integrations. Every LLM call, error, and fallback is now traceable, making the system observable and debuggable.

4. **Trade-offs are Everywhere:** Choosing to keep rule-based scoring simple meant sacrificing adaptive personalization. Choosing to use GitHub Copilot SDK meant accepting latency and API dependencies. Understanding these trade-offs helped me make intentional decisions rather than just defaulting to the easiest path.

**Next Steps (If Extending):**
- Integrate multiple LLM providers (Azure OpenAI, Anthropic Claude, local models) with a provider abstraction
- Implement caching for frequently recommended songs to reduce LLM API costs
- Add user feedback loops to measure explanation quality and improve prompts
- Expand the song catalog and add more sophisticated features (lyrics, popularity, trends)
- Build a web interface (FastAPI + React) for broader usability

---

**Technical Stack:**
- Python 3.8+
- GitHub Copilot CLI (direct subprocess integration)
- pandas, pytest, tenacity, pydantic, python-dotenv
- Structured logging, retry patterns, graceful degradation

**Lessons Applied:**
- Always build with fallback mechanisms
- Log comprehensively for observability
- Keep systems simple and understandable
- Test edge cases (missing API keys, API failures, extreme preferences)
- Document design decisions, not just code
