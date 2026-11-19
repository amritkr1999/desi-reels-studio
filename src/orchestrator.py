"""Master daily orchestrator: runs research -> plan -> render -> publish -> cleanup."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import config
from src.db import db
from src.media_builder import media_builder
from src.planner import script_planner
from src.research import research_engine

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("desi_reels.orchestrator")


def run_daily_pipeline(dry_run: Optional[bool] = None) -> int:
    """Execute complete once-daily automated video creation and staging run."""
    start_time = time.time()
    effective_dry_run = config.DRY_RUN if dry_run is None else dry_run

    logger.info("==================================================================")
    logger.info(f"🚀 DesiReels Daily Run Started | DRY_RUN: {effective_dry_run}")
    logger.info(f"Target Timezone: {config.TIMEZONE}")
    logger.info("==================================================================")

    # 1. Ensure topics exist in database
    research_engine.seed_database_if_empty()

    # 2. Select next pending topic
    topic = db.get_next_pending_topic()
    if not topic:
        logger.error("No pending topics found in database! Please add topics via dashboard or JSON.")
        return 1

    logger.info(f"📍 Selected Topic #{topic['id']}: {topic['title']} ({topic['region']})")

    # 3. Grounded Factual Research
    grounded = research_engine.get_grounded_topic_data(topic)
    logger.info(f"Factual grounding complete. Context length: {len(grounded.get('ground_truth_summary', ''))} chars")

    # 4. Generate 30s Scene Script Plan
    logger.info("Generating script and scene plan with local Ollama / style playbook...")
    plan = script_planner.generate_plan(grounded)
    logger.info(f"Plan generated: '{plan['title']}' ({len(plan['narration'].split())} words, {len(plan['scenes'])} scenes)")

    # 5. Build Media (Audio + Subtitles + Visual Motion -> 1080x1920 MP4)
    logger.info("Rendering 1080x1920 vertical video composite...")
    video_path = media_builder.build_video(topic, plan)

    # 6. Publishing Staging / Upload
    try:
        from src.publisher import publisher
        logger.info(f"Staging video for publishing across platforms (DRY_RUN={effective_dry_run})...")
        pub_results = publisher.publish_video(
            video_path=video_path,
            title=plan["youtube_title"],
            description=plan["caption"],
            tags=plan["hashtags"],
            dry_run=effective_dry_run,
        )
        logger.info(f"Publishing stage complete: {pub_results}")
    except ImportError:
        logger.info("Publisher module pending implementation in Phase 5.")
    except Exception as e:
        logger.error(f"Publishing encountered an error: {e}")

    total_elapsed = time.time() - start_time
    logger.info("==================================================================")
    logger.info(f"🎉 Daily Run Successfully Finished in {total_elapsed:.1f}s!")
    logger.info(f"Output File: {video_path}")
    logger.info("Review your video at: http://localhost:8500")
    logger.info("==================================================================")
    return 0


if __name__ == "__main__":
    is_dry = "--live" not in sys.argv
    sys.exit(run_daily_pipeline(dry_run=is_dry))
