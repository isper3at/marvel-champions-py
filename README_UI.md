# Marvel Champions - React UI

React-based frontend for Marvel Champions card game. Built with TypeScript and Axios, communicates with the Flask backend API.

## Quick Start

### Prerequisites
- Node.js 18+ with npm
- Backend server running on http://localhost:5000
- MongoDB (for backend, see main README)

### Start Frontend

**Using the startup script (recommended):**
```bash
./start-servers.sh --frontend-only
```

**Manual startup:**
```bash
cd ui
npm install  # Only needed once
npm start
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api
- API Documentation: http://localhost:5000/api/docs

### Stop Frontend

**Using the shutdown script:**
```bash
./stop-servers.sh --frontend-only
```

**Manual shutdown:**
```bash
# In a separate terminal, or Ctrl+C in the running terminal
pkill -f "react-scripts start"
# or find the process and kill it manually
```

## Frontend Setup

### Initial Installation

```bash
cd ui
npm install
```

### Development

```bash
cd ui
npm start
```

This starts the development server with hot reload at http://localhost:3000.

### Build for Production

```bash
cd ui
npm run build
```

Output is in `ui/build/` directory.

## Frontend Architecture

```
ui/
├── src/
│   ├── App.tsx                 # Main application component
│   ├── components/
│   │   ├── GameBoard.tsx       # Game board UI
│   │   ├── GameLobby.tsx       # Game lobby/selection
│   │   ├── CardComponent.tsx   # Card display
│   │   └── ...                 # Other UI components
│   ├── types/
│   │   └── index.ts            # TypeScript type definitions
│   ├── utils/
│   │   └── api.ts              # API client library
│   ├── styles/
│   │   └── ...                 # CSS/styling
│   ├── index.tsx               # React entry point
│   └── react-app-env.d.ts      # React type definitions
├── public/
│   └── index.html              # HTML template
├── package.json                # npm dependencies
├── tsconfig.json               # TypeScript configuration
└── build/                      # Production build (after npm run build)
```

## API Client

The frontend communicates with the backend via the `GameAPI` class in `ui/src/utils/api.ts`.

### Configuration

Set the backend API URL via environment variable:
```bash
export REACT_APP_API_URL=http://localhost:5000/api
npm start
```

**Default:** `http://localhost:5000/api`

### Available API Methods

**Game Management:**
- `listGames()` - Get all games
- `createGame(name, deckIds)` - Create new game
- `getGame(gameId)` - Get game details
- `deleteGame(gameId)` - Delete a game

**Game Actions:**
- `drawCard(gameId, playerName)` - Draw a card
- `playCard(gameId, playerName, cardCode, zone)` - Play card
- `moveCard(gameId, playerName, cardId, sourceZone, targetZone, position)` - Move card
- `rotateCard(gameId, playerName, cardId)` - Rotate card
- `updateCardCounter(gameId, playerName, cardId, counterValue)` - Update counter

**Deck Management:**
- `getDeck(deckId)` - Get deck info
- `getDeckCards(deckId)` - Get deck cards

**Card Queries:**
- `getCard(cardCode)` - Get card details
- `searchCards(query)` - Search cards
- `getCardImage(cardCode)` - Get card image URL

## Frontend Features

- **TypeScript**: Full type safety for API responses
- **Responsive Design**: Works on desktop and tablet
- **Real-time Updates**: Fetches latest game state
- **Card Display**: Shows card images from MarvelCDB
- **Game Lobby**: Create and join games
- **Game Board**: Full game interface for play

## Backend Integration

### Environment Variables

| Variable | Required | Default | Example |
|----------|----------|---------|---------|
| `REACT_APP_API_URL` | No | `http://localhost:5000/api` | `https://api.example.com/api` |

### API Response Structure

All API endpoints return consistent response structures:

**Success Response (List):**
```json
{
  "games": [
    {"id": "123", "name": "Game 1", ...},
    {"id": "456", "name": "Game 2", ...}
  ],
  "count": 2
}
```

**Success Response (Single):**
```json
{
  "id": "123",
  "name": "Game 1",
  ...
}
```

**Error Response:**
```json
{
  "error": "Description of error"
}
```

## Data Flow

1. User interacts with React component
2. Component calls method in `GameAPI` (e.g., `gameAPI.listGames()`)
3. API client sends HTTP request to backend
4. Backend processes request and returns JSON
5. Frontend parses response and updates React state
6. Component re-renders with new data

Example:
```typescript
const [games, setGames] = useState<GameState[]>([]);

useEffect(() => {
  const loadGames = async () => {
    try {
      const list = await gameAPI.listGames();
      setGames(list);
    } catch (err) {
      console.error('Failed to load games:', err);
    }
  };
  loadGames();
}, []);
```

## Browser Support

- Chrome/Chromium: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Edge: ✅ Full support

**Minimum Requirements:**
- ES2020 JavaScript support
- Fetch API or Axios
- React 18+

## Debugging

### Enable Debug Logging

Add to `ui/src/utils/api.ts`:
```typescript
// In the GameAPI class constructor
console.log('API Base URL:', API_BASE_URL);
```

### Check Network Requests

Open browser Developer Tools (F12):
1. Go to Network tab
2. Make API calls in the app
3. Click on request to see details

### Backend Logs

View backend logs:
```bash
tail -f logs/backend.log
```

## Performance Tips

- **Lazy Load Images**: Card images load on demand
- **Cache Deck Data**: Decks cached in browser localStorage
- **Minimize Re-renders**: Use React.memo for cards
- **Optimize State**: Keep state shallow and focused

## Troubleshooting

### "Cannot GET /api/..." Error
- Ensure backend is running on port 5000
- Check `REACT_APP_API_URL` environment variable
- Verify backend is accessible: `curl http://localhost:5000/api/health`

### CORS Errors
- Backend CORS is configured in Flask
- Ensure you're accessing frontend via `localhost:3000`, not `127.0.0.1:3000`

### API Requests Timing Out
- Check MongoDB connection in backend logs
- Verify backend is responding: `curl http://localhost:5000/health`

### Cards Not Loading
- Verify MarvelCDB API is accessible
- Check backend logs for API errors
- Image storage path exists and is writable

## Building for Production

### Build Steps

```bash
cd ui
npm run build
```

### Serve Built App

Using Flask (backend serves frontend):
```bash
python src/app.py
```

The app will be served at http://localhost:5000

## Type Definitions

Key types defined in `ui/src/types/index.ts`:

```typescript
interface GameState {
  id: string;
  name: string;
  players: Player[];
  created_at: string;
  state: Game;
}

interface Card {
  code: string;
  name: string;
  text: string;
}

interface Deck {
  id: string;
  name: string;
  cards: Card[];
  card_count: number;
  source_url: string;
}
```

See `ui/src/types/index.ts` for complete type definitions.

## Performance Metrics

- **Bundle Size**: ~150KB gzipped
- **Initial Load**: ~2-3 seconds (depends on network)
- **API Response Time**: ~100-200ms typical
- **Card Image Load**: ~50-500ms per image

## Notes

- The server uses MongoDB collection `games` for persistent game state
- Frontend caches fetched decks and cards in browser localStorage
- Socket.IO support available for real-time updates (frontend ready)
- Card images sourced from MarvelCDB - respects usage terms
- API documentation available at http://localhost:5000/api/docs
