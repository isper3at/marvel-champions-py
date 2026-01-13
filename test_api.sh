#!/bin/bash
# test_api.sh - Test all API endpoints

set -e

BASE_URL="http://localhost:5000"

echo "=========================================="
echo "Marvel Champions API Tests"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -n "Testing $name... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗${NC} (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
}

echo "1. Testing root endpoint..."
test_endpoint "Root" "GET" "/"

echo ""
echo "2. Testing health check..."
test_endpoint "Health" "GET" "/health"

echo ""
echo "=========================================="
echo "Card Endpoints"
echo "=========================================="

echo ""
echo "3. Importing a card..."
test_endpoint "Import Card" "POST" "/api/cards/import" '{"code": "test001"}'

echo ""
echo "4. Getting card by code..."
test_endpoint "Get Card" "GET" "/api/cards/test001"

echo ""
echo "5. Searching cards..."
test_endpoint "Search Cards" "GET" "/api/cards/search?q=test"

echo ""
echo "6. Bulk importing cards..."
test_endpoint "Bulk Import" "POST" "/api/cards/import/bulk" \
    '{"codes": ["test001", "test002", "test003"]}'

echo ""
echo "=========================================="
echo "Deck Endpoints"
echo "=========================================="

echo ""
echo "7. Creating a deck..."
DECK_RESPONSE=$(curl -s "$BASE_URL/api/decks" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Deck",
        "cards": [
            {"code": "test001", "quantity": 1},
            {"code": "test002", "quantity": 3}
        ]
    }')

DECK_ID=$(echo "$DECK_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$DECK_ID" ]; then
    echo -e "${GREEN}✓${NC} Created deck: $DECK_ID"
else
    echo -e "${RED}✗${NC} Failed to create deck"
    echo "Response: $DECK_RESPONSE"
    exit 1
fi

echo ""
echo "8. Listing all decks..."
test_endpoint "List Decks" "GET" "/api/decks"

echo ""
echo "9. Getting deck by ID..."
test_endpoint "Get Deck" "GET" "/api/decks/$DECK_ID"

echo ""
echo "10. Getting deck with cards..."
test_endpoint "Get Deck Cards" "GET" "/api/decks/$DECK_ID/cards"

echo ""
echo "11. Updating deck..."
test_endpoint "Update Deck" "PUT" "/api/decks/$DECK_ID" \
    '{"name": "Updated Test Deck"}'

echo ""
echo "=========================================="
echo "Game Endpoints"
echo "=========================================="

echo ""
echo "12. Creating a game..."
GAME_RESPONSE=$(curl -s "$BASE_URL/api/games" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Test Game\",
        \"deck_ids\": [\"$DECK_ID\"],
        \"player_names\": [\"Alice\"]
    }")

GAME_ID=$(echo "$GAME_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$GAME_ID" ]; then
    echo -e "${GREEN}✓${NC} Created game: $GAME_ID"
else
    echo -e "${RED}✗${NC} Failed to create game"
    echo "Response: $GAME_RESPONSE"
    exit 1
fi

echo ""
echo "13. Listing all games..."
test_endpoint "List Games" "GET" "/api/games"

echo ""
echo "14. Getting recent games..."
test_endpoint "Recent Games" "GET" "/api/games/recent?limit=5"

echo ""
echo "15. Getting game state..."
test_endpoint "Get Game" "GET" "/api/games/$GAME_ID"

echo ""
echo "16. Drawing a card..."
test_endpoint "Draw Card" "POST" "/api/games/$GAME_ID/draw" \
    '{"player_name": "Alice"}'

echo ""
echo "17. Playing card to table..."
test_endpoint "Play Card" "POST" "/api/games/$GAME_ID/play" \
    '{
        "player_name": "Alice",
        "card_code": "test001",
        "x": 100,
        "y": 200
    }'

echo ""
echo "18. Moving card on table..."
test_endpoint "Move Card" "POST" "/api/games/$GAME_ID/move" \
    '{
        "card_code": "test001",
        "x": 150,
        "y": 250
    }'

echo ""
echo "19. Rotating card..."
test_endpoint "Rotate Card" "POST" "/api/games/$GAME_ID/rotate" \
    '{"card_code": "test001"}'

echo ""
echo "20. Adding counter..."
test_endpoint "Add Counter" "POST" "/api/games/$GAME_ID/counter" \
    '{
        "card_code": "test001",
        "counter_type": "damage",
        "amount": 3
    }'

echo ""
echo "21. Shuffling discard into deck..."
test_endpoint "Shuffle Deck" "POST" "/api/games/$GAME_ID/shuffle" \
    '{"player_name": "Alice"}'

echo ""
echo "=========================================="
echo "Cleanup"
echo "=========================================="

echo ""
echo "22. Deleting game..."
test_endpoint "Delete Game" "DELETE" "/api/games/$GAME_ID"

echo ""
echo "23. Deleting deck..."
test_endpoint "Delete Deck" "DELETE" "/api/decks/$DECK_ID"

echo ""
echo "=========================================="
echo -e "${GREEN}All tests passed!${NC}"
echo "=========================================="
echo ""
echo "Check logs:"
echo "  - Application: logs/app.log"
echo "  - Audit: logs/audit.log"
echo ""

