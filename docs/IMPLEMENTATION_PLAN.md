# DesiReels Studio — Implementation Plan & Architecture Blueprint
**Autonomous, Local-First Short-Video Creation, Self-Learning & Publishing System for Indian Travel, Culture & Street-Food**
**Target Hardware:** MacBook Air M5 (Apple Silicon, Fanless) | **Target Form Factor:** 9:16 Vertical Video (1080x1920, 30s, ~8–15 MB, H.264/AAC, Faststart)

---

## 1. System Overview & Architecture

`DesiReels Studio` is an end-to-end, privacy-respecting, local-first autonomous short-video production pipeline designed specifically for Apple Silicon (M5 fanless architecture). It operates on a **once-daily, event-driven cycle** via macOS `launchd` rather than a battery-draining 24/7 daemon.

```
                           +----------------------------------------+
                           |           macOS launchd Timer          |
                           |   (Triggers 45m ahead of IST target)   |
                           +-------------------+--------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------------------+
|                                      DesiReels Studio Engine                                      |
|                                                                                                   |
|  +---------------------+      +---------------------+      +-----------------------------------+  |
|  |  Research & Topics  | ---> |   Scene & Script    | ---> | Audio & Visual Engine             |  |
|  |  - Seeded Catalog   |      |   Planner           |      | - Fast Local TTS (Kokoro/macOS)   |  |
|  |  - Wiki/Voyage API  |      |   - Ollama (llama3) |      | - Faster-Whisper Word Timestamps  |  |
|  |  - Anti-hallucinate |      |   - Style Playbook  |      | - High-contrast .ass Subtitles    |  |
|  +---------------------+      +---------------------+      | - Curated Asset / Pexels Engine   |  |
|                                                            | - FFmpeg Motion Engine (Zoom/Pan) |  |
|                                                            +-----------------+-----------------+  |
|                                                                              |                    |
|                                                                              v                    |
|  +-------------------------------------+                  +------------------+-----------------+  |
|  | Self-Learning & Memory Engine       |                  | Multi-Platform Publisher           |  |
|  | - Video cut rhythm analyzer         | <---------------+| - YouTube Shorts (Data API v3)     |  |
|  | - Feedback loop -> style_playbook   |  (Metrics/Input) | - Instagram Reels (Meta Graph API) |  |
|  | - Best-performing hook & pacing     |                  | - Facebook Reels (Page Reels API)  |  |
|  +-------------------------------------+                  | - Default: DRY_RUN=true (Safe)     |  |
|                                                           +------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
                                               |
                                               v
                                +------------------------------+
                                | Local Review Dashboard       |
                                | (http://localhost:8500)      |
                                | - Watch & Verify Render      |
                                | - 1-Click Approve / Publish  |
                                | - Feedback & Performance Log |
                                +------------------------------+
```

---

## 2. Environment Audit Findings & Prerequisites

A rigorous audit of the host environment revealed:

| Component | Status | Details / Actions Required |
| :--- | :--- | :--- |
| **macOS & Chip** | ✅ Detected | macOS 27.2.1, Apple Silicon `arm64` (MacBook Air M5). Ideal for Metal acceleration. |
| **Python** | ✅ Detected | Python 3.14.6 at `/opt/homebrew/bin/python3`. |
| **FFmpeg** | ✅ Detected | FFmpeg 8.1.2 at `/opt/homebrew/bin/ffmpeg` with H.264/AAC and Apple Silicon capabilities. |
| **Git** | ✅ Detected | Git 2.55.0 installed and operational. |
| **Ollama** | ⚠️ Installed | Client 0.40.16 present at `/usr/local/bin/ollama`. Models present: `llama3.1:8b`, `deepseek-ocr:latest`. The daemon needs to be verified running (`ollama serve` or Ollama macOS app). |
| **Package Tool (uv)** | ❌ Missing | Not found in PATH. Project will support `uv` (recommended: `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh`) while providing standard Python `venv` fallback. |
| **GitHub CLI (gh)** | ❌ Missing | Not found in PATH. Can be installed via `brew install gh` or project will provide direct Git remote configuration instructions. |

---

## 3. Non-Negotiable Boundaries & Technical Guardrails

