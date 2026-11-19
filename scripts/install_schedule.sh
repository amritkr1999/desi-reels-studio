#!/usr/bin/env bash
# ==============================================================================
# DesiReels Studio — macOS launchd Scheduler Installer
# Schedules once-daily autonomous execution ahead of prime IST evening window.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_LABEL="com.desireels.studio"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
RUNNER_SCRIPT="$PROJECT_ROOT/scripts/daily_run.sh"
LOGS_DIR="$PROJECT_ROOT/logs"

mkdir -p "$HOME/Library/LaunchAgents" "$LOGS_DIR"

echo "⚙️  Configuring macOS LaunchAgent for DesiReels Studio..."

cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${RUNNER_SCRIPT}</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${PROJECT_ROOT}</string>

    <!-- Schedule: Runs once daily at 18:00 (6:00 PM IST) ahead of evening peak -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>${LOGS_DIR}/launchd_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${LOGS_DIR}/launchd_stderr.log</string>

    <!-- Do not run immediately upon loading; wait for calendar trigger -->
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

echo "✅ Created LaunchAgent property list at:"
echo "   $PLIST_PATH"

echo ""
echo "------------------------------------------------------------------------------"
echo "To activate the daily 18:00 IST schedule, run:"
echo "   launchctl unload \"$PLIST_PATH\" 2>/dev/null || true"
echo "   launchctl load \"$PLIST_PATH\""
echo ""
echo "To test an immediate manual run via launchd:"
echo "   launchctl start ${PLIST_LABEL}"
echo ""
echo "To inspect recent execution logs:"
echo "   tail -f \"$LOGS_DIR/daily_run.log\""
echo "------------------------------------------------------------------------------"
