# AGENTS.md — AI Architecture & Engineering Guidelines
**Repository:** `DesiReels Studio`  
**Purpose:** Autonomous, local-first short-video creation, self-learning, and multi-platform publishing engine for Indian travel, culture, and street food.

---

## 1. Prime Directives for AI Agents

1. **Safety & Credential Boundary (NON-NEGOTIABLE):**
   - NEVER commit `.env`, `credentials/*`, access tokens, or rendered `.mp4` video files to Git.
   - All external publisher calls MUST respect `DRY_RUN=true` by default.
   - Never mock or invent fake credentials that look like real API secrets. Use clear placeholder names (`YOUR_ACCESS_TOKEN`).

2. **MacBook Air M5 Fanless Thermal Budget:**
   - No continuous polling loops or 24/7 daemon processes.
   - All modules must be fast, event-driven, and run in **under 3 minutes total**.
   - Use quantized Ollama models (`llama3.1:8b` or lighter) and efficient local TTS.
   - Use FFmpeg with hardware acceleration (`h264_videotoolbox`) or `-preset fast -crf 22` to avoid CPU thermal throttling.

3. **Format Consistency (30s Vertical 9:16):**
   - Resolution: Exactly `1080x1920`.
   - Audio: AAC stereo, 44.1kHz or 48kHz, -16 LUFS normalized.
   - Word budget: 75–85 words total.
   - 5–6 scenes with high-contrast, animated subtitle safe zones (bottom margin $\ge 120$px to avoid UI overlap on Instagram/TikTok/Shorts).
   - Faststart (`-movflags +faststart`) enabled on all output MP4s.

4. **Self-Improvement Protocol:**
   - Any learning adjustments must be written to `memory/style_playbook.json` and logged to `memory/feedback_history.json`.
   - Do NOT overwrite user modifications in `memory/style_playbook.json` without merging existing parameters.

---

## 2. Component Structure & Contracts

```
src/
├── config.py         <- Centralized, strongly-typed settings (pydantic or dataclass)
├── db.py             <- SQLite schema & connection management (studio.db)
├── research.py       <- Factual Wikipedia/Wikivoyage grounding engine
├── planner.py        <- Scene & script generator via local Ollama
├── audio_engine.py   <- TTS synthesis + Whisper word timestamp alignment
├── visual_engine.py  <- B-roll resolver & FFmpeg zoompan/pan motion filters
├── media_builder.py  <- Master video compositor (audio + video + subtitles -> 1080x1920)
├── learner.py        <- Reference video cut analysis & human feedback loop
├── dashboard.py      <- Lightweight review UI (http://localhost:8500)
└── publisher.py      <- YouTube Shorts, Instagram Reels & Facebook Reels publisher
```

---

## 3. Database Conventions

- All timestamps are stored as ISO 8601 strings in Indian Standard Time (`Asia/Kolkata` / `+05:30`).
- Database schema lives in `src/db.py`.
- Any schema alterations must use backwards-compatible `ALTER TABLE` or migration guards to prevent data loss.

---

## 4. Testing & Verification Standard

Before declaring any feature complete:
1. Run syntax and import checks on modified python files.
2. In dry-run mode, verify that no network mutating requests are made.
3. Verify that rendered MP4s conform to:
   - Width: 1080, Height: 1920
   - Video codec: h264
   - Audio codec: aac
   - Duration: 28.0s - 31.0s
