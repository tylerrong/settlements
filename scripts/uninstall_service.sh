#!/bin/bash
PLIST_NAME="com.settlements.monitor"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

launchctl unload "$PLIST_PATH" 2>/dev/null && echo "Service stopped." || echo "Service was not running."
rm -f "$PLIST_PATH" && echo "Plist removed."
echo "Settlement Monitor service uninstalled."