1. **Strict Fanless M5 Thermal Efficiency:**
   - No continuous background polling, zero heavy diffusion rendering (no multi-gigabyte Stable Video Diffusion or ComfyUI loops).
   - Execution duration budget: **1.5 to 3.0 minutes total per video run**.
   - Lightweight local inference: Quantized Ollama (`llama3.1:8b` or `llama3.2:3b`), CPU/Metal-accelerated TTS (Kokoro-82M or native macOS `say` fallback), and `faster-whisper` (base.en/tiny.en).
   - FFmpeg encoding uses single-pass `-preset fast -crf 22` or `h264_videotoolbox` hardware encoding to prevent thermal throttling.

2. **Manual Security & Credential Isolation:**
   - Absolutely zero hardcoded tokens, passwords, or bypasses.
   - All sensitive configs isolated in `.env` (strictly ignored by Git).
   - OAuth credential files isolated in `credentials/` directory (strictly ignored by Git).
   - `DRY_RUN=true` is the hardcoded default for all publisher scripts. Live publishing requires an explicit, deliberate flag (`DRY_RUN=false`).

3. **Autonomous Garbage Collection:**
   - Automated cleanup of intermediate audio segments, extracted frame caches, and temporary subtitles immediately post-render.
   - Preserves disk life on standard MacBook Air internal storage.

---

## 4. Phased Work Breakdown Structure (WBS)

### Phase 1: Planning, Environment & Architecture (Current Phase)
- [x] Host environment audit (`python3`, `ffmpeg`, `ollama`, `git`, `uv`, `gh`).
- [x] Create project workspace at `/Users/amrit/.gemini/antigravity/scratch/desi-reels-studio`.
- [x] Author comprehensive `docs/IMPLEMENTATION_PLAN.md`.
- [ ] Present summary in chat and obtain user gate approval.

### Phase 2: Strategic Blueprint (`docs/STRATEGY.md`)
- [ ] Draft **Content & Hook Strategy**:
  - 30-second pacing: exactly 75–85 words.
  - 5–6 timed scenes (4.5–5.5s per scene).
  - 3-second visual + verbal "pattern-interrupt" hook.
  - Three-pillar structure: Street Food Star -> Cultural Secret/History -> Practical Insider Tip.
  - Fact-grounding protocol to prevent AI culinary hallucinations.
- [ ] Draft **IST Posting Schedule & Performance Optimization Strategy**:
  - Weekday window: 18:30–21:00 IST (evening transit/leisure).
  - Weekend brunch window: 11:00–13:00 IST.
  - Sunday prime window: 19:30–21:30 IST.
  - SQLite metric learning algorithm (gradual reinforcement based on real engagement data).
- [ ] Draft **Self-Improvement & Reference Video Engine Strategy**:
  - Ingestion of user-provided reference reels into `reference_videos/`.
  - Cut-frequency and rhythm extraction via FFmpeg scene detection.
  - OCR/visual hook extraction via Ollama.
  - Human feedback translation into `memory/style_playbook.json`.
- [ ] Draft **MacBook Air Once-Daily Power Management**:
  - `launchd` calendar trigger vs sleep/wake strategies.
  - Auto-cleanup policies.
- [ ] Present strategy summary and obtain user gate approval.

### Phase 3: Core Pipeline & Local Media Engine
- [ ] **Task 3.1: Foundation & Storage Layer**
  - Scaffold folder structure: `src/`, `data/`, `memory/`, `assets/`, `output/`, `temp/`, `credentials/`.
  - Create `.gitignore`, `.env.example`, and `AGENTS.md`.
  - Implement SQLite database schema (`data/studio.db`):
    - `topics` table (status, tier, region, category, ground_truth_sources).
    - `videos` table (script, audio_path, video_path, render_duration_s, status).
    - `publishing_log` table (platform, post_id, post_url, scheduled_for_ist, published_at_ist, status).
    - `performance_metrics` table (views, likes, comments, shares, retention_pct, logged_at).
    - `feedback_log` table (rating, notes, applied_rules).
  - Setup Python virtual environment & dependencies (`requirements.txt` / `pyproject.toml`).
- [ ] **Task 3.2: Grounded Research & Scene Planner**
  - Create seed catalog of 25+ curated Indian street food and cultural topics across Northern, Southern, Western, Eastern, and Central India (`data/topics_seed.json`).
  - Implement `src/research.py`: Wikipedia / Wikivoyage API extractor for verified culinary history, ingredient facts, and local vendor locations.
  - Implement `src/planner.py`: Local Ollama integration reading `memory/style_playbook.json` with strict Pydantic JSON schema output:
    - 30-second voiceover narration (75–85 words).
    - 5–6 scene breakdown with exact timestamps, visual search keywords, on-screen text overlays, and sound cues.
    - Title, platform-tailored descriptions, and SEO hashtags.
