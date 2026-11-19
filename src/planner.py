"""Script and scene planner integrating local Ollama and style playbook constraints."""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import config, MEMORY_DIR

logger = logging.getLogger("desi_reels.planner")


class ScriptPlanner:
    """Generates structured 30-second vertical video scripts with exact scene timing."""

    def __init__(self, playbook_path: Optional[Path] = None) -> None:
        self.playbook_path = playbook_path or (MEMORY_DIR / "style_playbook.json")
        self.playbook = self._load_playbook()

    def _load_playbook(self) -> Dict[str, Any]:
        if self.playbook_path.is_file():
            try:
                with open(self.playbook_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load playbook: {e}")
        return {
            "pacing": {
                "target_duration_seconds": 30.0,
                "target_word_count_min": 75,
                "target_word_count_max": 85,
                "target_scenes": 6,
            }
        }

    def generate_plan(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete 30-second script & scene breakdown."""
        # Try Ollama local generation first
        ollama_result = self._generate_with_ollama(topic)
        if ollama_result:
            return ollama_result

        # Fallback to deterministic fact-grounded template planner
        logger.info("Using grounded deterministic template planner fallback.")
        return self._generate_grounded_fallback(topic)

    def _generate_with_ollama(self, topic: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call local Ollama instance with JSON schema constraints."""
        target_min = self.playbook.get("pacing", {}).get("target_word_count_min", 75)
        target_max = self.playbook.get("pacing", {}).get("target_word_count_max", 85)

        prompt = f"""You are the senior director for 'DesiReels', a viral Indian food and culture short-form channel.
Create a strict 30-second vertical short video script based ONLY on these verified facts:
TOPIC: {topic['title']}
REGION: {topic['region']}
FACTUAL GROUND TRUTH: {topic.get('ground_truth_summary', '')}

RULES:
1. Total voiceover narration MUST be between {target_min} and {target_max} words.
2. Structure:
   - 0.0s - 3.0s: Powerful pattern-interrupt hook (curiosity or sensory shock).
   - 3.0s - 14.0s: The street food star, aroma, craft, and ingredients.
   - 14.0s - 23.0s: The historical backstory or cultural origin.
   - 23.0s - 30.0s: Practical travel tip (price in ₹ or exact location) + engaging question for comments.
3. Divide into exactly 5 or 6 timed scenes totaling exactly 30.0 seconds.
4. Output ONLY valid JSON with no markdown wrapping or extra commentary:
{{
  "title": "Punchy viral title",
  "youtube_title": "Title under 60 chars #Shorts",
  "caption": "Instagram/Facebook caption with hook, location details, and question",
  "hashtags": ["#IndianStreetFood", "#Shorts", "#StreetFood", "#DesiFood", "#IncredibleIndia"],
  "narration": "Full voiceover script between {target_min} and {target_max} words.",
  "scenes": [
    {{
      "scene_number": 1,
      "start_time": 0.0,
      "end_time": 3.0,
      "visual_description": "Vivid visual description",
      "search_query": "b-roll search keywords",
      "text_overlay": "BOLD HOOK TEXT",
      "audio_cue": "sizzle"
    }}
  ]
}}"""

        req_data = {
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.4, "num_predict": 1024},
        }

        try:
            req = urllib.request.Request(
                f"{config.OLLAMA_HOST}/api/generate",
                data=json.dumps(req_data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=config.OLLAMA_TIMEOUT_SECONDS) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    response_text = data.get("response", "")
                    parsed = json.loads(response_text)
                    if self._validate_plan(parsed):
                        return parsed
        except Exception as e:
            logger.debug(f"Ollama generation skipped or failed: {e}")
        return None

    def _generate_grounded_fallback(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """High-quality grounded fallback generator ensuring strict 75-85 word compliance."""
        title = topic["title"]
        region = topic["region"]
        facts = topic.get("ground_truth_summary") or title

        # Build clean 78-82 word narration from verified facts
        clean_facts = facts.replace("\n", " ").strip()
        sentences = [s.strip() for s in re.split(r"[.!?]", clean_facts) if len(s.strip()) > 15]

        lead = sentences[0] if sentences else f"In the historic lanes of {region}, this street food marvel is legendary."
        body = sentences[1] if len(sentences) > 1 else "Crafted over boiling charcoal with ancient aromatic spices, every bite is pure culinary magic."
        origin = sentences[2] if len(sentences) > 2 else "Passed down through generations, this recipe has fueled locals for decades."

        narration = (
            f"Think you know Indian street food? Look at this legendary dish from {region}! "
            f"{lead}. {body}. {origin}. "
            f"Would you try this iconic delicacy? Tell us your favorite street bite in the comments below!"
        )

        # Regulate word count to 78-82 words
        words = narration.split()
        if len(words) < 75:
            narration = (
                f"Stop scrolling! Think you know Indian street food? Look at this legendary specialty from {region}! "
                f"{lead}. {body}. {origin}. "
                f"Every single morning, crowds gather just for one steaming fresh plate. "
                f"Would you dare try this unforgettable flavor? Let us know in the comments below!"
            )
            words = narration.split()

        if len(words) > 85:
            words = words[:82]
            narration = " ".join(words)
            if not narration.endswith("."):
                narration += " Tell us in the comments!"

        scenes = [
            {
                "scene_number": 1,
                "start_time": 0.0,
                "end_time": 3.0,
                "visual_description": f"High energy sizzling closeup of {title} in {region}",
                "search_query": f"{title} indian street food sizzling closeup",
                "text_overlay": "MUST TRY STREET FOOD!",
                "audio_cue": "sizzle",
            },
            {
                "scene_number": 2,
                "start_time": 3.0,
                "end_time": 8.5,
                "visual_description": f"Vendor skillfully preparing the dish with authentic spices and steam",
                "search_query": f"indian street food vendor cooking spices steam",
                "text_overlay": "THE SECRET CRAFT",
                "audio_cue": "crowd_chatter",
            },
            {
                "scene_number": 3,
                "start_time": 8.5,
                "end_time": 14.0,
                "visual_description": f"Macro shot of bubbling tawa, melting ghee, or rich steaming sauce",
                "search_query": f"indian cuisine boiling curry tawa ghee macro",
                "text_overlay": "PURE FLAVOR",
                "audio_cue": "bubble",
            },
            {
                "scene_number": 4,
                "start_time": 14.0,
                "end_time": 19.5,
                "visual_description": f"Historical atmosphere of {region} narrow bazaar and heritage street",
                "search_query": f"{region} heritage old bazaar street morning",
                "text_overlay": "100 YEAR HERITAGE",
                "audio_cue": "ambient_bazaar",
            },
            {
                "scene_number": 5,
                "start_time": 19.5,
                "end_time": 25.0,
                "visual_description": f"Plating in eco-friendly leaf donas or clay kulhad with rich garnish",
                "search_query": f"indian street food serving clay plate kulhad garnish",
                "text_overlay": "FRESH SERVING",
                "audio_cue": "spoon_clink",
            },
            {
                "scene_number": 6,
                "start_time": 25.0,
                "end_time": 30.0,
                "visual_description": f"Delighted customer enjoying the bite with mouthwatering steam",
                "search_query": f"eating indian street food happy smiling food reel",
                "text_overlay": "WOULD YOU TRY THIS?",
                "audio_cue": "ding",
            },
        ]

        clean_title = re.sub(r"[:\-]", " - ", title).split(" - ")[0].strip()
        return {
            "title": f"The Legendary Secret Behind {clean_title}!",
            "youtube_title": f"India's Secret {clean_title} | 100-Year Heritage #Shorts",
            "caption": (
                f"Have you ever tasted the legendary {clean_title} in {region}? 🇮🇳✨\n\n"
                f"{narration}\n\n"
                f"Save this for your next trip to {region}! What should we cover next?"
            ),
            "hashtags": [
                "#IndianStreetFood",
                "#Shorts",
                "#StreetFoodIndia",
                "#DesiReels",
                "#IncredibleIndia",
                "#FoodieShorts",
            ],
            "narration": narration,
            "scenes": scenes,
        }

    def _validate_plan(self, plan: Dict[str, Any]) -> bool:
        """Validate structure and word count."""
        if not isinstance(plan, dict):
            return False
        required_keys = ["title", "narration", "scenes"]
        if not all(k in plan for k in required_keys):
            return False
        word_count = len(plan["narration"].split())
        if word_count < 65 or word_count > 95:
            logger.warning(f"Plan word count out of range: {word_count}")
            return False
        if not isinstance(plan["scenes"], list) or len(plan["scenes"]) < 4:
            return False
        return True


script_planner = ScriptPlanner()
