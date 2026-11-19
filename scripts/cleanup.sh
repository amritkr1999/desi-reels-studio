#!/usr/bin/env bash
# ==============================================================================
# DesiReels Studio — Temporary Cache & Artifact Cleanup Script
# Preserves internal SSD storage on MacBook Air M5.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMP_DIR="$PROJECT_ROOT/temp"

echo "🧹 [DesiReels Cleanup] Starting garbage collection in $TEMP_DIR..."

if [ -d "$TEMP_DIR" ]; then
    # Remove temporary wav slices, png backdrops, and ass subtitles
    find "$TEMP_DIR" -type f \( -name "*.wav" -o -name "*.aiff" -o -name "*.png" -o -name "*.jpg" -o -name "*.ass" -o -name "*.srt" -o -name "*.txt" \) ! -name ".gitkeep" -delete
    echo "✅ [DesiReels Cleanup] Temporary video slices and audio caches purged."
fi

# Rotate logs if larger than 10MB
LOG_FILE="$PROJECT_ROOT/logs/daily_run.log"
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]; then
    mv "$LOG_FILE" "$LOG_FILE.old"
    echo "✅ [DesiReels Cleanup] Rotated daily_run.log."
fi

echo "✨ [DesiReels Cleanup] Storage optimization complete."
