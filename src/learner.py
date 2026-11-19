"""Self-improvement engine: reference video cut analyzer and natural-language feedback learner."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import config, MEMORY_DIR, REFERENCE_VIDEOS_DIR
from src.db import db

logger = logging.getLogger("desi_reels.learner")
IST = timezone(timedelta(hours=5, minutes=30))


class LearnerEngine:
    """Extracts pacing metrics from viral reference videos and adapts the style playbook from human feedback."""

    def __init__(self) -> None:
        self.playbook_file = MEMORY_DIR / "style_playbook.json"
        self.history_file = MEMORY_DIR / "feedback_history.json"
        self.ref_dir = REFERENCE_VIDEOS_DIR

    def load_playbook(self) -> Dict[str, Any]:
        if self.playbook_file.is_file():
            try:
                with open(self.playbook_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading playbook: {e}")
        return {}

    def save_playbook(self, playbook: Dict[str, Any]) -> None:
        playbook["last_updated"] = datetime.now(IST).isoformat()
        with open(self.playbook_file, "w", encoding="utf-8") as f:
            json.dump(playbook, f, indent=2)
        logger.info(f"Updated playbook saved to {self.playbook_file}")

    # --------------------------------------------------------------------------
    # 1. Reference Video Cut & Rhythm Analyzer
    # --------------------------------------------------------------------------
    def analyze_reference_videos(self) -> Dict[str, Any]:
        """Analyze all .mp4 videos in reference_videos/ for cut rhythm and shot lengths."""
        mp4_files = list(self.ref_dir.glob("*.mp4"))
        if not mp4_files:
            return {
                "status": "empty",
                "message": "No reference videos found in reference_videos/. Drop .mp4 reels there to analyze.",
                "videos_analyzed": 0,
            }

        video_stats = []
        for vid in mp4_files:
            stats = self._analyze_single_video(vid)
            if stats:
                video_stats.append(stats)

        if not video_stats:
            return {"status": "error", "message": "Could not extract cut data from reference videos."}

        avg_shot_durations = [v["avg_shot_duration"] for v in video_stats if v.get("avg_shot_duration")]
        overall_avg_cut = sum(avg_shot_durations) / len(avg_shot_durations) if avg_shot_durations else 4.5
        first_cuts = [v["first_cut_seconds"] for v in video_stats if v.get("first_cut_seconds")]
        overall_first_cut = sum(first_cuts) / len(first_cuts) if first_cuts else 2.5

        # Adapt playbook with reference metrics
        playbook = self.load_playbook()
        old_scene_dur = playbook.get("pacing", {}).get("average_scene_duration_seconds", 5.0)

        # Smooth transition towards reference video pacing (50% blend)
        new_scene_dur = round((old_scene_dur + overall_avg_cut) / 2.0, 2)
        playbook["pacing"]["average_scene_duration_seconds"] = max(2.5, min(6.0, new_scene_dur))
        playbook["pacing"]["target_scenes"] = max(5, min(8, int(round(30.0 / new_scene_dur))))
        playbook["hooks"]["max_hook_duration_seconds"] = max(2.0, min(3.5, round(overall_first_cut, 1)))

        self.save_playbook(playbook)

        return {
            "status": "success",
            "videos_analyzed": len(video_stats),
            "reference_average_cut_seconds": round(overall_avg_cut, 2),
            "reference_first_cut_seconds": round(overall_first_cut, 2),
            "updated_playbook_scene_duration": new_scene_dur,
            "updated_target_scenes": playbook["pacing"]["target_scenes"],
        }

    def _analyze_single_video(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """Run FFmpeg scene filter to detect cut timestamps."""
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-filter:v",
            "select='gt(scene,0.28)',metadata=print",
            "-f",
            "null",
            "-",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            pts_matches = re.findall(r"pts_time:([0-9\.]+)", res.stderr)
            cut_times = [float(t) for t in pts_matches]

            # Get video total duration
            dur_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]
            dur_res = subprocess.run(dur_cmd, capture_output=True, text=True)
            total_dur = float(dur_res.stdout.strip()) if dur_res.stdout.strip() else 30.0

            if not cut_times:
                return {"file": video_path.name, "cuts": 0, "avg_shot_duration": total_dur, "first_cut_seconds": 3.0}

            # Calculate shot intervals
            intervals = []
            prev_t = 0.0
            for t in cut_times:
                intervals.append(t - prev_t)
                prev_t = t
            intervals.append(max(0.5, total_dur - prev_t))

            return {
                "file": video_path.name,
                "duration": total_dur,
                "cuts": len(cut_times),
                "first_cut_seconds": cut_times[0],
                "avg_shot_duration": sum(intervals) / len(intervals),
            }
        except Exception as e:
            logger.warning(f"Could not analyze video {video_path}: {e}")
            return None

    # --------------------------------------------------------------------------
    # 2. Human Feedback to Style Playbook Adaptation Loop
    # --------------------------------------------------------------------------
    def apply_human_feedback(
        self, rating: int, critique: str, video_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Convert natural language feedback into structured playbook updates."""
        playbook = self.load_playbook()
        critique_lower = critique.lower()
        applied_changes: Dict[str, Any] = {}

        # 1. Pacing & Speech Rate adjustments
        if re.search(r"\b(too fast|talking.*fast|slow down|rushed)\b", critique_lower):
            old_wpm = playbook.get("pacing", {}).get("target_wpm", 160)
            new_wpm = max(140, old_wpm - 8)
            playbook["pacing"]["target_wpm"] = new_wpm
            applied_changes["target_wpm"] = f"{old_wpm} -> {new_wpm}"

        if re.search(r"\b(too slow|talking.*slow|speed up|sluggish)\b", critique_lower):
            old_wpm = playbook.get("pacing", {}).get("target_wpm", 160)
            new_wpm = min(180, old_wpm + 8)
            playbook["pacing"]["target_wpm"] = new_wpm
            applied_changes["target_wpm"] = f"{old_wpm} -> {new_wpm}"

        # 2. Subtitle Positioning & Font Size
        if re.search(r"\b(subtitles?.*(?:low|bottom|ui)|instagram ui|blocked)\b", critique_lower):
            old_margin = playbook.get("subtitles", {}).get("margin_v", 240)
            new_margin = min(360, old_margin + 30)
            playbook["subtitles"]["margin_v"] = new_margin
            applied_changes["subtitle_margin_v"] = f"{old_margin} -> {new_margin}px"

        if re.search(r"\b(subtitles?.*(?:high|top))\b", critique_lower):
            old_margin = playbook.get("subtitles", {}).get("margin_v", 240)
            new_margin = max(180, old_margin - 30)
            playbook["subtitles"]["margin_v"] = new_margin
            applied_changes["subtitle_margin_v"] = f"{old_margin} -> {new_margin}px"

        if re.search(r"\b(font.*small|bigger subtitles?|larger (?:text|font|subtitles?))\b", critique_lower):
            old_size = playbook.get("subtitles", {}).get("font_size", 72)
            new_size = min(96, old_size + 6)
            playbook["subtitles"]["font_size"] = new_size
            applied_changes["subtitle_font_size"] = f"{old_size} -> {new_size}pt"

        # 3. Hook Style Weighting
        if re.search(r"\b(boring hook|hook.*(?:slow|weak|catchy|better)|stronger hook|more energy)\b", critique_lower):
            weights = playbook.get("hooks", {}).get("archetype_weights", {})
            weights["sensory_shock"] = min(0.60, round(weights.get("sensory_shock", 0.35) + 0.10, 2))
            weights["contrarian_question"] = min(0.40, round(weights.get("contrarian_question", 0.25) + 0.05, 2))
            playbook["hooks"]["archetype_weights"] = weights
            applied_changes["boosted_hook_archetypes"] = ["sensory_shock", "contrarian_question"]

        # 4. Visual Motion Intensity
        if re.search(r"\b(more motion|faster zoom|more dynamic|more energetic)\b", critique_lower):
            old_zoom = playbook.get("visual_style", {}).get("motion_zoom_speed", 0.002)
            new_zoom = min(0.0035, round(old_zoom + 0.0005, 4))
            playbook["visual_style"]["motion_zoom_speed"] = new_zoom
            applied_changes["motion_zoom_speed"] = f"{old_zoom} -> {new_zoom}"

        # If no explicit keyword matched, record note but maintain stable baseline
        if not applied_changes:
            applied_changes["note"] = "Critique recorded in history; baseline parameters retained."

        # Save updated playbook
        self.save_playbook(playbook)

        # Log to feedback history JSON
        history_entry = {
            "timestamp": datetime.now(IST).isoformat(),
            "video_id": video_id,
            "rating": rating,
            "critique": critique,
            "applied_changes": applied_changes,
        }
        self._append_to_history(history_entry)

        # Log to SQLite
        db.log_feedback(
            video_id=video_id,
            rating=rating,
            critique=critique,
            applied_playbook_changes=applied_changes,
        )

        return {
            "status": "success",
            "rating": rating,
            "critique": critique,
            "applied_changes": applied_changes,
        }

    def _append_to_history(self, entry: Dict[str, Any]) -> None:
        history = []
        if self.history_file.is_file():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        history.append(entry)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)


learner_engine = LearnerEngine()
