# Logging, Deck Parsing, and Debugging Implementation

## Overview

This document describes the new logging infrastructure, enhanced deck parsing from MarvelCDB, and debugging capabilities added to the Marvel Champions server.

## Logging Service

### Features

The new `logging_service.py` provides a comprehensive logging solution with:

1. **Multiple Verbosity Levels**
   - `DEBUG` (10) - Detailed diagnostic information
   - `INFO` (20) - General informational messages (default)
   - `WARNING` (30) - Warning messages
   - `ERROR` (40) - Error messages
   - `CRITICAL` (50) - Critical errors

2. **Multiple Output Backends**
   - **Console**: Real-time output with colors
   - **File**: Rolling log files in `logs/` directory with session timestamps
   - **MongoDB**: Automatic persistence to database on shutdown

3. **Structured Logging**
   - All logs include timestamp, level, app name, message
   - Support for additional context via kwargs
   - Session ID for grouping related logs

### Usage

#### Initialize Logger

```python
from logging_service import initialize_logger, LogLevel

# Initialize at application startup
logger = initialize_logger(
    app_name="marvel-champions",
    verbosity=LogLevel.INFO,
    log_dir="logs",
    mongo_connection="mongodb://localhost:27017",
    mongo_database="marvel_champions",
    mongo_collection="logs"
)
```

#### Log Messages

```python
logger.debug("Detailed diagnostic info")
logger.info("General information")
logger.warning("Something unexpected happened")
logger.error("An error occurred")
logger.critical("Critical failure")

# With context
logger.info("Player joined", player_id="p123", room_id="abc456")
```

#### Retrieve Logs

```python
# Get recent 100 logs from MongoDB
recent_logs = logger.get_recent_logs(limit=100)

# Get specific level logs
error_logs = logger.get_recent_logs(limit=50, level="ERROR")

# Get session ID for tracking
session_id = logger.get_session_id()
```

### Configuration

Control logging verbosity via environment variable:

```bash
# Set verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=DEBUG
python app.py

# Defaults to INFO if not set
python app.py
```

### Log File Location

Logs are stored in `logs/` directory with naming pattern:
```
logs/marvel-champions_20260111_143022.log
```

Each server instance has a unique session ID (timestamp-based).

### MongoDB Persistence

On server shutdown:
1. All buffered logs are automatically written to MongoDB
2. Collection: `marvel_champions.logs`
3. Documents include:
   - `timestamp`: UTC timestamp
   - `session_id`: Session identifier
   - `level`: Log level (DEBUG, INFO, WARNING, etc.)
   - `message`: Log message
   - `app_name`: Application name
   - Additional context fields

Query logs in MongoDB:

```javascript
// Find all ERROR logs from a session
db.logs.find({ session_id: "20260111_143022", level: "ERROR" })

// Find recent logs across all sessions
db.logs.find().sort({ timestamp: -1 }).limit(100)

// Analyze log levels
db.logs.aggregate([
  { $group: { _id: "$level", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

## Enhanced Deck Parsing

### Problem Solved

MarvelCDB may return either JSON or HTML responses, and the deck format can vary. The updated `MarvelCDBClient` now handles:

1. **JSON API responses** (primary path)
2. **HTML responses** (fallback with parsing)
3. **Multiple endpoint variations** (pack name vs pack code)

### Implementation

The `gateways/marvelcdb_client.py` now includes:

#### `_parse_html_response(html: str) -> Dict`

Parses HTML responses using BeautifulSoup:

1. **First attempt**: Look for JSON data embedded in `<script type="application/json">` tags
2. **Fallback**: Extract structured markup from HTML (title, card divs)
3. **Result**: Returns dict with `cards` list and metadata

#### Updated `get_decks()` Method

```python
# Try API endpoint first (JSON)
response = requests.get(f"{base_url}/api/public/decklist/{deck_id}")
# If JSON, return directly
# If HTML, parse and extract cards

# Fallback: Try HTML deck page if API fails
response = requests.get(f"{base_url}/decklist/{deck_id}")
# Parse HTML and extract deck data
```

#### Updated `get_cards()` Method

Similar logic for card retrieval with JSON primary path and HTML fallback.

### Returned Deck Format

```python
{
  "name": "Deck Name",
  "cards": [
    {
      "name": "Card Name",
      "quantity": 2,
      "card_id": "01001",
      # ... other fields
    },
    # ...
  ],
  "parsed_from_html": False  # True if HTML was parsed instead of JSON
}
```

### Error Handling

- Graceful degradation: HTML parsing used only when JSON fails
- All exceptions logged with context
- Client receives descriptive error messages

## Server Logging Integration

All major server operations now log with appropriate levels:

### INFO Level (User-Facing Events)
```
Creating lobby: room_id=abc123, host=Alice
Player joining lobby abc123: player_id=p001, name=Bob
Setting encounter for lobby abc123: module=core
Player p001 in lobby abc123 set ready=True
Starting game in lobby abc123 with 2 players
Successfully fetched deck 12345 with 54 cards
Successfully fetched module rise-and-fall with 78 cards
```

### DEBUG Level (Diagnostic Info)
```
Health check endpoint called
Root (index) endpoint called
Fetching lobby: abc123
Flask app configured successfully
Socket abc123-xyz joining room: abc123
Socket leaving room: abc123
Lobby abc123 inserted into MongoDB
Player p001 added to MongoDB lobby abc123
```

### WARNING Level (Issues)
```
MongoDB connection failed, using in-memory storage
Lobby not found: invalid123
Join attempt on non-existent lobby: invalid123
Set encounter on non-existent lobby: invalid123
Failed to emit lobby_update for abc123: timeout
```

### ERROR Level (Failures)
```
Could not initialize repositories: connection refused
Failed to fetch deck 99999: HTTP 404
Failed to fetch module invalid_module: invalid response
```

## Usage Example

### Running with Different Log Levels

```bash
# Production: Only warnings and errors
export LOG_LEVEL=WARNING
python app.py

# Development: All messages including debug
export LOG_LEVEL=DEBUG
python app.py

# Standard operation: Info and above
python app.py  # Defaults to INFO
```

### Monitoring Logs

**In Terminal:**
```bash
# Monitor real-time logs
tail -f logs/marvel-champions_*.log

# Filter for errors
grep ERROR logs/marvel-champions_*.log

# Count events
grep "Starting game" logs/marvel-champions_*.log | wc -l
```

**In MongoDB:**
```bash
# Connect to MongoDB shell
mongo

# Query logs
use marvel_champions
db.logs.find({ level: "ERROR" }).pretty()

# Analyze session performance
db.logs.aggregate([
  { $match: { session_id: "20260111_143022" } },
  { $group: { _id: "$level", count: { $sum: 1 } } },
  { $sort: { _id: 1 } }
])
```

## Benefits

1. **Debuggability**: Comprehensive logging makes troubleshooting easier
2. **Auditability**: All server actions logged with timestamps
3. **Resilience**: Deck parsing handles multiple response formats
4. **Redundancy**: Logs backed up in both files and MongoDB
5. **Flexibility**: Verbosity levels for different environments
6. **Performance**: Buffered MongoDB writes on shutdown (no blocking)

## Files Modified

- `app.py` - Integrated logging throughout server
- `logging_service.py` - New comprehensive logging module
- `gateways/marvelcdb_client.py` - Enhanced with HTML parsing and better error handling
