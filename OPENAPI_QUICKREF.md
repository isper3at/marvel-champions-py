# OpenAPI Documentation - Quick Reference

## 📋 OpenAPI Specification

**File**: `openapi.yaml`
**Version**: OpenAPI 3.0.0
**Title**: Marvel Champions Game API
**Endpoints**: 20+ REST endpoints

## 🚀 Quick Start

### View Documentation

```bash
# Option 1: Swagger UI (Interactive)
http://localhost:5000/api/docs

# Option 2: ReDoc (Read-only)
http://localhost:5000/api/redoc

# Option 3: Raw OpenAPI Spec
http://localhost:5000/openapi.yaml

# Option 4: Health Check
http://localhost:5000/api/health
```

### Run Locally

```bash
# Start Flask app
python app.py

# Open browser to http://localhost:5000/api/docs
```

## 📚 API Endpoints by Category

### Cards (5 endpoints)
- `GET /api/cards/{code}` - Get card by code
- `GET /api/cards/search?q=...` - Search by name
- `POST /api/cards/import` - Import single card
- `POST /api/cards/import/bulk` - Import multiple
- `GET /api/cards/{code}/image` - Get image

### Decks (8 endpoints)
- `GET /api/decks` - List all
- `POST /api/decks` - Create new
- `GET /api/decks/{id}` - Get deck
- `PUT /api/decks/{id}` - Update
- `DELETE /api/decks/{id}` - Delete
- `GET /api/decks/{id}/cards` - With details
- `POST /api/decks/import` - From MarvelCDB
- `GET /api/decks/marvelcdb/mine` - User's decks

### Games (10 endpoints)
- `GET /api/games` - List all
- `POST /api/games` - Create new
- `GET /api/games/recent` - Recent games
- `GET /api/games/{id}` - Get state
- `DELETE /api/games/{id}` - Delete
- `POST /api/games/{id}/draw` - Draw card
- `POST /api/games/{id}/shuffle` - Shuffle discard
- `POST /api/games/{id}/play` - Play card
- `POST /api/games/{id}/move` - Move card
- `POST /api/games/{id}/rotate` - Toggle rotation
- `POST /api/games/{id}/counter` - Add counter

### Health
- `GET /api/health` - Status check

## 📝 Request/Response Examples

### Example 1: Import Card

```bash
curl -X POST http://localhost:5000/api/cards/import \
  -H "Content-Type: application/json" \
  -d '{"code": "01001a"}'
```

**Response (201)**:
```json
{
  "success": true,
  "card": {
    "code": "01001a",
    "name": "Spider-Man",
    "text": "Hero - Can spend [1 resource], flip to alter ego"
  }
}
```

### Example 2: Create Deck

```bash
curl -X POST http://localhost:5000/api/decks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spider-Man Control",
    "cards": [
      {"code": "01001a", "quantity": 2},
      {"code": "01002b", "quantity": 1}
    ]
  }'
```

**Response (201)**:
```json
{
  "success": true,
  "deck": {
    "id": "deck_123",
    "name": "Spider-Man Control",
    "card_count": 3,
    "created_at": "2026-01-13T12:00:00"
  }
}
```

### Example 3: Create Game

```bash
curl -X POST http://localhost:5000/api/games \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice vs Bob",
    "deck_ids": ["deck_123", "deck_456"],
    "player_names": ["Alice", "Bob"]
  }'
```

**Response (201)**:
```json
{
  "success": true,
  "game": {
    "id": "game_789",
    "name": "Alice vs Bob",
    "players": ["Alice", "Bob"],
    "created_at": "2026-01-13T12:00:00"
  }
}
```

### Example 4: Draw Card

```bash
curl -X POST http://localhost:5000/api/games/game_789/draw \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice"}'
```

**Response (200)**:
```json
{
  "success": true,
  "game": {
    "id": "game_789",
    "state": {
      "players": [
        {
          "player_name": "Alice",
          "deck": ["01001b", "01001c"],
          "hand": ["01001a"],
          "discard": [],
          "removed": []
        }
      ],
      "play_area": []
    }
  }
}
```

## 🔄 Complete Game Flow

