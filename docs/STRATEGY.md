# DesiReels Studio — Strategic Blueprint
**Product, Content, Growth, Timing & Self-Improvement Strategy for Indian Travel, Culture & Street-Food Shorts**

---

## 1. Executive Summary & Brand Positioning

**DesiReels Studio** is designed to produce compelling, highly authentic, 30-second vertical videos (9:16) capturing the sensory vibrancy, rich heritage, and culinary magic of India. 

### Core Channel Tenets
1. **Sensory-First Storytelling:** Evoke sight, sound, and aroma within the first 3 seconds (sizzling tawas, clay kulhads, boiling chai, colorful spice heaps).
2. **Hyper-Local Authenticity:** Ground every story in genuine historical fact, specific named bazaars, and local cultural context (e.g., Khari Baoli, Lucknow's Chowk, Madurai's Meenakshi street food corridors).
3. **High-Velocity Retention:** Every microsecond counts. No dead air, no generic AI fluff, no slow preamble.
4. **Lightweight, Zero-Maintenance Architecture:** Engineered to run on a fanless MacBook Air M5 in under 3 minutes per day, with zero battery drain when idle.

---

## 2. Content & Hook Strategy

### 2.1 The 30-Second Constraint & Timing Architecture
Attention spans on YouTube Shorts, Instagram Reels, and Facebook Reels demand ruthless economy of words:
- **Duration Budget:** Exactly 28.0 to 30.0 seconds.
- **Narration Word Count:** **75 to 85 words** (delivered at ~2.6–2.8 words/second).
- **Scene Breakdown:** **5 to 6 distinct visual cuts** (average cut length: 4.5 to 5.5 seconds).

```
 0s                  3s                       14s                      23s              30s
 +-------------------+------------------------+------------------------+------------------+
 |   THE HOOK        |   STREET FOOD STAR     |   CULTURAL LORE        |  INSIDER TIP/CTA |
 |   Pattern         |   The dish, technique, |   The history, secret, |  Exact location, |
 |   Interrupt       |   aroma, and craft     |   or royal origin      |  price, callout  |
 |   (1 Scene)       |   (2 Scenes)           |   (2 Scenes)           |  (1 Scene)       |
 +-------------------+------------------------+------------------------+------------------+
```

### 2.2 The 4 Hook Archetypes (0.0s – 3.0s)
The first 3 seconds decide whether the viewer scrolls away or watches to completion. Every script rotates through four proven hook archetypes defined in `memory/style_playbook.json`:

| Hook Archetype | Formula & Objective | Real World Example |
| :--- | :--- | :--- |
| **The Sensory Shock** | Bold statement paired with vivid sound/visual imagery. | *"This 100-year-old Lucknow tawa has cooked over 10 million kebabs!"* |
| **The Contrarian Question** | Challenges common assumptions or sparks debate. | *"Think you know Indian butter? This Delhi street foam disappears on your tongue in 2 seconds."* |
| **The Secret Royalty / History** | Ties a humble street snack to ancient kings or empires. | *"The Mughal secret behind this ₹40 dessert took 8 hours of winter dew to make."* |
| **The Hyper-Local Superlative** | Highlights an extreme, unique craft or intense crowd. | *"India’s most dangerous street tea is poured from 6 feet in the air!"* |

### 2.3 The Three-Pillar Content Formula
After the 3-second hook, every short follows a rigorous structural rhythm:
1. **Pillar 1: The Street Food Star (Seconds 3–14)**
   - Introduce the dish with mouthwatering descriptors (texture, spice blend, cooking technique).
   - Highlight the vendor's craft (wood-fired clay ovens, hand-pounded spices, brass vessels).
2. **Pillar 2: Cultural Heritage & Lore (Seconds 14–23)**
   - Unpack the historical backstory (e.g., how Portuguese traders introduced the pav, or how 17th-century royal kitchens created Shahi Tukda).
   - Ground the viewer in cultural context rather than just food appreciation.