- [ ] **Task 3.3: Audio-Driven Media Builder & Renderer**
  - Implement `src/audio_engine.py`:
    - Fast local TTS using Kokoro-TTS (or lightweight Piper/macOS `say` fallback with high-quality Indian English / natural tone).
    - Alignment engine using `faster-whisper` to generate word-level timestamped `.ass` subtitles with bold styling, animated highlights, and vertical safe-zone positioning.
  - Implement `src/visual_engine.py`:
    - Visual asset resolver: local asset library, Wikimedia Commons, and free stock video/image APIs (Pexels API with graceful fallback to high-resolution Ken Burns photo-motion).
    - FFmpeg motion filters: smooth pan/zoom (`zoompan`), dynamic cross-fades, and framing adjusted to 1080x1920 (9:16).
  - Implement `src/media_builder.py`:
    - Master compositing engine assembling Audio + Subtitles + Dynamic Motion Clips + Optional Background Ambience (royalty-free Indian street sounds at -24dB).
    - Video output: `1080x1920`, 30 FPS, H.264/AAC, target bitrate 3500–4500 kbps, faststart enabled.
    - Dry-run verification test producing `output/test_sample.mp4`.

### Phase 4: Self-Improvement Learner, Review Dashboard & Scheduler
- [ ] **Task 4.1: Reference Video Learner & Memory Loop**
  - Implement `src/learner.py`:
    - Scan `reference_videos/*.mp4` for cut-rate analysis (`ffmpeg -filter:v "select='gt(scene,0.3)',metadata=print"`).
    - Extract hook frames and analyze hook density and subtitle styles.
    - Parse human feedback from `data/studio.db` into updated weights in `memory/style_playbook.json`.
- [ ] **Task 4.2: Local Review & Operations Dashboard**
  - Implement `src/dashboard.py` (FastAPI/Streamlit or lightweight zero-dependency Python `http.server` with modern HTML5/JS UI on `http://localhost:8500`):
    - Video player to review the day's rendered short.
    - Quick "Approve for Publishing" or "Reject / Regenerate" actions.
    - Natural language feedback input ("Hook was too slow", "Increase subtitle font size").
    - Topic queue viewer and manual topic submitter.
    - Post metrics entry & historical analytics.
- [ ] **Task 4.3: macOS Once-Daily Automation**
  - Create `scripts/daily_run.sh` orchestrating: Research -> Plan -> Render -> Stage for Review or Auto-Publish based on config.
  - Create `install_schedule.sh` generating and loading macOS user LaunchAgent plist (`~/Library/LaunchAgents/com.desireels.studio.plist`).
  - Create `scripts/cleanup.sh` to purge intermediate temp files and keep disk footprint minimal.

### Phase 5: Multi-Platform Publishing System
- [ ] **Task 5.1: Publisher Architecture & Dry-Run Safety**
  - Implement `src/publisher.py` with unified interface and strict safety defaults (`DRY_RUN=true`).
- [ ] **Task 5.2: YouTube Shorts Integration**
  - Google OAuth2 token manager (`credentials/youtube_token.json`).
  - Resumable video upload with title, description, `#Shorts`, category 24/19 (Travel/Entertainment), and privacy status (`private` or `public`).
- [ ] **Task 5.3: Instagram Reels Integration**
  - Meta Graph API client for Instagram Professional/Creator account.
  - Resumable video container upload via `rupload.facebook.com/ig-api-upload`.
  - Status polling loop and publish trigger.
- [ ] **Task 5.4: Facebook Reels Integration**
  - Meta Graph API client for Facebook Page.
  - 3-step Reels upload protocol: start reel session, upload binary chunks to `rupload.facebook.com`, finalize publish.
- [ ] **Task 5.5: Setup & Credential Guide**
  - Document step-by-step developer account setup, scopes, and app creation in `docs/SETUP_GUIDE.md`.

