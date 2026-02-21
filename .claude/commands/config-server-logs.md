# /config-server-logs Command

Show recent logs from the Config Server.

## Usage

When the user types `/config-server-logs`:

1. Check if log file exists
2. Show the last 50 lines from the log file
3. Indicate if server is currently running

## Implementation

Execute the following:

```bash
echo "=== Config Server Logs ==="
echo ""

LOG_FILE="/tmp/config-server.log"
DB_FILE="/Users/oliviagao/project/glytec/gtm-hello-world/data/gtm_hello_world.db"

# Check server status
echo "Server Status:"
ERRORS=$(grep -ci "error" "$LOG_FILE" 2>/dev/null || echo "0")

if lsof -i :8099 > /dev/null 2>&1; then
  echo "  Config Server (8099): RUNNING ($ERRORS errors in log)"
else
  echo "  Config Server (8099): STOPPED ($ERRORS errors in log)"
fi

# Show DB info
echo ""
echo "GTM Hello World Database:"
if [ -f "$DB_FILE" ]; then
  CAMPAIGNS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM campaigns;" 2>/dev/null || echo "?")
  CONTACTS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM contacts;" 2>/dev/null || echo "?")
  ACCOUNTS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM accounts;" 2>/dev/null || echo "?")
  echo "  $DB_FILE"
  echo "  Accounts: $ACCOUNTS | Contacts: $CONTACTS | Campaigns: $CAMPAIGNS"
else
  echo "  No database found (run: cd gtm-hello-world && python seed_db.py)"
fi

echo ""
echo "=== Server Log ($LOG_FILE) ==="
if [ -f "$LOG_FILE" ]; then
  echo "(Last 50 lines)"
  tail -50 "$LOG_FILE"
else
  echo "(No log file found - server may not have been started with /config-server)"
fi

echo ""
echo "=== End of Logs ==="
echo "Tip: Use 'tail -f $LOG_FILE' to follow logs in real-time"
```

## Notes

- Shows last 50 lines from the log file
- Displays current server status (running/stopped)
- Shows GTM Hello World database stats (accounts, contacts, campaigns)
- Log file only exists if server was started via `/config-server`
- For real-time logs, use `tail -f /tmp/config-server.log`
