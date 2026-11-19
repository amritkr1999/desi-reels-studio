"""Lightweight local review & operations dashboard (http://localhost:8500)."""

from __future__ import annotations

import json
import logging
import mimetypes
import os
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

from src.config import config, OUTPUT_DIR, MEMORY_DIR
from src.db import db
from src.learner import learner_engine
from src.media_builder import media_builder
from src.planner import script_planner
from src.research import research_engine

logger = logging.getLogger("desi_reels.dashboard")


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DesiReels Studio — Operations & Review Dashboard</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --accent: #f59e0b;
      --accent-hover: #d97706;
      --text: #f8fafc;
      --muted: #94a3b8;
      --border: #334155;
      --success: #10b981;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
    }
    .brand { font-size: 1.5rem; font-weight: 800; color: var(--accent); }
    .badge {
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      background: #3b82f6;
      color: white;
    }
    .badge.dry-run { background: #8b5cf6; }
    .grid {
      display: grid;
      grid-template-columns: 420px 1fr;
      gap: 24px;
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 14px;
      color: var(--accent);
      display: flex;
      justify-content: space-between;
    }
    .video-container {
      width: 100%;
      max-width: 380px;
      height: 640px;
      background: #000;
      border-radius: 12px;
      overflow: hidden;
      margin: 0 auto 16px auto;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
    }
    video {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .btn {
      background: var(--accent);
      color: #000;
      font-weight: 700;
      border: none;
      padding: 10px 18px;
      border-radius: 8px;
      cursor: pointer;
      transition: background 0.2s;
      width: 100%;
      margin-top: 8px;
    }
    .btn:hover { background: var(--accent-hover); }
    .btn.secondary {
      background: #334155;
      color: white;
    }
    .btn.secondary:hover { background: #475569; }
    .btn-group { display: flex; gap: 8px; margin-top: 8px; }
    textarea, input, select {
      width: 100%;
      padding: 10px;
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 6px;
      color: white;
      margin-bottom: 10px;
      font-size: 0.9rem;
    }
    textarea { resize: vertical; min-height: 70px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85rem; }
    th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 600; }
    .status-pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: bold;
    }
    .status-pending { background: #3b82f6; color: white; }
    .status-produced { background: #10b981; color: white; }
    .status-published { background: #06b6d4; color: white; }
    pre {
      background: #0f172a;
      padding: 12px;
      border-radius: 8px;
      font-size: 0.8rem;
      overflow-x: auto;
      max-height: 220px;
    }
    .banner {
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 16px;
      display: none;
      font-weight: 600;
    }
    .banner.success { background: #065f46; color: #a7f3d0; display: block; }
    .banner.error { background: #991b1b; color: #fecaca; display: block; }
  </style>
</head>
<body>
  <header>
    <div>
      <span class="brand">DesiReels Studio</span>
      <span style="color: var(--muted); font-size: 0.9rem; margin-left: 8px;">Autonomous Indian Short-Video Creator</span>
    </div>
    <div style="display: flex; gap: 12px; align-items: center;">
      <span id="ist-clock" style="font-size: 0.9rem; color: var(--muted);"></span>
      <span class="badge dry-run">DRY_RUN: TRUE (Safe)</span>
    </div>
  </header>

  <div id="alert-banner" class="banner"></div>

  <div class="grid">
    <!-- Left Column: Video Review & Feedback -->
    <div>
      <div class="card">
        <div class="card-title">
          <span>Latest Generated Video</span>
          <span id="video-dur" style="font-size: 0.85rem; color: var(--muted);"></span>
        </div>
        <div class="video-container">
          <video id="player" controls playsinline loop>
            <source id="video-source" src="" type="video/mp4">
            Your browser does not support vertical MP4 video playback.
          </video>
        </div>
        <div id="video-title" style="font-weight: 700; margin-bottom: 6px;">No video loaded</div>
        <div id="video-topic" style="font-size: 0.85rem; color: var(--muted); margin-bottom: 12px;"></div>

        <form id="feedback-form" onsubmit="submitFeedback(event)">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
            <label style="font-size: 0.85rem; color: var(--muted);">Rating:</label>
            <select id="fb-rating" style="width: auto; margin-bottom: 0;">
              <option value="5">⭐⭐⭐⭐⭐ (5/5 Excellent)</option>
              <option value="4" selected>⭐⭐⭐⭐ (4/5 Good)</option>
              <option value="3">⭐⭐⭐ (3/5 Average)</option>
              <option value="2">⭐⭐ (2/5 Needs Work)</option>
              <option value="1">⭐ (1/5 Poor)</option>
            </select>
          </div>
          <textarea id="fb-critique" placeholder="Provide feedback (e.g., 'Subtitles were too low', 'Talking too fast in middle', 'Hook was amazing')"></textarea>
          <button type="submit" class="btn">Submit Feedback & Update AI Memory</button>
        </form>
      </div>

      <div class="card">
        <div class="card-title">Pipeline Actions</div>
        <button onclick="triggerPipeline(true)" class="btn secondary">⚡ Trigger Dry-Run Render Now</button>
        <button onclick="triggerLearner()" class="btn secondary" style="margin-top: 8px;">🔄 Analyze Reference Videos</button>
      </div>
    </div>

    <!-- Right Column: Topics, Memory & History -->
    <div>
      <div class="card">
        <div class="card-title">
          <span>Topic Queue & Seed Catalog</span>
          <span id="topic-count" style="font-size: 0.85rem; color: var(--muted);"></span>
        </div>
        <div style="max-height: 250px; overflow-y: auto;">
          <table id="topics-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Topic</th>
                <th>Region</th>
                <th>Category</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>

        <details style="margin-top: 14px;">
          <summary style="cursor: pointer; font-size: 0.85rem; color: var(--accent); font-weight: 600;">+ Add New Custom Topic</summary>
          <form id="add-topic-form" onsubmit="addTopic(event)" style="margin-top: 10px;">
            <input type="text" id="new-title" placeholder="Topic Title (e.g. Pune Bedekar Misal)" required>
            <input type="text" id="new-region" placeholder="Region (e.g. West India / Pune)" required>
            <select id="new-category">
              <option value="street_food">Street Food</option>
              <option value="culture">Culture & Lore</option>
              <option value="travel">Travel & Bazaars</option>
            </select>
            <textarea id="new-summary" placeholder="Verified factual summary (origin, history, stall name, authentic price)"></textarea>
            <button type="submit" class="btn">Add Topic to Queue</button>
          </form>
        </details>
      </div>

      <div class="card">
        <div class="card-title">Publishing & Platform Logs</div>
        <div style="max-height: 200px; overflow-y: auto;">
          <table id="publishing-table">
            <thead>
              <tr>
                <th>Video Title</th>
                <th>Platform</th>
                <th>Scheduled (IST)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Active AI Style Playbook</div>
        <pre><code id="playbook-json">Loading playbook...</code></pre>
      </div>
    </div>
  </div>

  <script>
    function updateClock() {
      const now = new Date();
      const options = { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
      document.getElementById('ist-clock').innerText = 'IST: ' + now.toLocaleTimeString('en-US', options);
    }
    setInterval(updateClock, 1000);
    updateClock();

    function showBanner(msg, isSuccess=true) {
      const banner = document.getElementById('alert-banner');
      banner.className = 'banner ' + (isSuccess ? 'success' : 'error');
      banner.innerText = msg;
      banner.style.display = 'block';
      setTimeout(() => { banner.style.display = 'none'; }, 5000);
    }

    async function fetchStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        // Video info
        if (data.latest_video) {
          const v = data.latest_video;
          document.getElementById('video-title').innerText = v.title;
          document.getElementById('video-topic').innerText = (v.region || '') + ' • ' + (v.category || '');
          document.getElementById('video-dur').innerText = v.duration_seconds + 's • Rendered in ' + v.render_time_seconds + 's';
          
          const filename = v.video_path.split('/').pop();
          const player = document.getElementById('player');
          const source = document.getElementById('video-source');
          source.src = '/output/' + filename;
          player.load();
        }

        // Topics Table
        const tb = document.querySelector('#topics-table tbody');
        tb.innerHTML = '';
        (data.topics || []).forEach(t => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${t.id}</td><td style="font-weight: 600;">${t.title}</td><td>${t.region}</td><td>${t.category}</td><td><span class="status-pill status-${t.status}">${t.status}</span></td>`;
          tb.appendChild(tr);
        });
        document.getElementById('topic-count').innerText = (data.topics || []).length + ' topics';

        // Publishing Table
        const pb = document.querySelector('#publishing-table tbody');
        pb.innerHTML = '';
        (data.publishing_history || []).forEach(p => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${p.video_title || 'Video #' + p.video_id}</td><td>${p.platform}</td><td>${p.scheduled_for_ist}</td><td><span class="status-pill status-${p.status}">${p.status}</span></td>`;
          pb.appendChild(tr);
        });

        // Playbook
        document.getElementById('playbook-json').innerText = JSON.stringify(data.playbook, null, 2);
      } catch (err) {
        console.error('Error fetching dashboard status:', err);
      }
    }

    async function submitFeedback(e) {
      e.preventDefault();
      const rating = parseInt(document.getElementById('fb-rating').value);
      const critique = document.getElementById('fb-critique').value;
      if (!critique.trim()) return;

      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, critique })
      });
      const data = await res.json();
      showBanner('Feedback applied! Updated parameters: ' + JSON.stringify(data.applied_changes));
      document.getElementById('fb-critique').value = '';
      fetchStatus();
    }

    async function addTopic(e) {
      e.preventDefault();
      const title = document.getElementById('new-title').value;
      const region = document.getElementById('new-region').value;
      const category = document.getElementById('new-category').value;
      const summary = document.getElementById('new-summary').value;

      const res = await fetch('/api/topics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, region, category, ground_truth_summary: summary })
      });
      const data = await res.json();
      showBanner('Topic added successfully!');
      document.getElementById('add-topic-form').reset();
      fetchStatus();
    }

    async function triggerPipeline(dryRun) {
      showBanner('Starting pipeline render... check terminal or wait a moment', true);
      const res = await fetch('/api/run-pipeline?dry_run=' + dryRun, { method: 'POST' });
      const data = await res.json();
      showBanner('Pipeline finished! Generated: ' + data.video_title);
      fetchStatus();
    }

    async function triggerLearner() {
      showBanner('Analyzing reference videos...', true);
      const res = await fetch('/api/run-learner', { method: 'POST' });
      const data = await res.json();
      showBanner('Learner analysis complete: ' + (data.message || data.status));
      fetchStatus();
    }

    fetchStatus();
  </script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP handler for local review dashboard."""

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
            return

        if path == "/api/status":
            latest_vid = db.get_latest_video()
            topics = db.list_topics(limit=50)
            pub_history = db.get_publishing_history(limit=10)
            playbook = learner_engine.load_playbook()

            data = {
                "latest_video": latest_vid,
                "topics": topics,
                "publishing_history": pub_history,
                "playbook": playbook,
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path.startswith("/output/"):
            filename = os.path.basename(path)
            file_path = OUTPUT_DIR / filename
            if file_path.is_file():
                mime, _ = mimetypes.guess_type(str(file_path))
                self.send_response(200)
                self.send_header("Content-Type", mime or "video/mp4")
                self.send_header("Content-Length", str(file_path.stat().st_size))
                self.end_headers()
                with open(file_path, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
                return

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/feedback":
            rating = int(payload.get("rating", 4))
            critique = payload.get("critique", "")
            video_id = payload.get("video_id")
            res = learner_engine.apply_human_feedback(rating, critique, video_id)
            self._send_json(res)
            return

        if path == "/api/topics":
            title = payload.get("title")
            region = payload.get("region")
            category = payload.get("category", "street_food")
            summary = payload.get("ground_truth_summary")
            if title and region:
                row_id = db.insert_topic(title, region, category, summary)
                self._send_json({"status": "success", "topic_id": row_id})
            else:
                self._send_json({"status": "error", "message": "Missing title or region"}, code=400)
            return

        if path == "/api/run-pipeline":
            # Run one pipeline generation cycle
            topic = db.get_next_pending_topic()
            if not topic:
                self._send_json({"status": "error", "message": "No pending topics"}, code=400)
                return

            grounded = research_engine.get_grounded_topic_data(topic)
            plan = script_planner.generate_plan(grounded)
            video_path = media_builder.build_video(topic, plan)

            self._send_json({
                "status": "success",
                "video_title": plan["title"],
                "video_file": video_path.name,
            })
            return

        if path == "/api/run-learner":
            res = learner_engine.analyze_reference_videos()
            self._send_json(res)
            return

        self.send_error(404, "Not Found")

    def _send_json(self, data: Dict[str, Any], code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        return  # Suppress default noisy console access log


def run_dashboard_server(host: str = "127.0.0.1", port: int = 8500) -> None:
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    logger.info(f"Dashboard running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping dashboard server...")
        server.server_close()


if __name__ == "__main__":
    run_dashboard_server()
