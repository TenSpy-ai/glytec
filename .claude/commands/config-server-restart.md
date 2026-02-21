# /config-server-restart Command

Restart the Config Server (stop then start).

## Usage

When the user types `/config-server-restart`:

1. Stop any running server on port 8099
2. Start fresh server
3. Open the browser

## Implementation

Execute the following:

```bash
echo "=== Restarting Config Server ==="
echo ""

PROJECT_DIR="/Users/oliviagao/project/glytec"
LOG_FILE="/tmp/config-server.log"

# Stop server
echo "Stopping server..."
if lsof -ti :8099 > /dev/null 2>&1; then
  lsof -ti :8099 | xargs kill -9 2>/dev/null
  echo "  Stopped Config Server"
else
  echo "  Config Server was not running"
fi

# Brief pause to ensure port is released
sleep 1

# Start server
echo ""
echo "Starting server..."
cd "$PROJECT_DIR/gtm-hello-world" && python config_server.py > "$LOG_FILE" 2>&1 &
sleep 2

# Verify server started
if ! lsof -i :8099 > /dev/null 2>&1; then
  echo ""
  echo "ERROR: Server failed to start. Check $LOG_FILE for details."
  exit 1
fi

# Open browser
open http://localhost:8099/tracker.html
echo ""
echo "Config Server restarted and opened in browser"
echo "Log: $LOG_FILE"
```

## Notes

- Useful after making changes to config_server.py or tracker.html
- Forces fresh server instance (doesn't reuse existing)
- Waits 1 second after stopping to ensure port is released
- Same behavior as running `/config-server-stop` then `/config-server`
