# OpenAPI / Swagger Documentation

## Overview

This project uses **OpenAPI 3.0.0** specification to document the REST API. The complete specification is in `openapi.yaml`.

## Accessing the Documentation

### Option 1: Swagger UI (Recommended)

Interactive API documentation with "Try It Out" functionality.

```bash
# Install Swagger UI dependencies
pip install flask-cors flasgger

# Start the server
python app.py

# Access at: http://localhost:5000/api/docs
```

### Option 2: ReDoc

Alternative documentation viewer (read-only, cleaner design).

```
http://localhost:5000/api/redoc
```

### Option 3: OpenAPI YAML

Raw OpenAPI specification:

```
http://localhost:5000/openapi.yaml
```

## API Structure

### Base URL
- Development: `http://localhost:5000`
- Production: `https://api.marvelchampions.example.com`

### Authentication
Currently, the API has **no authentication**. Future versions may add:
- API keys
- JWT tokens
- OAuth 2.0

### Content Type
All requests use `application/json` (except image downloads).

## API Sections

### 1. Cards API
**Base path**: `/api/cards`

Managing card data from MarvelCDB:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/{code}` | Get card by code |
| GET | `/search?q=...` | Search cards by name |
| POST | `/import` | Import single card |
| POST | `/import/bulk` | Import multiple cards |
| GET | `/{code}/image` | Get card image |

**Example: Import a card**
```bash
curl -X POST http://localhost:5000/api/cards/import \
  -H "Content-Type: application/json" \
  -d '{"code": "01001a"}'
```

### 2. Decks API
**Base path**: `/api/decks`

Managing deck compositions:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `` | List all decks |
| POST | `` | Create new deck |
| GET | `/{deck_id}` | Get deck details |
| PUT | `/{deck_id}` | Update deck |
| DELETE | `/{deck_id}` | Delete deck |
| GET | `/{deck_id}/cards` | Get deck with card details |
| POST | `/import` | Import from MarvelCDB |
| GET | `/marvelcdb/mine` | Get user's MarvelCDB decks |

**Example: Create a deck**
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

### 3. Games API
**Base path**: `/api/games`

Managing game sessions and actions:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `` | List all games |
| POST | `` | Create new game |
| GET | `/recent` | Get recent games |
| GET | `/{game_id}` | Get game state |
| DELETE | `/{game_id}` | Delete game |
| POST | `/{game_id}/draw` | Draw card |
| POST | `/{game_id}/shuffle` | Shuffle discard |
| POST | `/{game_id}/play` | Play card |
| POST | `/{game_id}/move` | Move card |
| POST | `/{game_id}/rotate` | Toggle rotation |
| POST | `/{game_id}/counter` | Add counter |

**Example: Create a game**
```bash
curl -X POST http://localhost:5000/api/games \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice vs Bob",
    "deck_ids": ["deck1", "deck2"],
    "player_names": ["Alice", "Bob"]
  }'
```

**Example: Draw a card**
```bash
curl -X POST http://localhost:5000/api/games/{game_id}/draw \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice"}'
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response
```json
{
  "error": "Error message describing what went wrong"
}
```

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

## Key Concepts

### No Rules Enforcement
The API **does not validate game rules**. This means:
- ✅ You can play cards without resources
- ✅ You can draw from an empty deck (returns no change)
- ✅ You can move non-existent cards
- ✅ You can add any counter type

**Why?** Different game variants have different rules. The UI or players enforce the rules.

### Immutability
All game operations return the complete updated **Game** entity. This means:
- All changes are included in response
- Safe for concurrent access
- Easy to implement undo/redo

### Cards vs Card Codes
The API primarily works with **card codes** (e.g., "01001a"):
- Card operations return full **Card** objects (with name, text)
- Deck operations use **card codes** (lightweight references)
- Game operations store **card codes** in player zones
- Call `/api/decks/{id}/cards` to get full card details

## Workflow Examples

### Example 1: Import and Play

```bash
# 1. Import a card
curl -X POST http://localhost:5000/api/cards/import \
  -H "Content-Type: application/json" \
  -d '{"code": "01001a"}'

# 2. Create deck with that card
curl -X POST http://localhost:5000/api/decks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Deck",
    "cards": [{"code": "01001a", "quantity": 2}]
  }'

# Response contains deck_id, store it

# 3. Create game with deck
curl -X POST http://localhost:5000/api/games \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Game",
    "deck_ids": ["<deck_id>"],
    "player_names": ["Alice"]
  }'

# Response contains game_id, store it

# 4. Draw card
curl -X POST http://localhost:5000/api/games/<game_id>/draw \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice"}'

# 5. Play card
curl -X POST http://localhost:5000/api/games/<game_id>/play \
  -H "Content-Type: application/json" \
  -d '{
    "player_name": "Alice",
    "card_code": "01001a",
    "position": {"x": 0, "y": 0}
  }'

# 6. Add damage counter
curl -X POST http://localhost:5000/api/games/<game_id>/counter \
  -H "Content-Type: application/json" \
  -d '{
    "card_code": "01001a",
    "counter_type": "damage",
    "amount": 3
  }'
```

### Example 2: Search and Import

```bash
# 1. Search for cards
curl -X GET 'http://localhost:5000/api/cards/search?q=Spider'

# 2. Bulk import results
curl -X POST http://localhost:5000/api/cards/import/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "codes": ["01001a", "01002b", "01003c"]
  }'
```

## Integration with Swagger UI

### Installation

```bash
pip install flask-cors flasgger
```

### Configuration

The `app.py` can be updated to serve Swagger UI:

```python
from flasgger import Swagger

swagger = Swagger(app, template={
    'swagger': '3.0.0',
    'info': {'title': 'Marvel Champions API'},
    'servers': [{'url': 'http://localhost:5000'}]
})
```

### Access Points

- **Swagger UI**: `http://localhost:5000/apidocs`
- **Swagger JSON**: `http://localhost:5000/swagger.json`

## Validating the OpenAPI Spec

```bash
# Using Swagger CLI
npx swagger-cli validate openapi.yaml

# Using OpenAPI validation tools
pip install openapi-spec-validator
python -m openapi_spec_validator openapi.yaml
```

## Documentation Best Practices

### When Adding New Endpoints

1. Add path to `openapi.yaml`
2. Include description and operationId
3. Document all parameters
4. Show example request/response
5. List all possible status codes
6. Add to this README

### Keeping Documentation in Sync

- Review `openapi.yaml` before pulling
- Update `openapi.yaml` when changing endpoints
- Validate with tools before committing
- Update examples in README

## Troubleshooting

### Missing Endpoints in Swagger?

1. Check `openapi.yaml` has path entry
2. Verify operationId is unique
3. Confirm requestBody schema is valid
4. Reload Swagger UI (hard refresh browser cache)

### Can't Connect to API?

1. Verify `servers` section in `openapi.yaml`
2. Ensure Flask app is running
3. Check CORS is enabled for your domain
4. Look for network errors in browser console

### Responses Don't Match Schema?

1. Check response code (200, 201, 400, etc)
2. Verify response has correct schema
3. Run actual request in Swagger UI
4. Compare actual vs documented response

## Resources

- [OpenAPI 3.0 Spec](https://spec.openapis.org/oas/v3.0.3)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://redoc.ly/)
- [OpenAPI Tools](https://openapi.tools/)

## Next Steps

1. ✅ Validate OpenAPI spec
2. ✅ Test all endpoints in Swagger UI
3. ✅ Generate client SDKs (if needed)
4. ✅ Add authentication (if needed)
5. ✅ Set up API versioning (if needed)