```
1. Import Cards
   POST /api/cards/import/bulk {"codes": ["01001a", "01002b"]}

2. Create Deck
   POST /api/decks {"name": "Deck", "cards": [...]}

3. Create Game
   POST /api/games {
     "name": "Game1",
     "deck_ids": ["deck1", "deck2"],
     "player_names": ["Alice", "Bob"]
   }

4. Draw Cards
   POST /api/games/{game_id}/draw {"player_name": "Alice"}

5. Play Cards
   POST /api/games/{game_id}/play {
     "player_name": "Alice",
     "card_code": "01001a",
     "position": {"x": 0, "y": 0}
   }

6. Add Counters
   POST /api/games/{game_id}/counter {
     "card_code": "01001a",
     "counter_type": "damage",
     "amount": 3
   }
```

## 🔑 Key Features

### No Rules Enforcement
- Backend manages state only
- UI enforces game rules
- Any move is allowed (if it doesn't crash)

### Immutability
- All operations return complete updated entity
- Safe for concurrent access
- Easy to implement undo/redo

### Generic Counters
- Add any counter type (damage, threat, tokens)
- Application-defined meanings
- No code changes needed for new types

### Idempotent Operations
- Multiple imports of same card = safe
- Deck creation is repeatable
- Game actions are reliable

## 📊 Status Codes

| Code | Meaning | Use |
|------|---------|-----|
| 200 | OK | Successful GET/POST/PUT |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input or missing fields |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Unexpected error |

## 📦 Data Schemas

### Card
```json
{
  "code": "01001a",
  "name": "Spider-Man",
  "text": "Hero - Can spend [1 resource]..."
}
```

### DeckCard
```json
{
  "code": "01001a",
  "quantity": 2
}
```

### Position
```json
{
  "x": 1,
  "y": 2
}
```

### CardInPlay
```json
{
  "code": "01001a",
  "position": {"x": 1, "y": 2},
  "rotated": false,
  "flipped": false,
  "counters": {"damage": 3, "threat": 1}
}
```

### PlayerZones
```json
{
  "player_name": "Alice",
  "deck": ["01001a", "01001b"],
  "hand": ["01001c"],
  "discard": [],
  "removed": []
}
```

## 🛠️ Testing Tools

### Browser
```
http://localhost:5000/api/docs
```

### cURL
```bash
curl -X GET http://localhost:5000/api/cards/01001a
```

### Postman
- Import: `http://localhost:5000/openapi.yaml`
- Use "Try It Out" in collection

### Python
```python
import requests

response = requests.get('http://localhost:5000/api/cards/01001a')
print(response.json())
```

### JavaScript
```javascript
const client = new MarvelChampionsClient('http://localhost:5000');
const card = await client.getCard('01001a');
```

## 📖 Documentation Files

- **openapi.yaml** - OpenAPI specification
- **OPENAPI_GUIDE.md** - Detailed usage guide
- **SWAGGER_SETUP.md** - Setup and configuration
- **DEVELOPER_GUIDE.md** - Architecture and patterns

## 🔗 Resources

- [OpenAPI 3.0 Spec](https://spec.openapis.org/oas/v3.0.3)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://redoc.ly/)
- [cURL Docs](https://curl.se/docs/manpage.html)

## ⚡ Pro Tips

1. **Use Swagger UI for testing** - Try endpoints interactively
2. **Copy cURL from Swagger** - Use "Generate Client" feature
3. **Validate requests before sending** - Check required fields
4. **Monitor response times** - Use browser dev tools
5. **Test with real IDs** - Use actual deck/game IDs
6. **Cache card imports** - Import once, use many times
7. **Use bulk import** - Faster than importing one by one

## 🐛 Common Issues

### 404 Card Not Found
**Solution**: Import card first with `POST /api/cards/import`

### 400 Bad Request
**Solution**: Check required fields in request body

### Can't See Changes
**Solution**: Game state returned in response, reload from API

### Deck Cards Empty
**Solution**: Create deck with proper format: `[{"code": "...", "quantity": 2}]`

## 📞 Support

- Check `OPENAPI_GUIDE.md` for detailed docs
- Review `openapi.yaml` for schema details
- Look at examples in this file
- Use Swagger UI "Try It Out" for testing

---

**Last Updated**: January 13, 2026
**Version**: 1.0.0
**Status**: ✅ Complete
