# EchoGrid Demo Script

This script is for a conference-style synthetic simulation demo.

## Setup

1. Start the app with `make run`.
2. Open the Streamlit URL, usually `http://localhost:8501`.
3. Keep provider set to `mock`.
4. Choose `City restricts short-term rentals` or `AI surveillance in public spaces`.
5. Use `300` agents, seed `42`, four framings, and echo simulation enabled.

## Talking Path

1. Start on `Overview`.
   - State that EchoGrid is synthetic and not a poll.
   - Show the event, frame count, reaction count, echo item count, and average share likelihood.
2. Open `Initial Reaction`.
   - Show stance distribution and filter by frame or stance.
   - Explain that each row is a synthetic agent reaction, not a real person.
3. Open `Echo Timeline`.
   - Walk from original event to frames, reactions, echo items, and echo reactions.
4. Open `Echo Items`.
   - Filter by echo type and target bubble.
   - Point out distortion and estimated reach.
5. Open `Amplification` and `Bubble Impact`.
   - Explain trust, anger, virality, and bubble-specific shifts.
6. Open `Comments`.
   - Filter by stance, frame, and social bubble to show representative synthetic comments.
7. Open `Export`.
   - Download the full ZIP bundle and note that every export carries synthetic-use disclaimers.

## Recommended Close

EchoGrid is best framed as a hypothesis-generation tool for media literacy and risk analysis. The release build is strongest in deterministic mock mode; hybrid LLM generation should be treated as a future extension with strict safety and cost controls.
