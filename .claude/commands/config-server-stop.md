# /config-server-stop Command

Stop the Config Server background process.

## Usage

When the user types `/config-server-stop`:

1. Kill any process running on port 8099
2. Confirm what was stopped

## Implementation

Execute the following:

```bash
echo "Stopping Config Server..."

# Kill server (port 8099)
if lsof -ti :8099 > /dev/null 2>&1; then
  lsof -ti :8099 | xargs kill -9 2>/dev/null
  echo "Stopped Config Server"
else
  echo "Config Server was not running"
fi

echo ""
echo "Done. Use /config-server to start server again."
```

## Notes

- Safe to run even if server isn't running
- Uses `kill -9` to ensure process stops
- Does not affect other processes on different ports