3. **Pillar 3: Insider Practical Tip & Engagement CTA (Seconds 23–30)**
   - Provide an actionable travel tip (exact lane, ideal visit time, fair price in ₹).
   - Single natural question prompting viewer comments (*"Would you dare try this 4-alarm spice level? Tell us in the comments!"*).

### 2.4 Guarding Against Hallucination & Generic AI Fluff
Generic AI scripts fail because they use clichés like *"India, the land of spices"* or *"Take a journey into flavors"*. 
- **The Grounding Rule:** Before generating a script, `research.py` queries Wikipedia / Wikivoyage APIs for the specific topic.
- **The Entity Validator:** Every script must contain at least:
  - 1 specific named geographic entity (e.g., *Aminabad, Old Delhi, Fort Kochi, Jodhpur Old City*).
  - 1 specific culinary term (e.g., *Dum pukht, Tandoor, Tadka, Chashni, Bhatura*).
  - 1 specific historical, vendor, or preparation metric (e.g., *slow-cooked for 12 hours, simmered on charcoal, 1928 origin*).

---

## 3. Indian Standard Time (IST) Posting & Reach Strategy

### 3.1 Peak Traffic Windows in India (IST)
Indian mobile users exhibit distinct short-form video consumption habits across workdays and weekends:

```
    WEEKDAYS (Mon - Thu)               WEEKENDS (Sat - Sun)
+---------------------------+       +---------------------------+
| 08:00 - 09:30  (Commute)  |       | 11:00 - 13:00  (Brunch)   |
| 13:00 - 14:00  (Lunch)    |       | 16:30 - 18:30  (Snack)    |
| 18:30 - 21:00  (PRIME PEAK|       | 19:30 - 21:30  (MEGA PEAK)|
+---------------------------+       +---------------------------+
```

#### Baseline Target Publishing Windows

| Day of Week | Primary Target Window (IST) | Rationale & Audience Mindset |
| :--- | :--- | :--- |
| **Monday – Thursday** | **19:00 – 20:30 IST** | Evening transit & post-dinner unwind. Highest smartphone engagement for food/travel entertainment. |
| **Friday** | **18:30 – 21:00 IST** | Transition into weekend mode. Viewers actively looking for weekend food/travel plans. |
| **Saturday** | **11:30 – 13:00 IST** *(Window A)*<br>**19:00 – 21:00 IST** *(Window B)* | Late brunch scrolling or evening leisure before heading out. |
| **Sunday** | **11:00 – 13:00 IST** *(Brunch)*<br>**19:30 – 21:30 IST** *(Prime)* | Highest gross weekly reach. Sunday evening generates the longest watch sessions. |

### 3.2 Performance Feedback & Dynamic Schedule Optimization
Rather than relying on static assumptions, `studio.db` stores performance metrics for every published video:
- Metrics tracked: `views_1h`, `views_24h`, `likes_24h`, `comments_24h`, `average_retention_pct`.
- **Epsilon-Greedy Scheduling Heuristic:**
  - 80% of scheduled runs target the historically top-performing 30-minute bucket for that specific day of the week.
  - 20% of scheduled runs explore adjacent 30-minute time slots (e.g., testing 18:15 IST vs 20:45 IST) to discover shifting audience peaks.

---

## 4. Self-Improvement & Reference-Video Learning Engine

The system improves with every single video through two distinct learning feedback loops:

```
                                  SELF-IMPROVEMENT LOOPS
                                  
   [ Reference Video Loop ]                                 [ Human Feedback Loop ]
   User drops viral .mp4 reels                             User reviews daily render
   into reference_videos/                                  in Dashboard (:8500)
              |                                                       |
              v                                                       v
   FFmpeg Scene Detection (Cut Frequency)                 Plain-English Critique
   Ollama Vision (Hook/Text/Visual Style)                  ("Hook too slow", "More spice focus")
              |                                                       |
              +---------------------------> + <-----------------------+
                                            |
                                            v
                                 memory/style_playbook.json
                                 - Target Cut Rhythm (e.g. 4.2s -> 3.6s)
                                 - Hook Weightings (Boost Sensory Shock)
                                 - Subtitle Font Size & Animation Rules
                                 - B-roll Motion Intensity
```

