"""Grounded research engine with Wikipedia/Wikivoyage enrichment and seed catalog management."""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import config, DATA_DIR
from src.db import db

logger = logging.getLogger("desi_reels.research")


class ResearchEngine:
    """Enriches street food and travel topics with verified factual context."""

    def __init__(self, seed_file: Optional[Path] = None) -> None:
        self.seed_file = seed_file or (DATA_DIR / "topics_seed.json")

    def seed_database_if_empty(self) -> int:
        """Seed the SQLite database from topics_seed.json if table is empty."""
        existing_topics = db.list_topics(limit=5)
        if existing_topics:
            return 0

        if not self.seed_file.is_file():
            logger.warning(f"Seed file not found at {self.seed_file}")
            return 0

        with open(self.seed_file, "r", encoding="utf-8") as f:
            topics_data: List[Dict[str, Any]] = json.load(f)

        count = 0
        for item in topics_data:
            res = db.insert_topic(
                title=item["title"],
                region=item["region"],
                category=item["category"],
                ground_truth_summary=item.get("ground_truth_summary"),
            )
            if res:
                count += 1

        logger.info(f"Seeded {count} topics into database.")
        return count

    def fetch_wikipedia_summary(self, query: str) -> Optional[str]:
        """Fetch summary extract from Wikipedia API, with graceful fallback."""
        try:
            # Clean query for search
            clean_term = re.sub(r"[:\-\(\)]", " ", query).split()[0:3]
            search_str = " ".join(clean_term)
            encoded = urllib.parse.quote(search_str)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DesiReelsStudio/1.0 (Educational Indian Travel System)"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    extract = data.get("extract")
                    if extract and len(extract) > 40:
                        return extract
        except Exception as e:
            logger.debug(f"Wikipedia lookup skipped or failed for '{query}': {e}")
        return None

    def get_grounded_topic_data(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve topic details fortified with factual anti-hallucination checkpoints."""
        title = topic["title"]
        existing_gt = topic.get("ground_truth_summary") or ""

        # Try Wikipedia enrichment if available
        wiki_summary = self.fetch_wikipedia_summary(title)

        combined_facts = existing_gt
        if wiki_summary and wiki_summary not in existing_gt:
            combined_facts = f"{existing_gt}\n\nAdditional Historical Context: {wiki_summary}".strip()

        # Update db if new facts were gathered
        if combined_facts != existing_gt:
            db.update_topic_status(topic["id"], topic["status"], ground_truth=combined_facts)

        return {
            "id": topic["id"],
            "title": title,
            "region": topic["region"],
            "category": topic["category"],
            "ground_truth_summary": combined_facts,
            "required_entities": self._extract_key_entities(combined_facts, title),
        }

    def _extract_key_entities(self, text: str, title: str) -> List[str]:
        """Extract key named entities that the script generator must reference."""
        entities = []
        # Extract years / centuries
        years = re.findall(r"\b(1[6-9]\d\d|20\d\d|[0-9]+th century)\b", text, re.IGNORECASE)
        if years:
            entities.append(f"Historical anchor: {years[0]}")

        # Extract rupees or pricing if present
        prices = re.findall(r"₹\s*\d+", text)
        if prices:
            entities.append(f"Local price: {prices[0]}")

        # Extract quoted or key local food/shop names
        shop_matches = re.findall(r"[A-Z][a-z]+ (?:Bazaar|Chowk|Ghat|Road|Market|Kababi|Dosa|Chaat|Sweet Mart|Mishthan Bhandar)", text)
        for s in shop_matches[:2]:
            if s not in entities:
                entities.append(s)

        return entities


research_engine = ResearchEngine()
