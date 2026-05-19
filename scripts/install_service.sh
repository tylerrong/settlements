#!/bin/bash
# Installs Settlement Monitor as a macOS LaunchAgent.
# It will start automatically at login and restart if it crashes.
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
PLIST_NAME="com.settlements.monitor"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LOG_DIR="$PROJECT_DIR/logs"

# Sanity checks
if [ ! -f "$VENV_PYTHON" ]; then
  echo "Error: venv not found. Run 'bash scripts/setup.sh' first."
  exit 1
fi
if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo "Error: .env file missing. Copy .env.example and fill in your keys."
  exit 1
fi

mkdir -p "$LOG_DIR"

# Write the plist
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$PLIST_NAME</string>

  <key>ProgramArguments</key>
  <array>
    <string>$VENV_PYTHON</string>
    <string>$PROJECT_DIR/main.py</string>
    <string>daemon</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$PROJECT_DIR</string>

  <!-- Restart automatically if it exits for any reason -->
  <key>KeepAlive</key>
  <true/>

  <!-- Start immediately when launchd loads (login / boot) -->
  <key>RunAtLoad</key>
  <true/>

  <!-- Throttle restarts: wait 30s before restarting after a crash -->
  <key>ThrottleInterval</key>
  <integer>30</integer>

  <key>StandardOutPath</key>
  <string>$LOG_DIR/monitor.log</string>

  <key>StandardErrorPath</key>
  <string>$LOG_DIR/monitor.err</string>

  <!-- Pass the project dir as an env var so relative paths work -->
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>$HOME</string>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
</dict>
</plist>
EOF

echo "Wrote $PLIST_PATH"

# Unload if already running, then load fresh
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo ""
echo "✓ Settlement Monitor is now running as a background service."
echo ""
echo "Logs:          tail -f $LOG_DIR/monitor.log"
echo "Stop service:  launchctl unload $PLIST_PATH"
echo "Start service: launchctl load $PLIST_PATH"
echo "Uninstall:     bash scripts/uninstall_service.sh"
