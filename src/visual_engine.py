"""Visual asset resolver and FFmpeg motion graphics generator."""

from __future__ import annotations

import json
import logging
import random
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from src.config import config, ASSETS_DIR, TEMP_DIR

logger = logging.getLogger("desi_reels.visual")


class VisualEngine:
    """Manages visual assets, motion transforms (zoompan), and vertical formatting."""

    def __init__(self) -> None:
        self.assets_dir = ASSETS_DIR / "visuals"
        self.temp_dir = TEMP_DIR
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def resolve_scene_visual(
        self, scene: Dict[str, Any], topic_title: str, scene_idx: int
    ) -> Path:
        """Find or generate a 1080x1920 visual asset for the given scene."""
        # 1. Check local assets
        search_query = scene.get("search_query", "").lower()
        for f in self.assets_dir.glob("*.*"):
            if any(term in f.stem.lower() for term in search_query.split() if len(term) > 3):
                logger.info(f"Using matching local asset: {f}")
                return f

        # 2. Try Pexels if API key is provided
        if config.PEXELS_API_KEY:
            pexels_asset = self._fetch_pexels_asset(scene.get("search_query", topic_title), scene_idx)
            if pexels_asset:
                return pexels_asset

        # 3. Procedural high-res cinematic backdrop generation
        procedural_img = self._generate_procedural_backdrop(scene, topic_title, scene_idx)
        return procedural_img

    def _fetch_pexels_asset(self, query: str, scene_idx: int) -> Optional[Path]:
        """Fetch free vertical image from Pexels API."""
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.pexels.com/v1/search?query={encoded}&orientation=portrait&per_page=5"
            req = urllib.request.Request(
                url,
                headers={"Authorization": config.PEXELS_API_KEY},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    photos = data.get("photos", [])
                    if photos:
                        photo_url = photos[0]["src"]["large2x"]
                        out_path = self.temp_dir / f"pexels_{scene_idx}.jpg"
                        urllib.request.urlretrieve(photo_url, out_path)
                        return out_path
        except Exception as e:
            logger.debug(f"Pexels fetch skipped: {e}")
        return None

    def _generate_procedural_backdrop(
        self, scene: Dict[str, Any], topic_title: str, scene_idx: int
    ) -> Path:
        """Generate a vibrant, high-contrast 1080x1920 poster background with food aesthetic."""
        out_path = self.temp_dir / f"backdrop_scene_{scene_idx}.png"

        width, height = 1080, 1920
        # Authentic Indian culinary color themes
        palettes = [
            ((180, 83, 9), (217, 119, 6), (245, 158, 11)),     # Deep Saffron / Turmeric
            ((153, 27, 27), (220, 38, 38), (239, 68, 68)),     # Fiery Kashmiri Chili
            ((21, 128, 61), (34, 197, 94), (74, 222, 128)),    # Fresh Mint / Coriander
            ((112, 26, 117), (162, 28, 175), (192, 38, 211)),  # Royal Jamun / Beetroot
            ((30, 41, 59), (51, 65, 85), (71, 85, 105)),       # Midnight Charcoal Tawa
            ((194, 65, 12), (234, 88, 12), (249, 115, 22)),    # Clay Tandoor / Terracotta
        ]
        color_start, color_mid, color_end = palettes[scene_idx % len(palettes)]

        img = Image.new("RGB", (width, height), color=color_start)
        draw = ImageDraw.Draw(img)

        # Smooth vertical gradient
        for y in range(height):
            ratio = y / height
            if ratio < 0.5:
                sub_r = ratio / 0.5
                r = int(color_start[0] + (color_mid[0] - color_start[0]) * sub_r)
                g = int(color_start[1] + (color_mid[1] - color_start[1]) * sub_r)
                b = int(color_start[2] + (color_mid[2] - color_start[2]) * sub_r)
            else:
                sub_r = (ratio - 0.5) / 0.5
                r = int(color_mid[0] + (color_end[0] - color_mid[0]) * sub_r)
                g = int(color_mid[1] + (color_end[1] - color_mid[1]) * sub_r)
                b = int(color_mid[2] + (color_end[2] - color_mid[2]) * sub_r)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Add atmospheric geometric circles / bokeh texture
        for i in range(12):
            cx = random.randint(100, width - 100)
            cy = random.randint(200, height - 300)
            radius = random.randint(60, 240)
            alpha_color = (
                min(255, color_mid[0] + 40),
                min(255, color_mid[1] + 40),
                min(255, color_mid[2] + 40),
            )
            draw.ellipse(
                [(cx - radius, cy - radius), (cx + radius, cy + radius)],
                outline=alpha_color,
                width=3,
            )

        # Draw decorative culinary badge in center
        badge_top = 700
        badge_bottom = 1220
        draw.rectangle(
            [(80, badge_top), (width - 80, badge_bottom)],
            fill=(0, 0, 0, 160),
            outline=(255, 215, 0),
            width=5,
        )

        overlay_text = scene.get("text_overlay", "INDIAN STREET FOOD")
        draw.text(
            (width // 2, 850),
            overlay_text,
            fill=(255, 230, 0),
            anchor="mm",
            font=None,
        )
        draw.text(
            (width // 2, 980),
            f"SCENE {scene_idx + 1}",
            fill=(255, 255, 255),
            anchor="mm",
            font=None,
        )
        draw.text(
            (width // 2, 1080),
            topic_title[:35].upper(),
            fill=(220, 220, 220),
            anchor="mm",
            font=None,
        )

        img.save(out_path, "PNG")
        return out_path

    def render_scene_clip(
        self,
        image_path: Path,
        duration: float,
        output_mp4: Path,
        zoom_direction: str = "in",
    ) -> Path:
        """Apply smooth FFmpeg zoompan Ken Burns motion to an image, outputting 1080x1920 MP4."""
        total_frames = int(math_ceil(duration * 30))

        # Alternating dynamic motion: Zoom-In vs Pan/Zoom-Out
        if zoom_direction == "in":
            # Smooth slow zoom in towards center
            zoom_expr = f"min(pzoom+0.0018,1.28)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            # Gentle pan across frame
            zoom_expr = "1.15"
            x_expr = f"(on/{total_frames})*(iw-iw/zoom)"
            y_expr = "ih/2-(ih/zoom/2)"

        # FFmpeg filter: scale to high res, apply zoompan at 30 fps, then format to 1080x1920
        vf_filter = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s=1080x1920:fps=30,"
            f"format=yuv420p"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-t",
            f"{duration:.2f}",
            "-vf",
            vf_filter,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "22",
            "-pix_fmt",
            "yuv420p",
            str(output_mp4),
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return output_mp4


def math_ceil(val: float) -> int:
    return int(val) if val == int(val) else int(val) + 1


visual_engine = VisualEngine()
