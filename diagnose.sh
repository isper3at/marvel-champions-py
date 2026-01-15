#!/bin/bash
# diagnose.sh - Diagnose "Create Game" issues

echo "=========================================="
echo "Marvel Champions - Diagnostics"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check 1: Backend running
echo "1. Checking if backend is running..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is running"
    HEALTH=$(curl -s http://localhost:5000/health)
    echo "   Response: $HEALTH"
else
    echo -e "${RED}✗${NC} Backend is NOT running!"
    echo ""
    echo "To start backend:"
    echo "  poetry run python src/app.py"
    echo ""
    exit 1
fi

echo ""

# Check 2: MongoDB
echo "2. Checking MongoDB..."
if mongosh --quiet --eval "db.version()" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} MongoDB is running"
    MONGO_VERSION=$(mongosh --quiet --eval "db.version()")
    echo "   Version: $MONGO_VERSION"
else
    echo -e "${RED}✗${NC} MongoDB is NOT running!"
    echo ""
    echo "To start MongoDB:"
    echo "  macOS: brew services start mongodb-community"
    echo "  Linux: sudo systemctl start mongodb"
    echo ""
    exit 1
fi

echo ""

# Check 3: Can create a card
echo "3. Testing card creation..."
CARD_RESPONSE=$(curl -s -X POST http://localhost:5000/api/cards/import \
    -H "Content-Type: application/json" \
    -d '{"code": "test_diag_001"}')

if echo $CARD_RESPONSE | grep -q "success"; then
    echo -e "${GREEN}✓${NC} Card creation works"
else
    echo -e "${YELLOW}⚠${NC} Card may already exist or error occurred"
    echo "   Response: $CARD_RESPONSE"
fi

echo ""

# Check 4: Can create a deck
echo "4. Testing deck creation..."
DECK_RESPONSE=$(curl -s -X POST http://localhost:5000/api/decks \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Diagnostic Test Deck",
        "cards": [{"code": "test_diag_001", "quantity": 3}]
    }')

DECK_ID=$(echo $DECK_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$DECK_ID" ]; then
    echo -e "${GREEN}✓${NC} Deck creation works"
    echo "   Deck ID: $DECK_ID"
else
    echo -e "${RED}✗${NC} Deck creation failed!"
    echo "   Response: $DECK_RESPONSE"
    exit 1
fi

echo ""

# Check 5: Can create a game
echo "5. Testing game creation..."
GAME_RESPONSE=$(curl -s -X POST http://localhost:5000/api/games \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Diagnostic Test Game\",
        \"deck_ids\": [\"$DECK_ID\"],
        \"player_names\": [\"TestPlayer\"]
    }")

GAME_ID=$(echo $GAME_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$GAME_ID" ]; then
    echo -e "${GREEN}✓${NC} Game creation works!"
    echo "   Game ID: $GAME_ID"
else
    echo -e "${RED}✗${NC} Game creation failed!"
    echo "   Response: $GAME_RESPONSE"
    echo ""
    echo "This is likely your issue!"
    exit 1
fi

echo ""

# Check 6: CORS
echo "6. Checking CORS headers..."
CORS_RESPONSE=$(curl -s -I http://localhost:5000/health | grep -i "access-control")

if [ -n "$CORS_RESPONSE" ]; then
    echo -e "${GREEN}✓${NC} CORS is enabled"
    echo "   $CORS_RESPONSE"
else
    echo -e "${YELLOW}⚠${NC} CORS headers not found"
    echo "   Make sure flask-cors is installed and enabled"
fi

echo ""

# Check 7: Logs
echo "7. Checking logs..."
if [ -f "logs/app.log" ]; then
    echo -e "${GREEN}✓${NC} Application log exists"
    echo "   Last 5 lines:"
    tail -5 logs/app.log | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠${NC} No application log found"
fi

echo ""

if [ -f "logs/audit.log" ]; then
    echo -e "${GREEN}✓${NC} Audit log exists"
    echo "   Last entry:"
    tail -1 logs/audit.log | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠${NC} No audit log found"
fi

echo ""

# Cleanup
echo "8. Cleaning up test data..."
curl -s -X DELETE http://localhost:5000/api/games/$GAME_ID > /dev/null
curl -s -X DELETE http://localhost:5000/api/decks/$DECK_ID > /dev/null
echo -e "${GREEN}✓${NC} Cleanup complete"

echo ""
echo "=========================================="
echo -e "${GREEN}All systems operational!${NC}"
echo "=========================================="
echo ""
echo "If you're still having issues:"
echo "1. Open browser DevTools (F12)"
echo "2. Go to Network tab"
echo "3. Try creating a game"
echo "4. Check the request/response"
echo ""
echo "Or check backend logs:"
echo "  tail -f logs/app.log"
echo ""

