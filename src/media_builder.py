"""Master compositing engine: synthesizes audio, renders scene motion, burns subtitles, and outputs 1080x1920 MP4."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.audio_engine import audio_engine
from src.config import config, OUTPUT_DIR, TEMP_DIR
from src.db import db
from src.visual_engine import visual_engine

logger = logging.getLogger("desi_reels.media_builder")


class MediaBuilder:
    """Orchestrates end-to-end 30-second short video rendering."""

    def __init__(self) -> None:
        self.temp_dir = TEMP_DIR
        self.output_dir = OUTPUT_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._has_ass_filter = self._check_ass_filter()

    def _check_ass_filter(self) -> bool:
        """Check if ffmpeg build has libass/ass filter support."""
        try:
            res = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True)
            return " ass " in res.stdout or " subtitles " in res.stdout
        except Exception:
            return False

    def build_video(self, topic: Dict[str, Any], plan: Dict[str, Any]) -> Path:
        """Render complete 1080x1920 vertical video from topic and script plan."""
        start_time = time.time()
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^\w\-]", "_", plan["title"][:30]).lower()
        output_mp4 = self.output_dir / f"{timestamp_str}_{slug}.mp4"

        logger.info(f"--- Starting Render for: {plan['title']} ---")

        # 1. Synthesize Audio
        voice_wav = self.temp_dir / f"voice_{timestamp_str}.wav"
        audio_duration = audio_engine.synthesize(plan["narration"], voice_wav)
        logger.info(f"1. Voiceover synthesized: {audio_duration:.2f} seconds")

        # 2. Generate Word-Aligned Subtitles (.ass & .srt)
        subtitles_ass = self.temp_dir / f"subtitles_{timestamp_str}.ass"
        subtitles_srt = self.temp_dir / f"subtitles_{timestamp_str}.srt"

        audio_engine.generate_ass_subtitles(
            text=plan["narration"],
            total_duration=audio_duration,
            output_ass=subtitles_ass,
            scenes=plan["scenes"],
        )
        audio_engine.generate_srt_subtitles(
            text=plan["narration"],
            total_duration=audio_duration,
            output_srt=subtitles_srt,
        )
        logger.info("2. Styled subtitles (.ass and .srt) prepared")

        # 3. Render Visual Scenes with Alternating Motion
        scenes = plan.get("scenes", [])
        num_scenes = len(scenes)
        scene_duration = audio_duration / max(1, num_scenes)

        rendered_clips: List[Path] = []
        for idx, sc in enumerate(scenes):
            scene_asset = visual_engine.resolve_scene_visual(sc, plan["title"], idx)
            clip_path = self.temp_dir / f"scene_{idx}_{timestamp_str}.mp4"
            direction = "in" if idx % 2 == 0 else "pan"

            visual_engine.render_scene_clip(
                image_path=scene_asset,
                duration=scene_duration,
                output_mp4=clip_path,
                zoom_direction=direction,
            )
            rendered_clips.append(clip_path)

        logger.info(f"3. Rendered {len(rendered_clips)} motion scene clips")

        # 4. Concatenate Scene Clips
        concat_txt = self.temp_dir / f"concat_{timestamp_str}.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for clip in rendered_clips:
                f.write(f"file '{clip.resolve()}'\n")

        concatenated_video = self.temp_dir / f"visual_track_{timestamp_str}.mp4"
        cmd_concat = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-c",
            "copy",
            str(concatenated_video),
        ]
        subprocess.run(cmd_concat, capture_output=True, check=True)

        # 5. Master Composite: Audio + Video + Subtitles -> 1080x1920 MP4
        logger.info("4. Assembling master vertical composite...")

        if self._has_ass_filter:
            sub_escaped = str(subtitles_ass.resolve()).replace(":", "\\:").replace("'", "\\'")
            cmd_master = [
                "ffmpeg",
                "-y",
                "-i",
                str(concatenated_video),
                "-i",
                str(voice_wav),
                "-vf",
                f"ass='{sub_escaped}'",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "22",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ar",
                "44100",
                "-shortest",
                "-movflags",
                "+faststart",
                str(output_mp4),
            ]
        else:
            # High-performance pipeline with embedded mov_text subtitles track
            cmd_master = [
                "ffmpeg",
                "-y",
                "-i",
                str(concatenated_video),
                "-i",
                str(voice_wav),
                "-i",
                str(subtitles_srt),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "22",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ar",
                "44100",
                "-c:s",
                "mov_text",
                "-metadata:s:s:0",
                "language=eng",
                "-shortest",
                "-movflags",
                "+faststart",
                str(output_mp4),
            ]

        subprocess.run(cmd_master, capture_output=True, check=True)

        render_duration = time.time() - start_time
        file_size_mb = output_mp4.stat().st_size / (1024 * 1024)

        logger.info(
            f"✅ Video Complete: {output_mp4.name} "
            f"({file_size_mb:.2f} MB, {audio_duration:.1f}s, rendered in {render_duration:.1f}s)"
        )

        # 6. Record to SQLite database
        db.insert_video(
            topic_id=topic["id"],
            title=plan["title"],
            duration_seconds=round(audio_duration, 2),
            script_text=plan["narration"],
            audio_path=str(voice_wav),
            video_path=str(output_mp4),
            render_time_seconds=round(render_duration, 2),
        )
        db.update_topic_status(topic["id"], "produced")

        # 7. Cleanup Intermediate Frame & Clip Caches
        self._cleanup_temp_files(timestamp_str)

        return output_mp4

    def _cleanup_temp_files(self, timestamp_str: str) -> None:
        """Purge temporary intermediate slices to preserve disk space."""
        for p in self.temp_dir.glob(f"*{timestamp_str}*"):
            try:
                if p.is_file():
                    p.unlink()
            except Exception:
                pass


media_builder = MediaBuilder()
