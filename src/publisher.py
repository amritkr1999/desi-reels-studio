"""Multi-platform short video publisher supporting YouTube Shorts, Instagram Reels, and Facebook Reels."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import config
from src.db import db

logger = logging.getLogger("desi_reels.publisher")
IST = timezone(timedelta(hours=5, minutes=30))


class PlatformPublisher:
    """Unified publisher for YouTube Shorts, Instagram Reels, and Facebook Reels with safe DRY_RUN defaults."""

    def __init__(self) -> None:
        pass

    def publish_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Publish or stage a video across all configured platforms."""
        is_dry = config.DRY_RUN if dry_run is None else dry_run
        tags = tags or ["#IndianStreetFood", "#Shorts", "#FoodReels"]
        scheduled_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

        # Find video ID in database
        latest_vid = db.get_latest_video()
        video_id = latest_vid["id"] if latest_vid else 1

        results = {
            "timestamp": scheduled_ist,
            "dry_run": is_dry,
            "video_path": str(video_path),
            "platforms": {},
        }

        # 1. YouTube Shorts
        yt_res = self._publish_youtube(video_id, video_path, title, description, tags, is_dry, scheduled_ist)
        results["platforms"]["youtube"] = yt_res

        # 2. Instagram Reels
        ig_res = self._publish_instagram(video_id, video_path, description, tags, is_dry, scheduled_ist)
        results["platforms"]["instagram"] = ig_res

        # 3. Facebook Reels
        fb_res = self._publish_facebook(video_id, video_path, description, tags, is_dry, scheduled_ist)
        results["platforms"]["facebook"] = fb_res

        return results

    # --------------------------------------------------------------------------
    # YouTube Shorts Publishing (Google Data API v3)
    # --------------------------------------------------------------------------
    def _publish_youtube(
        self,
        video_id: int,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str],
        dry_run: bool,
        scheduled_ist: str,
    ) -> Dict[str, Any]:
        """Publish to YouTube Shorts with #Shorts tag in title/description."""
        yt_title = title if "#Shorts" in title else f"{title} #Shorts"
        if len(yt_title) > 100:
            yt_title = yt_title[:90] + " #Shorts"

        if dry_run or not config.YOUTUBE_CLIENT_SECRETS_FILE.is_file():
            sim_id = f"yt_dry_{int(time.time())}"
            sim_url = f"https://youtube.com/shorts/{sim_id}"
            db.log_publish_event(
                video_id=video_id,
                platform="youtube",
                scheduled_for_ist=scheduled_ist,
                status="dry_run",
                published_at_ist=scheduled_ist,
                external_post_id=sim_id,
                external_post_url=sim_url,
            )
            return {
                "status": "dry_run",
                "message": "Simulated upload. To enable live uploads, add youtube_client_secret.json in credentials/.",
                "post_id": sim_id,
                "url": sim_url,
                "title": yt_title,
            }

        # Live YouTube Upload via Google API Client
        try:
            import google.oauth2.credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            if not config.YOUTUBE_TOKEN_FILE.is_file():
                raise FileNotFoundError(
                    f"OAuth token file not found at {config.YOUTUBE_TOKEN_FILE}. Run authentication setup first."
                )

            with open(config.YOUTUBE_TOKEN_FILE, "r", encoding="utf-8") as f:
                token_info = json.load(f)

            creds = google.oauth2.credentials.Credentials.from_authorized_user_info(token_info)
            youtube = build("youtube", "v3", credentials=creds)

            body = {
                "snippet": {
                    "title": yt_title,
                    "description": f"{description}\n\n{' '.join(tags)}",
                    "tags": tags,
                    "categoryId": "24",  # Entertainment
                },
                "status": {
                    "privacyStatus": config.YOUTUBE_PRIVACY_STATUS,
                    "selfDeclaredMadeForKids": False,
                },
            }

            media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"YouTube Upload Progress: {int(status.progress() * 100)}%")

            real_id = response.get("id")
            real_url = f"https://youtube.com/shorts/{real_id}"

            db.log_publish_event(
                video_id=video_id,
                platform="youtube",
                scheduled_for_ist=scheduled_ist,
                status="published",
                published_at_ist=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
                external_post_id=real_id,
                external_post_url=real_url,
            )
            return {"status": "published", "post_id": real_id, "url": real_url}

        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            db.log_publish_event(
                video_id=video_id,
                platform="youtube",
                scheduled_for_ist=scheduled_ist,
                status="failed",
                error_message=str(e),
            )
            return {"status": "failed", "error": str(e)}

    # --------------------------------------------------------------------------
    # Instagram Reels Publishing (Meta Graph API)
    # --------------------------------------------------------------------------
    def _publish_instagram(
        self,
        video_id: int,
        video_path: Path,
        description: str,
        tags: List[str],
        dry_run: bool,
        scheduled_ist: str,
    ) -> Dict[str, Any]:
        """Publish to Instagram Reels via Meta Graph API Container Protocol."""
        ig_caption = f"{description}\n\n{' '.join(tags)}"

        if dry_run or not config.INSTAGRAM_ACCOUNT_ID or not config.INSTAGRAM_ACCESS_TOKEN:
            sim_id = f"ig_dry_{int(time.time())}"
            sim_url = f"https://www.instagram.com/reel/{sim_id}/"
            db.log_publish_event(
                video_id=video_id,
                platform="instagram",
                scheduled_for_ist=scheduled_ist,
                status="dry_run",
                published_at_ist=scheduled_ist,
                external_post_id=sim_id,
                external_post_url=sim_url,
            )
            return {
                "status": "dry_run",
                "message": "Simulated upload. To enable live Instagram uploads, set INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN in .env.",
                "post_id": sim_id,
                "url": sim_url,
            }

        # Live Instagram Reels Upload
        try:
            # Step 1: Initialize Reel Container
            init_url = f"https://graph.facebook.com/v20.0/{config.INSTAGRAM_ACCOUNT_ID}/media"
            init_data = urllib.parse.urlencode({
                "media_type": "REELS",
                "upload_type": "resumable",
                "caption": ig_caption,
                "access_token": config.INSTAGRAM_ACCESS_TOKEN,
            }).encode("utf-8")

            req = urllib.request.Request(init_url, data=init_data, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                init_res = json.loads(resp.read().decode("utf-8"))
                container_id = init_res.get("id")
                upload_uri = init_res.get("uri")

            if not upload_uri:
                raise ValueError(f"No upload URI returned from Meta container creation: {init_res}")

            # Step 2: Upload Video Binary
            file_size = video_path.stat().st_size
            with open(video_path, "rb") as f:
                video_bytes = f.read()

            upload_req = urllib.request.Request(
                upload_uri,
                data=video_bytes,
                headers={
                    "Authorization": f"OAuth {config.INSTAGRAM_ACCESS_TOKEN}",
                    "offset": "0",
                    "file_size": str(file_size),
                    "Content-Type": "application/octet-stream",
                },
                method="POST",
            )
            with urllib.request.urlopen(upload_req, timeout=60) as resp:
                logger.info(f"Instagram binary upload HTTP {resp.status}")

            # Step 3: Poll status until FINISHED
            status_url = f"https://graph.facebook.com/v20.0/{container_id}?fields=status_code&access_token={config.INSTAGRAM_ACCESS_TOKEN}"
            for _ in range(15):
                time.sleep(4)
                with urllib.request.urlopen(status_url, timeout=10) as s_resp:
                    s_data = json.loads(s_resp.read().decode("utf-8"))
                    if s_data.get("status_code") == "FINISHED":
                        break
                    if s_data.get("status_code") == "ERROR":
                        raise RuntimeError(f"Instagram container processing failed: {s_data}")

            # Step 4: Publish Container
            pub_url = f"https://graph.facebook.com/v20.0/{config.INSTAGRAM_ACCOUNT_ID}/media_publish"
            pub_data = urllib.parse.urlencode({
                "creation_id": container_id,
                "access_token": config.INSTAGRAM_ACCESS_TOKEN,
            }).encode("utf-8")

            pub_req = urllib.request.Request(pub_url, data=pub_data, method="POST")
            with urllib.request.urlopen(pub_req, timeout=15) as p_resp:
                pub_res = json.loads(p_resp.read().decode("utf-8"))
                media_id = pub_res.get("id")

            real_url = f"https://www.instagram.com/reel/{media_id}/"
            db.log_publish_event(
                video_id=video_id,
                platform="instagram",
                scheduled_for_ist=scheduled_ist,
                status="published",
                published_at_ist=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
                external_post_id=media_id,
                external_post_url=real_url,
            )
            return {"status": "published", "post_id": media_id, "url": real_url}

        except Exception as e:
            logger.error(f"Instagram upload failed: {e}")
            db.log_publish_event(
                video_id=video_id,
                platform="instagram",
                scheduled_for_ist=scheduled_ist,
                status="failed",
                error_message=str(e),
            )
            return {"status": "failed", "error": str(e)}

    # --------------------------------------------------------------------------
    # Facebook Reels Publishing (Meta Page Video Reels API)
    # --------------------------------------------------------------------------
    def _publish_facebook(
        self,
        video_id: int,
        video_path: Path,
        description: str,
        tags: List[str],
        dry_run: bool,
        scheduled_ist: str,
    ) -> Dict[str, Any]:
        """Publish to Facebook Page Reels via 3-step Page Reels flow."""
        fb_caption = f"{description}\n\n{' '.join(tags)}"

        if dry_run or not config.FACEBOOK_PAGE_ID or not config.FACEBOOK_PAGE_ACCESS_TOKEN:
            sim_id = f"fb_dry_{int(time.time())}"
            sim_url = f"https://www.facebook.com/reel/{sim_id}/"
            db.log_publish_event(
                video_id=video_id,
                platform="facebook",
                scheduled_for_ist=scheduled_ist,
                status="dry_run",
                published_at_ist=scheduled_ist,
                external_post_id=sim_id,
                external_post_url=sim_url,
            )
            return {
                "status": "dry_run",
                "message": "Simulated upload. To enable live Facebook Page uploads, set FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN in .env.",
                "post_id": sim_id,
                "url": sim_url,
            }

        # Live Facebook Page Reels Upload
        try:
            # Step 1: Start upload session
            start_url = f"https://graph.facebook.com/v20.0/{config.FACEBOOK_PAGE_ID}/video_reels"
            start_data = urllib.parse.urlencode({
                "upload_phase": "start",
                "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
            }).encode("utf-8")

            req = urllib.request.Request(start_url, data=start_data, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                start_res = json.loads(resp.read().decode("utf-8"))
                fb_video_id = start_res.get("video_id")
                upload_url = start_res.get("upload_url")

            if not upload_url:
                raise ValueError(f"No upload URL returned from Facebook start reel: {start_res}")

            # Step 2: Upload Binary Chunks
            file_size = video_path.stat().st_size
            with open(video_path, "rb") as f:
                video_bytes = f.read()

            upload_req = urllib.request.Request(
                upload_url,
                data=video_bytes,
                headers={
                    "Authorization": f"OAuth {config.FACEBOOK_PAGE_ACCESS_TOKEN}",
                    "offset": "0",
                    "file_size": str(file_size),
                    "Content-Type": "application/octet-stream",
                },
                method="POST",
            )
            with urllib.request.urlopen(upload_req, timeout=60) as resp:
                logger.info(f"Facebook binary upload HTTP {resp.status}")

            # Step 3: Finish and Publish
            finish_url = f"https://graph.facebook.com/v20.0/{config.FACEBOOK_PAGE_ID}/video_reels"
            finish_data = urllib.parse.urlencode({
                "upload_phase": "finish",
                "video_id": fb_video_id,
                "video_state": "PUBLISHED",
                "description": fb_caption,
                "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
            }).encode("utf-8")

            finish_req = urllib.request.Request(finish_url, data=finish_data, method="POST")
            with urllib.request.urlopen(finish_req, timeout=15) as f_resp:
                fin_res = json.loads(f_resp.read().decode("utf-8"))

            real_url = f"https://www.facebook.com/reel/{fb_video_id}/"
            db.log_publish_event(
                video_id=video_id,
                platform="facebook",
                scheduled_for_ist=scheduled_ist,
                status="published",
                published_at_ist=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
                external_post_id=fb_video_id,
                external_post_url=real_url,
            )
            return {"status": "published", "post_id": fb_video_id, "url": real_url}

        except Exception as e:
            logger.error(f"Facebook upload failed: {e}")
            db.log_publish_event(
                video_id=video_id,
                platform="facebook",
                scheduled_for_ist=scheduled_ist,
                status="failed",
                error_message=str(e),
            )
            return {"status": "failed", "error": str(e)}


publisher = PlatformPublisher()