### Phase 6: Documentation, Git Hygiene & GitHub Repository
- [ ] Compile comprehensive documentation:
  - `README.md` (System overview, visual architecture, quickstart, daily 2-minute workflow).
  - `docs/STRATEGY.md` (Content, pacing, hooks, IST scheduling, self-learning).
  - `docs/SETUP_GUIDE.md` (YouTube, Instagram, Facebook API credentials and token setups).
  - `docs/RUNBOOK.md` (Day-to-day operation, troubleshooting, launchd maintenance).
  - `AGENTS.md` (System conventions for future AI sessions).
- [ ] Git initialization, `.gitignore` validation, clean commit tree.
- [ ] GitHub repository setup (`gh repo create` or manual remote instructions) and push to `main`.

---

## 5. Directory & File Storage Layout

```
desi-reels-studio/
├── .env.example                 <- Sample environment variables (never contains secrets)
├── .gitignore                   <- Comprehensive ignore (venv, .env, credentials, outputs, temp)
├── AGENTS.md                    <- Rules & architecture for AI assistants
├── README.md                    <- Public repository guide & architecture
├── requirements.txt             <- Python dependencies
├── pyproject.toml               <- Project configuration
├── docs/
│   ├── IMPLEMENTATION_PLAN.md   <- This document
│   ├── STRATEGY.md              <- Content, timing, and learning strategy
│   ├── SETUP_GUIDE.md           <- Step-by-step API & OAuth configuration
│   └── RUNBOOK.md               <- Daily operations and troubleshooting
├── data/
│   ├── studio.db                <- SQLite database (topics, renders, publish log, feedback)
│   └── topics_seed.json         <- 25+ rich Indian travel, culture, street-food topics
├── memory/
│   ├── style_playbook.json      <- Dynamic AI style, hook guidelines, and pacing rules
│   └── feedback_history.json    <- Chronological human feedback learnings
├── credentials/                 <- Local OAuth token directory (strictly .gitignored)
├── reference_videos/            <- Drop viral .mp4 reels here for automatic style extraction
├── assets/
│   ├── audio/                   <- Royalty-free background street ambience / sitar loops
│   ├── fonts/                   <- Open-source display fonts (Montserrat, Oswald, Poppins)
│   └── visuals/                 <- High-resolution local B-roll / fallback images
├── temp/                        <- Intermediate audio, subtitle, and frame cache (cleaned daily)
├── output/                      <- Rendered 1080x1920 MP4 files (staged for review/publish)
├── scripts/
│   ├── daily_run.sh             <- Master daily runner triggered by launchd
│   ├── install_schedule.sh      <- Installs and activates launchd plist
│   └── cleanup.sh               <- Garbage collector for temp files
└── src/
    ├── __init__.py
    ├── config.py                <- Typed configuration & environment loading
    ├── db.py                    <- SQLite database access layer
    ├── research.py              <- Factual topic enrichment (Wikipedia/Wikivoyage)
    ├── planner.py               <- Script & scene planner via local Ollama
    ├── audio_engine.py          <- TTS generation & Whisper subtitle alignment
    ├── visual_engine.py         <- Media retrieval & FFmpeg zoompan/motion effects
    ├── media_builder.py         <- Final compositing pipeline (1080x1920 MP4)
    ├── learner.py               <- Reference video & feedback analysis engine
    ├── dashboard.py             <- Lightweight local web review UI (:8500)
    └── publisher.py             <- Multi-platform publisher (YT, IG, FB) with DRY_RUN
```

---

## 6. Verification Milestones & Phase Gates

| Gate | Milestone | Acceptance Criteria |
| :--- | :--- | :--- |
| **Gate 1** | **Implementation Plan** | Plan is reviewed, environment audited, and user approves roadmap. |
| **Gate 2** | **Strategy Document** | `docs/STRATEGY.md` approved covering content, hooks, IST scheduling, and learning. |
| **Gate 3** | **Core Media Pipeline** | Dry-run produces valid 30s `1080x1920` MP4 with clear audio, animated subtitles, and smooth transitions within 2 minutes. |
| **Gate 4** | **Learner & Dashboard** | Local dashboard loads at `:8500`, plays video, records feedback, and `learner.py` adapts playbook. |
| **Gate 5** | **Publisher & Credentials** | `DRY_RUN=true` validates payload formatting for YouTube, IG, FB; `SETUP_GUIDE.md` completed. |
| **Gate 6** | **Final Polish & Git** | All docs clean, Git repo committed, pushed to GitHub remote with clean branch state. |
