"""Audio synthesis and word-aligned subtitle generation engine."""

from __future__ import annotations

import logging
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import config, TEMP_DIR

logger = logging.getLogger("desi_reels.audio")


class AudioEngine:
    """Handles text-to-speech synthesis and word-level .ass subtitle timing."""

    def __init__(self) -> None:
        self.temp_dir = TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_audio_duration(self, audio_path: Path) -> float:
        """Accurately extract duration in seconds using ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not probe audio duration for {audio_path}: {e}")
            return 30.0

    def synthesize(self, text: str, output_wav: Path, voice: Optional[str] = None) -> float:
        """Synthesize speech from text using macOS say or fallback to synth tone."""
        voice = voice or config.MACOS_SAY_VOICE
        output_wav.parent.mkdir(parents=True, exist_ok=True)

        # 1. Try macOS say command
        try:
            cmd = [
                "say",
                "-v",
                voice,
                "--file-format=WAVE",
                "--data-format=LEI16@22050",
                text,
                "-o",
                str(output_wav),
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            if output_wav.is_file() and output_wav.stat().st_size > 10000:
                duration = self.get_audio_duration(output_wav)
                if duration > 1.0:
                    logger.info(f"Synthesized {duration:.1f}s speech using macOS voice '{voice}'")
                    return duration
        except Exception as e:
            logger.debug(f"macOS say failed or empty: {e}")

        # 2. Fallback: Generate spoken-pace ambient audio track using FFmpeg
        logger.info("Using FFmpeg audio generator fallback.")
        words = len(text.split())
        est_duration = max(28.0, min(31.0, (words / config.TARGET_WPM) * 60.0))

        # Generate a warm, gentle voiceover carrier audio track
        cmd_fallback = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=d={est_duration}:c=pink:r=44100:a=0.01",
            "-filter:a",
            "lowpass=f=1200,volume=0.3",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output_wav),
        ]
        subprocess.run(cmd_fallback, capture_output=True, check=True)
        return self.get_audio_duration(output_wav)

    def generate_ass_subtitles(
        self,
        text: str,
        total_duration: float,
        output_ass: Path,
        scenes: Optional[List[Dict[str, Any]]] = None,
    ) -> Path:
        """Generate high-contrast, animated 9:16 vertical ASS subtitles."""
        words = text.split()
        if not words:
            return output_ass

        # Calculate word-level timestamps
        # Allocate time proportionally based on word character length
        char_weights = [max(1, len(re.sub(r"[^\w]", "", w))) for w in words]
        total_weight = sum(char_weights)
        time_per_weight = (total_duration - 0.5) / total_weight

        word_timings: List[Dict[str, Any]] = []
        curr_t = 0.2
        for w, weight in zip(words, char_weights):
            dur = weight * time_per_weight
            word_timings.append({
                "word": w,
                "start": curr_t,
                "end": curr_t + dur,
            })
            curr_t += dur

        # Group words into punchy 2-3 word display phrases
        phrase_size = 3
        phrases = []
        for i in range(0, len(word_timings), phrase_size):
            chunk = word_timings[i : i + phrase_size]
            start_t = chunk[0]["start"]
            end_t = chunk[-1]["end"]
            phrases.append({
                "start": start_t,
                "end": end_t,
                "words": chunk,
            })

        # Build ASS format content
        header = """[Script Info]
Title: DesiReels Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,68,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4.5,2.0,2,80,80,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        dialogue_lines = []
        for p in phrases:
            start_str = self._format_ass_time(p["start"])
            end_str = self._format_ass_time(p["end"])

            # Highlight the phrase with bold uppercase styling and vibrant cyan accent
            raw_text = " ".join([item["word"] for item in p["words"]]).upper()
            line = f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{{\\b1\\c&H0000E5FF&}}{raw_text}{{\\c&H00FFFFFF&}}"
            dialogue_lines.append(line)

        output_ass.parent.mkdir(parents=True, exist_ok=True)
        with open(output_ass, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(dialogue_lines) + "\n")

        logger.info(f"Generated styled .ass subtitles at {output_ass}")
        return output_ass

    def generate_srt_subtitles(
        self,
        text: str,
        total_duration: float,
        output_srt: Path,
    ) -> Path:
        """Generate standard SRT subtitles for platform compatibility and container embedding."""
        words = text.split()
        if not words:
            return output_srt

        char_weights = [max(1, len(re.sub(r"[^\w]", "", w))) for w in words]
        total_weight = sum(char_weights)
        time_per_weight = (total_duration - 0.5) / total_weight

        word_timings = []
        curr_t = 0.2
        for w, weight in zip(words, char_weights):
            dur = weight * time_per_weight
            word_timings.append({"word": w, "start": curr_t, "end": curr_t + dur})
            curr_t += dur

        phrase_size = 4
        srt_lines = []
        idx = 1
        for i in range(0, len(word_timings), phrase_size):
            chunk = word_timings[i : i + phrase_size]
            start_str = self._format_srt_time(chunk[0]["start"])
            end_str = self._format_srt_time(chunk[-1]["end"])
            phrase_text = " ".join([item["word"] for item in chunk]).upper()
            srt_lines.append(f"{idx}\n{start_str} --> {end_str}\n{phrase_text}\n")
            idx += 1

        output_srt.parent.mkdir(parents=True, exist_ok=True)
        with open(output_srt, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))

        logger.info(f"Generated .srt subtitles at {output_srt}")
        return output_srt

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time string (HH:MM:SS,mmm)."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds - int(seconds)) * 1000))
        if ms >= 1000:
            ms = 999
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _format_ass_time(self, seconds: float) -> str:
        """Format seconds to ASS time string (H:MM:SS.cs)."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        if cs >= 100:
            cs = 99
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


audio_engine = AudioEngine()
