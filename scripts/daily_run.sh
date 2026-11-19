#!/usr/bin/env bash
# ==============================================================================
# DesiReels Studio — Master Daily Autonomous Runner
# Invoked once daily ahead of peak Indian evening window (18:00 IST).
# ==============================================================================
set -euo pipefail

# Ensure Homebrew and standard Apple Silicon paths are loaded
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOGS_DIR"
cd "$PROJECT_ROOT"

# Activate local python environment if present
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Starting daily short video generation cycle..." >> "$LOGS_DIR/daily_run.log"

# Run the master python pipeline
python3 -m src.orchestrator >> "$LOGS_DIR/daily_run.log" 2>&1

# Run cache cleanup
"$SCRIPT_DIR/cleanup.sh" >> "$LOGS_DIR/daily_run.log" 2>&1

# Send macOS desktop notification
if command -v osascript &>/dev/null; then
    osascript -e 'display notification "Your daily 30s Indian street food short is rendered and ready for review at http://localhost:8500!" with title "DesiReels Studio" sound name "Glass"' 2>/dev/null || true
fi

echo "[$TIMESTAMP] Daily run completed successfully." >> "$LOGS_DIR/daily_run.log"
