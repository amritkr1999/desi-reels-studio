"""Comprehensive automated regression and verification test suite for DesiReels Studio."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from src.audio_engine import audio_engine
from src.config import config, MEMORY_DIR, OUTPUT_DIR, TEMP_DIR
from src.db import db
from src.learner import learner_engine
from src.media_builder import media_builder
from src.planner import script_planner
from src.research import research_engine


class TestDesiReelsPipeline(unittest.TestCase):
    """Rigorous tests covering architecture, database, planner, media, and self-learning."""

    def test_01_config_and_directories(self) -> None:
        """Verify configuration defaults and required project directories exist."""
        self.assertTrue(config.DRY_RUN, "Default safety must have DRY_RUN=True")
        self.assertEqual(config.TIMEZONE, "Asia/Kolkata")
        self.assertTrue(MEMORY_DIR.is_dir(), "memory directory must exist")
        self.assertTrue(OUTPUT_DIR.is_dir(), "output directory must exist")
        self.assertTrue(TEMP_DIR.is_dir(), "temp directory must exist")

    def test_02_database_operations(self) -> None:
        """Verify SQLite tables, CRUD operations, and constraints."""
        # Test topic insertion
        test_title = f"Test Topic {os.urandom(4).hex()}"
        topic_id = db.insert_topic(
            title=test_title,
            region="North India (Punjab)",
            category="street_food",
            ground_truth_summary="Test ground truth facts.",
        )
        self.assertIsNotNone(topic_id)

        # Retrieve topic
        topics = db.list_topics(limit=5)
        self.assertTrue(any(t["title"] == test_title for t in topics))

        # Update status
        db.update_topic_status(topic_id, "scripted")
        updated_topics = db.list_topics(limit=10)
        matched = [t for t in updated_topics if t["id"] == topic_id]
        self.assertEqual(matched[0]["status"], "scripted")

    def test_03_research_enrichment(self) -> None:
        """Verify factual topic enrichment and entity extraction."""
        topic = {
            "id": 999,
            "title": "Kolkata Kathi Roll: Nizam's Street Invention",
            "region": "East India (Kolkata)",
            "category": "street_food",
            "ground_truth_summary": "Invented in 1932 at Nizam Restaurant in New Market, Kolkata. Skewered meat rolled inside flaky layered parotta for ₹40.",
        }
        grounded = research_engine.get_grounded_topic_data(topic)
        self.assertIn("ground_truth_summary", grounded)
        entities = grounded.get("required_entities", [])
        self.assertTrue(len(entities) > 0, "Should extract historical or local pricing entities")

    def test_04_script_planner_constraints(self) -> None:
        """Verify 30-second pacing, word count constraints (70-90 words), and 5-6 scenes."""
        topic = {
            "id": 1,
            "title": "Mumbai Vada Pav",
            "region": "West India (Mumbai)",
            "category": "street_food",
            "ground_truth_summary": "Invented in 1966 outside Dadar station by Ashok Vaidya to feed textile mill workers. Spiced potato ball fried in besan batter served in a soft pav with dry garlic-peanut chutney.",
        }
        plan = script_planner.generate_plan(topic)
        self.assertIn("title", plan)
        self.assertIn("narration", plan)
        self.assertIn("scenes", plan)

        words = len(plan["narration"].split())
        self.assertGreaterEqual(words, 68, f"Word count {words} too low for 30s")
        self.assertLessEqual(words, 92, f"Word count {words} too high for 30s")

        scenes = plan["scenes"]
        self.assertIn(len(scenes), (5, 6), f"Scene count {len(scenes)} must be 5 or 6")
        self.assertEqual(scenes[0]["scene_number"], 1)

    def test_05_audio_and_subtitle_generation(self) -> None:
        """Verify audio synthesis and valid .ass/.srt subtitle file output."""
        test_text = "Stop scrolling! Look at this legendary street food marvel sizzling in pure desi ghee!"
        out_wav = TEMP_DIR / "unit_test_voice.wav"
        out_ass = TEMP_DIR / "unit_test_subtitles.ass"
        out_srt = TEMP_DIR / "unit_test_subtitles.srt"

        dur = audio_engine.synthesize(test_text, out_wav)
        self.assertGreater(dur, 1.0, "Audio duration must be greater than 1s")

        audio_engine.generate_ass_subtitles(test_text, dur, out_ass)
        self.assertTrue(out_ass.is_file(), ".ass file must be generated")
        with open(out_ass, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("[Script Info]", content)
            self.assertIn("PlayResX: 1080", content)
            self.assertIn("PlayResY: 1920", content)

        audio_engine.generate_srt_subtitles(test_text, dur, out_srt)
        self.assertTrue(out_srt.is_file(), ".srt file must be generated")
        with open(out_srt, "r", encoding="utf-8") as f:
            srt_content = f.read()
            self.assertIn("-->", srt_content)

    def test_06_rendered_video_broadcast_specs(self) -> None:
        """Verify rendered MP4 conforms strictly to 9:16 vertical broadcast standards."""
        # Find latest rendered video
        latest = db.get_latest_video()
        self.assertIsNotNone(latest, "A rendered video must exist in database from dry run")

        video_path = Path(latest["video_path"])
        self.assertTrue(video_path.is_file(), f"Rendered video file {video_path} must exist on disk")

        # FFprobe inspection
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=width,height,codec_name,codec_type:format=duration,size",
            "-of",
            "json",
            str(video_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(res.stdout)

        video_stream = next((s for s in probe_data["streams"] if s["codec_type"] == "video"), None)
        audio_stream = next((s for s in probe_data["streams"] if s["codec_type"] == "audio"), None)

        self.assertIsNotNone(video_stream, "Must have a video stream")
        self.assertIsNotNone(audio_stream, "Must have an audio stream")

        # Check resolution: 1080x1920
        self.assertEqual(video_stream["width"], 1080, "Video width must be 1080")
        self.assertEqual(video_stream["height"], 1920, "Video height must be 1920 (9:16 vertical)")
        self.assertEqual(video_stream["codec_name"], "h264", "Video codec must be H.264")
        self.assertEqual(audio_stream["codec_name"], "aac", "Audio codec must be AAC")

        duration = float(probe_data["format"]["duration"])
        self.assertGreaterEqual(duration, 28.0, f"Duration {duration}s must be >= 28s")
        self.assertLessEqual(duration, 33.0, f"Duration {duration}s must be <= 33s")

    def test_07_learner_feedback_engine(self) -> None:
        """Verify that human critique adjusts the style playbook correctly."""
        initial_playbook = learner_engine.load_playbook()
        old_wpm = initial_playbook["pacing"]["target_wpm"]
        old_margin = initial_playbook["subtitles"]["margin_v"]

        # Apply critique
        learner_engine.apply_human_feedback(
            rating=5,
            critique="The speech was a bit too slow, and subtitles were too low on Instagram.",
            video_id=1,
        )

        updated_playbook = learner_engine.load_playbook()
        # WPM should increase (faster speech)
        self.assertGreater(updated_playbook["pacing"]["target_wpm"], old_wpm)
        # Margin should increase (raise subtitles higher)
        self.assertGreater(updated_playbook["subtitles"]["margin_v"], old_margin)

    def test_08_publisher_dry_run_safety(self) -> None:
        """Verify that multi-platform publisher enforces DRY_RUN safety and formats payloads."""
        from src.publisher import publisher

        latest = db.get_latest_video()
        self.assertIsNotNone(latest)
        video_path = Path(latest["video_path"])

        res = publisher.publish_video(
            video_path=video_path,
            title="Authentic Lucknow Galouti Kebab",
            description="Mouthwatering kebab recipe in Chowk bazaar.",
            tags=["#Shorts", "#IndianFood"],
            dry_run=True,
        )

        self.assertTrue(res["dry_run"])
        self.assertEqual(res["platforms"]["youtube"]["status"], "dry_run")
        self.assertEqual(res["platforms"]["instagram"]["status"], "dry_run")
        self.assertEqual(res["platforms"]["facebook"]["status"], "dry_run")
        self.assertIn("https://youtube.com/shorts/", res["platforms"]["youtube"]["url"])
        self.assertIn("https://www.instagram.com/reel/", res["platforms"]["instagram"]["url"])
        self.assertIn("https://www.facebook.com/reel/", res["platforms"]["facebook"]["url"])


if __name__ == "__main__":
    unittest.main()