### 4.1 Reference Video Ingestion (`reference_videos/*.mp4`)
When you observe a viral Indian travel or street food reel on Instagram or YouTube, simply drop the `.mp4` into `reference_videos/`. During analysis:
1. **Rhythm & Pacing Profiler:** FFmpeg's `scene` filter detects cut timestamps. It calculates the average shot length, the standard deviation of shot changes, and whether the first cut occurs in under 2.5 seconds.
2. **Visual & Text Density Analysis:** Keyframes from seconds 1, 2, and 3 are sampled and evaluated by local Ollama to measure title text bounding boxes, font placement (safe zones), and visual saturation.
3. **Rhythm Transfer:** The learned timing metrics directly update `style_playbook.json`'s target scene duration profiles.

### 4.2 Human Feedback Loop
When viewing the rendered video in the local dashboard (`http://localhost:8500`), you can type natural English feedback:
- *Example 1:* *"The voiceover was too fast in the middle section."*  
  $\rightarrow$ `learner.py` decreases the target word-per-minute rate in `style_playbook.json` by 5%.
- *Example 2:* *"The subtitles are blocked by the platform description on Instagram."*  
  $\rightarrow$ `learner.py` adjusts the bottom margin parameter in the `.ass` subtitle generator up by 40 pixels.
- *Example 3:* *"Use more vibrant colors and faster zoom on food closeups."*  
  $\rightarrow$ `learner.py` increases FFmpeg `zoompan` scale increments from `0.0015` to `0.0025`.

---

## 5. MacBook Air M5 Fanless Thermal & Power Strategy

The MacBook Air M5 is a powerful fanless laptop. Sustained heavy rendering or 24/7 background daemons will drain battery and cause passive thermal throttling. Our architecture guarantees optimal efficiency:

```
                                 DAILY RUN TIMELINE (~2.5 MIN TOTAL)
                                 
  [launchd trigger]
   45m before post
          |
          v
   +--------------+      +--------------+      +----------------+      +--------------+
   | Factual Wiki | ---> | Ollama Scene | ---> | TTS + Whisper  | ---> | FFmpeg M5    | ---> [Clean Exit]
   | Research     |      | Scripting    |      | Subtitles      |      | Render       |      Temp Purged
   | (2-5s)       |      | (15-30s)     |      | (20-40s)       |      | (30-60s)     |      (0% CPU Idle)
   +--------------+      +--------------+      +----------------+      +--------------+
```

### Thermal & Resource Rules
1. **Zero 24/7 Background Daemons:** The pipeline uses native macOS `launchd` Calendar intervals. Between runs, zero Python or Node processes run in the background.
2. **Hardware Accelerated Encoding:** Video encoding leverages FFmpeg with Apple Silicon VideoToolbox (`h264_videotoolbox`) or single-pass `libx264 -preset fast -crf 22`, maintaining low CPU temperatures.
3. **Automatic Cache Purging:** Temporary `.wav` voice slices, `.png` frames, and intermediate `.ass` subtitles in `temp/` are immediately removed post-render, keeping disk write cycles minimal.
4. **Sleep & Wake Awareness:** If the MacBook Air is asleep when `launchd` fires, macOS runs the job immediately upon system wake, ensuring no daily video is skipped.

---

## 6. Metrics & Success Criteria

| Milestone | Target Indicator |
| :--- | :--- |
| **Render Speed** | Complete 30s video assembled in **< 150 seconds** on M5. |
| **File Quality & Size** | 1080x1920 (9:16), 30 fps, crisp audio, faststart enabled, **8–15 MB**. |
| **Viewer Retention** | Average watch percentage **> 75%** on 30s format. |
| **Engagement** | Comment rate **> 2.5%** driven by natural conversational end-hooks. |
| **Self-Improvement** | Style playbook converges on user-preferred pacing within 5 feedback cycles. |
