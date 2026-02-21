# /config-server Command

Start the Config Server (if needed) and open the tracker UI in your browser.

## Usage

When the user types `/config-server`:

1. Check if the server (port 8099) is running
2. If not running, start it in the background
3. Open the browser to http://localhost:8099/tracker.html

## Implementation

Execute the following:

```bash
PROJECT_DIR="/Users/oliviagao/project/glytec"
LOG_FILE="/tmp/config-server.log"

# Check and start server if needed
if ! lsof -i :8099 > /dev/null 2>&1; then
  echo "Starting Config Server on port 8099..."
  cd "$PROJECT_DIR/gtm-hello-world" && python config_server.py > "$LOG_FILE" 2>&1 &
  sleep 2
fi

# Verify server started
if ! lsof -i :8099 > /dev/null 2>&1; then
  echo "ERROR: Server failed to start. Check $LOG_FILE for details."
  exit 1
fi

# Open browser
open http://localhost:8099/tracker.html
echo "Config Server opened in browser"
echo ""
echo "Server running in background. Use /config-server-stop to stop."
echo "  Tracker:    http://localhost:8099/tracker.html"
echo "  Config API: http://localhost:8099/config"
echo "  Log:        $LOG_FILE"
```

## Notes

- Server runs in background — use `/config-server-stop` to stop it
- Logs are written to `/tmp/config-server.log`
- Server persists until stopped or Mac restarts
- Serves tracker.html with campaign tracker, docs, and Config editor
- Config tab lets you edit config.py constants (DRY_RUN, thresholds) from the browser
