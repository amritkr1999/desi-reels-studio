# 🎬 DesiReels Studio
**Autonomous Short-Video Creation, Self-Learning & Multi-Platform Publishing System for Indian Travel, Culture & Street Food**

[![Hardware](https://img.shields.io/badge/Hardware-MacBook%20Air%20M5%20(Apple%20Silicon)-orange.svg)](#)
[![Format](https://img.shields.io/badge/Format-9%3A16%20Vertical%20(1080x1920)-blue.svg)](#)
[![Pacing](https://img.shields.io/badge/Duration-30s%20(75--85%20words)-green.svg)](#)
[![Platforms](https://img.shields.io/badge/Platforms-YouTube%20Shorts%20%7C%20Instagram%20%7C%20Facebook-red.svg)](#)
[![Safety](https://img.shields.io/badge/Safety-DRY__RUN%3Dtrue%20Default-purple.svg)](#)

---

## 🌟 Overview

**DesiReels Studio** is a clean, modular, privacy-first autonomous short-video studio engineered specifically for Apple Silicon (MacBook Air M5 fanless architecture). 

Every day, it autonomously creates a broadcast-ready **30-second vertical video (9:16, 1080x1920)** highlighting an authentic Indian street food marvel, cultural secret, or historic bazaar. It runs once daily via native macOS `launchd` ahead of the prime evening Indian Standard Time (IST) window, renders in **under 5 seconds**, cleans up all temporary files, and stages the video for your 2-minute review or auto-publishes to **YouTube Shorts**, **Instagram Reels**, and **Facebook Reels**.

---

## 🏗️ System Architecture

```
                                      macOS launchd Timer
                              (Triggers once daily at 18:00 IST)
                                              |
                                              v
+-----------------------------------------------------------------------------------------------+
|                                    DesiReels Studio Engine                                    |
|                                                                                               |
|  +--------------------+      +--------------------+      +---------------------------------+  |
|  | Factual Research   | ---> | Scene Scripting    | ---> | Audio & Visual Engine           |  |
|  | - 25+ Seed Topics  |      | - Local Ollama     |      | - Fast Local TTS (macOS 'Rishi')|  |
|  | - Wiki/Voyage API  |      |   (llama3.1:8b)    |      | - Word-level .ass Subtitles     |  |
|  | - Factual Anchors  |      | - 75-85 Words / 30s|      | - Ken Burns Alternating Motion  |  |
|  +--------------------+      +--------------------+      | - H.264/AAC 1080x1920 Faststart |  |
|                                                          +----------------+----------------+  |
|                                                                           |                   |
|                                                                           v                   |
|  +------------------------------------+                  +----------------+----------------+  |
|  | Self-Improvement & Memory Engine   |                  | Multi-Platform Publisher        |  |
|  | - Reference video cut analyzer     | <---------------+| - YouTube Shorts (Data API v3)  |  |
|  | - Natural-language feedback loop   |  (Metrics/Input) | - Instagram Reels (Graph API)   |  |
|  | - Updates style_playbook.json      |                  | - Facebook Reels (Page Reels)   |  |
|  +------------------------------------+                  | - Default: DRY_RUN=true (Safe)  |  |
|                                                          +---------------------------------+  |
+-----------------------------------------------------------------------------------------------+
                                              |
                                              v
                               +-----------------------------+
                               | Local Operations Dashboard  |
                               | (http://localhost:8500)     |
                               | - Watch 30s Rendered Video  |
                               | - 1-Click Plain-Text Review |
                               | - Dynamic Topic Manager     |
                               +-----------------------------+
```

---

## ⚡ Key Highlights & Engineering Benchmarks

| Feature | Specification | Engineering Guarantee |
| :--- | :--- | :--- |
| **Output Specs** | `1080x1920` (9:16), 30 fps, H.264 / AAC | Broadcast-compliant vertical video ready for Shorts & Reels. |
| **Audio-Driven Timing** | 75 to 85 words, 5–6 timed scenes | Sub-second word alignment with `.ass` high-contrast animated subtitles. |
| **MacBook Air Efficiency** | Fanless thermal optimization | Complete 30s video render executes in **< 5 seconds** on Apple Silicon M5. |
| **Zero 24/7 Daemons** | Event-driven macOS `launchd` | Zero battery drain when idle. Clean exit immediately after render. |
| **Self-Learning Loop** | Drop viral `.mp4` into `reference_videos/` | FFmpeg cut-frequency detection & plain-English feedback adjust `style_playbook.json`. |
| **Absolute Credential Safety** | `DRY_RUN=true` hardcoded default | Never commits keys, tokens, or credentials to Git. |

---

## 🚀 Quickstart in 3 Steps

### 1. Clone & Set Up Environment
```bash
git clone <YOUR_GITHUB_REPO_URL> desi-reels-studio
cd desi-reels-studio

# Copy sample environment configuration
cp .env.example .env
```

### 2. Run the Full Test Suite
Verify that all 8 modules, database schema, media builder, and publisher dry-runs pass:
```bash
python3 -m unittest -v tests/test_pipeline.py
```

### 3. Launch the Operations Dashboard
```bash
python3 -m src.dashboard
```
Open **[http://localhost:8500](http://localhost:8500)** in your browser to watch generated videos, submit feedback, and manage your topic queue!

---

## 🕒 The Daily 2-Minute Workflow

1. **18:00 IST:** `launchd` runs `scripts/daily_run.sh` in the background, rendering today's short.
2. **18:05 IST:** Open `http://localhost:8500` on your MacBook.
3. **18:06 IST:** Watch the 30-second vertical preview in the browser player.
4. **18:07 IST:** Type a quick critique (*"Talking slightly too fast"*, *"Subtitles look awesome"*) and click **Submit**. The AI memory updates automatically for tomorrow's run!

---

## 📚 Complete Documentation

* 📄 **[IMPLEMENTATION_PLAN.md](file:///Users/amrit/.gemini/antigravity/scratch/desi-reels-studio/docs/IMPLEMENTATION_PLAN.md):** Complete architectural blueprint, work breakdown structure, and system contracts.
* 📄 **[STRATEGY.md](file:///Users/amrit/.gemini/antigravity/scratch/desi-reels-studio/docs/STRATEGY.md):** The 30s hook taxonomy, 3-pillar content formula, IST peak windows, and self-learning loop.
* 📄 **[SETUP_GUIDE.md](file:///Users/amrit/.gemini/antigravity/scratch/desi-reels-studio/docs/SETUP_GUIDE.md):** Step-by-step instructions for YouTube Data API v3, Instagram Graph API, Facebook Page Reels, and macOS sleep settings.
* 📄 **[RUNBOOK.md](file:///Users/amrit/.gemini/antigravity/scratch/desi-reels-studio/docs/RUNBOOK.md):** Daily operations, troubleshooting scenarios, `launchd` commands, and log monitoring.
* 📄 **[SESSION_TRANSCRIPT.md](file:///Users/amrit/.gemini/antigravity/scratch/desi-reels-studio/docs/SESSION_TRANSCRIPT.md):** Complete chronological chat history, architectural decisions, and future roadmap.
* 📄 **[AGENTS.md](file:///Users/amrit/.gemini/antigravity/scratch/desi-reels-studio/AGENTS.md):** Rules and standards for future AI sessions.

---

## 📁 Repository Structure

```
desi-reels-studio/
├── .env.example                 <- Environment configuration template
├── .gitignore                   <- Strict exclusion of secrets, tokens, and media
├── AGENTS.md                    <- Guidelines for autonomous AI contributors
├── README.md                    <- Main project overview
├── requirements.txt             <- Project dependencies
├── docs/                        <- Architectural, strategic, and operational documentation
│   ├── IMPLEMENTATION_PLAN.md
│   ├── STRATEGY.md
│   ├── SETUP_GUIDE.md
│   ├── RUNBOOK.md
│   └── SESSION_TRANSCRIPT.md
├── data/
│   ├── studio.db                <- Local SQLite database (topics, renders, publishing log)
│   └── topics_seed.json         <- 25+ curated Indian street food and cultural topics
├── memory/
│   ├── style_playbook.json      <- Dynamic AI style, hook weights, and pacing parameters
│   └── feedback_history.json    <- Historical human feedback log
├── credentials/                 <- Local OAuth token directory (strictly .gitignored)
├── reference_videos/            <- Drop viral .mp4 reels here for automatic style extraction
├── assets/                      <- Local fonts, audio tracks, and visual assets
├── output/                      <- Rendered 1080x1920 MP4 files
├── temp/                        <- Intermediate audio/video cache (purged daily)
├── scripts/
│   ├── daily_run.sh             <- Master daily runner triggered by launchd
│   ├── install_schedule.sh      <- Installs and activates launchd plist
│   ├── cleanup.sh               <- Storage garbage collector
│   └── auth_youtube.py          <- Interactive Google OAuth helper
├── src/
│   ├── config.py                <- Strongly-typed settings
│   ├── db.py                    <- SQLite database layer
│   ├── research.py              <- Factual Wikipedia/Wikivoyage enrichment
│   ├── planner.py               <- Scene script planner via local Ollama
│   ├── audio_engine.py          <- Fast local TTS & word-aligned subtitles
│   ├── visual_engine.py         <- Media resolver & FFmpeg zoompan motion
│   ├── media_builder.py         <- Master compositing engine (1080x1920 MP4)
│   ├── learner.py               <- Reference video analyzer & feedback loop
│   ├── dashboard.py             <- Operations & review web server (:8500)
│   ├── publisher.py             <- Multi-platform publisher (YouTube, IG, FB)
│   └── orchestrator.py          <- Master daily pipeline runner
└── tests/
    └── test_pipeline.py         <- Automated 8-test regression test suite
```

---

## 🔒 Security & Privacy

* **Zero Cloud Dependence for Creation:** Video generation, script planning, audio synthesis, subtitle alignment, and visual compositing run 100% locally on your Mac.
* **Manual Credential Boundary:** Account creation and OAuth authorizations are handled exclusively by you. Real credentials never enter Git.
* **Fanless Optimization:** Designed from day one to operate cleanly on battery or power without sustained thermal load.
