#!/usr/bin/env python3
"""Export full Antigravity conversation transcript to Markdown for project documentation."""

import json
from pathlib import Path

TRANSCRIPT_PATH = Path(
    "/Users/amrit/.gemini/antigravity/brain/2b41883c-3075-4ca5-a17f-cc4ac40e985a/.system_generated/logs/transcript.jsonl"
)
OUTPUT_MD_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "SESSION_TRANSCRIPT.md"
)


def export_transcript() -> None:
    header = """# DesiReels Studio — Session Architectural Transcript & Context Memory
**Conversation ID:** `2b41883c-3075-4ca5-a17f-cc4ac40e985a`  
**Date:** November 19, 2026 | **Target Hardware:** MacBook Air M5 (Apple Silicon)  
**System:** Autonomous Indian Short-Video Creation, Self-Learning & Multi-Platform Publishing Engine  

> [!NOTE]
> This document preserves the complete chronological interaction, architectural discussions, phase gate approvals, test verifications, and engineering decisions between the User and the Senior AI Architect. Future Antigravity sessions can ingest this file to seamlessly continue development without losing context.

---

## Table of Contents
1. [Chronological Dialogue Log](#1-chronological-dialogue-log)
2. [Architectural Decisions & Rationale Log](#2-architectural-decisions--rationale-log)
3. [Future Roadmap & Next Milestones](#3-future-roadmap--next-milestones)

---

## 1. Chronological Dialogue Log
"""

    turns_md = []
    turn_count = 1

    if not TRANSCRIPT_PATH.is_file():
        print(f"Transcript not found at {TRANSCRIPT_PATH}")
        return

    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            src = data.get("source")
            stype = data.get("type")
            content = data.get("content")
            if not content:
                continue

            if stype == "USER_INPUT" and src == "USER_EXPLICIT":
                clean_content = (
                    content.replace("<USER_REQUEST>", "")
                    .replace("</USER_REQUEST>", "")
                    .strip()
                )
                turns_md.append(
                    f"### Turn {turn_count}: User Prompt\n\n```text\n{clean_content}\n```\n"
                )
                turn_count += 1
            elif stype == "PLANNER_RESPONSE" and src == "MODEL":
                turns_md.append(
                    f"### Turn {turn_count}: Assistant Architecture Response\n\n{content.strip()}\n\n---\n"
                )
                turn_count += 1

    footer = """
---

## 2. Architectural Decisions & Rationale Log

| Decision Area | Choice Made | Architectural Rationale |
| :--- | :--- | :--- |
| **Pacing & Word Count** | Exactly 75–85 words across 28–30s | At 2.6–2.8 words/second, this speech cadence maximizes completion rate on YouTube Shorts and Instagram Reels without feeling rushed. |
| **Subtitle Strategy** | Dual-layer: styled `.ass` + embedded `.mov_text` + burned scene badges | Ensures subtitles are universally readable across all player types and prevents dependency failures on Homebrew FFmpeg builds lacking `libass`. |
| **Database Architecture** | Local SQLite (`data/studio.db`) | Zero network overhead, ACID transactions, simple foreign keys, fast indexing, and zero daemon load on MacBook Air. |
| **Fanless M5 Optimization** | Single-pass hardware encoding + LaunchAgent triggers | Runs once daily for < 5 seconds of compute. No 24/7 background daemons to drain battery. |
| **Security Boundary** | `DRY_RUN=true` default + strict gitignore | Prevents accidental live publishing and ensures zero credentials touch Git. |
| **Self-Learning Loop** | Cut-frequency detection + natural-language regex/playbook deltas | Quantitative metrics from viral videos blend with qualitative human critique to adapt `style_playbook.json`. |

---

## 3. Future Roadmap & Next Milestones

1. **Enhanced Multilingual Voices:**
   - Expand local TTS voices to regional Indian languages (Hindi, Tamil, Telugu, Bengali) using Piper or Kokoro models once native Apple Silicon wheels release.
2. **Automated B-Roll Ingestion:**
   - Integrate automated Wikimedia Commons and Pexels HD video downloader for royalty-free Indian bazaar footage matching topic search queries.
3. **Engagement Analytics Synchronizer:**
   - Build a daily cron job to pull 24-hour view counts, like ratios, and top comments via YouTube Data API and Meta Graph API to dynamically train posting time optimization in SQLite.
4. **Interactive Comment Reply Generator:**
   - Use local Ollama to draft authentic, engaging responses to top viewer comments on published reels.
"""

    full_text = header + "\n" + "\n".join(turns_md) + "\n" + footer
    OUTPUT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"✅ Generated {OUTPUT_MD_PATH} ({len(full_text)} bytes, {turn_count-1} turns)")


if __name__ == "__main__":
    export_transcript()
