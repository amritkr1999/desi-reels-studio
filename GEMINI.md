# GEMINI.md — Project Workspace Context & Instructions

This repository is **DesiReels Studio**, an autonomous 30-second Indian travel, culture, and street-food short-video production and self-learning system built on Apple Silicon (MacBook Air M5).

---

## 🧭 Workspace Navigation & Key Files
- **Full Architecture & Previous Session Dialogue:** [`docs/SESSION_TRANSCRIPT.md`](docs/SESSION_TRANSCRIPT.md)
- **Content Strategy & Pacing Rules:** [`docs/STRATEGY.md`](docs/STRATEGY.md)
- **Implementation Plan & Architecture:** [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)
- **Setup & Credentials (YouTube, Instagram, Facebook):** [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)
- **Operations & Runbook:** [`docs/RUNBOOK.md`](docs/RUNBOOK.md)
- **Agent Guidelines & Code Conventions:** [`AGENTS.md`](AGENTS.md)

---

## ⚡ Core Directives for Any Agent in This Workspace
1. **Safety:** Keep `DRY_RUN=True` default unless the user explicitly requests live publishing. Never commit `.env`, `credentials/*`, `output/*.mp4`, or `data/*.db` to Git.
2. **MacBook Air M5 Thermals:** All pipeline tasks must be lightweight and event-driven (< 3 minutes runtime). No 24/7 background polling daemons.
3. **Format Standards:** Exactly 1080x1920 (9:16 vertical), 28–30s duration, 75–85 words of narration, H.264/AAC, faststart enabled.
4. **Self-Learning:** When user feedback is provided, update `memory/style_playbook.json` and log to `data/studio.db`.
5. **Testing Standard:** Run `python3 -m unittest -v tests/test_pipeline.py` after modifying any core module to verify all 8 regression tests pass.

---

## 🚀 Quick Execution Commands
- **Run Review Dashboard:** `python3 -m src.dashboard` (Access at `http://localhost:8500`)
- **Run Daily Generation (Dry Run):** `python3 -m src.orchestrator`
- **Run Daily Generation (Live Publish):** `python3 -m src.orchestrator --live`
- **Run Regression Tests:** `python3 -m unittest -v tests/test_pipeline.py`
- **Purge Cache:** `./scripts/cleanup.sh`
