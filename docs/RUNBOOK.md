# DesiReels Studio — Daily Operations & Troubleshooting Runbook
**Daily Maintenance, Operational Cheatsheet, launchd Management & Incident Response**

---

## 1. The Daily 2-Minute Workflow

DesiReels Studio is built for autonomous once-daily execution. As the channel director, your daily check-in takes only 2 minutes:

```
                                DAILY 2-MINUTE CHECK-IN
                                
   18:00 IST                   18:05 IST                     18:07 IST
 [launchd Auto-Run] ----> [Open Dashboard] ----------> [Quick Review & Feedback]
  - Topic researched       - http://localhost:8500      - Watch 30s video in player
  - Script generated       - See today's render         - Rate 1-5 stars
  - 1080x1920 MP4 built                                 - Type plain-English critique
  - Staged for publish                                  - Click 'Submit' -> AI learns!
```

### Steps:
1. **Open the Review Dashboard:**
   Open your browser to [http://localhost:8500](http://localhost:8500).
2. **Watch the Daily Render:**
   Click play on the vertical video player in the left column. Listen to the voiceover pacing, inspect subtitle alignment, and verify visual transitions.
3. **Submit Your Review & Critique:**
   - Select a star rating (1 to 5).
   - Type a short critique in plain English (e.g., *"Talking slightly too fast in the middle"*, *"Subtitles look great"*, *"Hook was slow"*).
   - Click **Submit Feedback & Update AI Memory**.
   - `learner.py` automatically updates `memory/style_playbook.json` so tomorrow's video adapts to your preferences.
4. **Done!**
   If `DRY_RUN=false` is configured with credentials, the video publishes automatically to YouTube Shorts, Instagram Reels, and Facebook Reels.

---

## 2. Common Operations & Commands

All commands should be run from the project root:
```bash
cd /Users/amrit/.gemini/antigravity/scratch/desi-reels-studio
```

### 2.1 Starting the Review Dashboard
To run the dashboard manually at any time:
```bash
python3 -m src.dashboard
# Access at: http://localhost:8500
```

### 2.2 Triggering an Immediate Video Generation Run
To manually run the pipeline right now without waiting for the 18:00 IST schedule:

* **Dry-Run Mode (Safe, no publishing):**
  ```bash
  python3 -m src.orchestrator
  ```
* **Live Publishing Mode (Uploads to configured platforms):**
  ```bash
  python3 -m src.orchestrator --live
  ```

### 2.3 Running the Full Automated Regression Test Suite
Verify that all 8 architectural modules and constraints pass:
```bash
python3 -m unittest -v tests/test_pipeline.py
```

### 2.4 Analyzing Reference Videos (`reference_videos/*.mp4`)
When you discover viral Indian street food or travel reels:
1. Drop the `.mp4` files into the `reference_videos/` folder.
2. Trigger the learner:
   ```bash
   python3 -c "from src.learner import learner_engine; res = learner_engine.analyze_reference_videos(); print(res)"
   ```
   *(Or click the "Analyze Reference Videos" button in the dashboard).*
3. The engine measures cut frequency, shot lengths, and hook timing, updating `memory/style_playbook.json`.

### 2.5 Adding New Custom Topics
You can add custom topics via the dashboard UI or programmatically via Python:
```python
from src.db import db
db.insert_topic(
    title="Bengaluru Vidyarthi Bhavan Masala Dosa",
    region="South India (Bengaluru, Karnataka)",
    category="street_food",
    ground_truth_summary="Opened in 1943 in Gandhi Bazaar. Famous for thick, golden, crispy butter dosas served with fresh coconut chutney."
)
```

---

## 3. macOS `launchd` Scheduler Management

The scheduler runs once daily at **18:00 IST** (6:00 PM IST) via a native macOS LaunchAgent (`com.desireels.studio`).

### 3.1 Install or Reload the Schedule
```bash
./scripts/install_schedule.sh
launchctl unload ~/Library/LaunchAgents/com.desireels.studio.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.desireels.studio.plist
```

### 3.2 Check if the Schedule is Loaded
```bash
launchctl list | grep com.desireels.studio
```
*(If loaded, you will see a status line showing PID or `0`).*

### 3.3 Force an Immediate Trigger via `launchd`
```bash
launchctl start com.desireels.studio
```

### 3.4 Unload / Disable the Schedule
```bash
launchctl unload ~/Library/LaunchAgents/com.desireels.studio.plist
```

---

## 4. Log Inspection & Monitoring

All automated runs write to persistent logs in `logs/`:

| Log File | Purpose | Viewing Command |
| :--- | :--- | :--- |
| `logs/daily_run.log` | Master pipeline execution output & timestamps | `tail -f logs/daily_run.log` |
| `logs/launchd_stdout.log` | Standard output captured by macOS `launchd` | `tail -f logs/launchd_stdout.log` |
| `logs/launchd_stderr.log` | Standard errors captured by macOS `launchd` | `tail -f logs/launchd_stderr.log` |

---

## 5. Troubleshooting & Incident Recovery

### Issue 1: "Could not connect to Ollama instance"
* **Symptom:** `dial tcp 127.0.0.1:11434: connect: operation not permitted` or connection refused.
* **Diagnosis:** The local Ollama daemon is not running.
* **Resolution:**
  1. Open the **Ollama** application from your macOS Applications folder (or menu bar).
  2. Or start the daemon in a terminal window:
     ```bash
     ollama serve
     ```
  3. Verify the model is present:
     ```bash
     ollama list
     ```
  *Note:* The pipeline contains an automated, fact-grounded fallback generator that activates if Ollama is unreachable, ensuring your daily video never fails to render.

### Issue 2: "Video rendered without subtitles or font missing"
* **Diagnosis:** Missing system fonts for `.ass` subtitle rendering.
* **Resolution:**
  1. The pipeline defaults to `Arial Black` / `Montserrat-Bold`, which are universally available on macOS.
  2. If custom fonts are desired, place them into `assets/fonts/`.
  3. Run `python3 -m unittest -v tests/test_pipeline.py` to verify subtitle compilation.

### Issue 3: "Disk space warning on internal SSD"
* **Diagnosis:** Old rendered videos or intermediate frame caches accumulating.
* **Resolution:**
  1. Run the garbage collection script:
     ```bash
     ./scripts/cleanup.sh
     ```
  2. Check the size of `output/`:
     ```bash
     du -sh output/
     ```
  3. Keep the rendered MP4s you want to archive, or move them to external storage.

### Issue 4: "YouTube OAuth Token Expired or Revoked"
* **Symptom:** `google.auth.exceptions.RefreshError` during live upload.
* **Resolution:**
  Re-run the interactive authentication script:
  ```bash
  python3 scripts/auth_youtube.py
  ```
  Follow the on-screen browser prompt to sign in and generate a fresh `credentials/youtube_token.json`.

### Issue 5: "Instagram or Facebook Graph API Error: (#100) Invalid Token"
* **Symptom:** Meta Graph API returns HTTP 400 with an OAuthException.
* **Resolution:**
  1. Check token validity via the [Meta Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/).
  2. Generate a fresh 60-day long-lived token following [SETUP_GUIDE.md](file:///Users/amrit/.gemini/antigravity/scratch/desi-reels-studio/docs/SETUP_GUIDE.md).
  3. Update `INSTAGRAM_ACCESS_TOKEN` or `FACEBOOK_PAGE_ACCESS_TOKEN` in `.env`.
