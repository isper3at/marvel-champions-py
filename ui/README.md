# Marvel Champions UI

React-based frontend for the Marvel Champions card game. Features real-time multiplayer game board with drag-and-drop card mechanics.

## Features

- 🎮 Interactive game board with splayed player hand
- 🃏 Drag-and-drop card mechanics between all zones
- 👥 Multi-player support with opponent zone displays
- 📋 Deck view for managing cards during gameplay
- ⚡ Real-time game state synchronization
- 📱 Responsive design for desktop and tablet

## Architecture

### Components

- **GameBoard**: Main game container orchestrating the layout
- **PlayerHand**: Splayed card hand at bottom (hover to lift cards)
- **EncounterZone**: Large central drag-and-drop area with deck/discard stacks
- **PlayerZone**: Player's play field with multiple card zones
- **OpponentZone**: Compact display of opponent game states
- **DeckView**: List-based modal for viewing and managing deck cards
- **GameLobby**: Game selection and player setup

### File Structure

```
src/
├── components/        # React components
│   ├── GameBoard.tsx
│   ├── PlayerHand.tsx
│   ├── EncounterZone.tsx
│   ├── PlayerZone.tsx
│   ├── OpponentZone.tsx
│   ├── DeckView.tsx
│   ├── Card.tsx
│   └── GameLobby.tsx
├── hooks/            # Custom React hooks
├── types/            # TypeScript type definitions
├── utils/            # Utility functions and API client
├── styles/           # CSS files
└── App.tsx          # Main App component
```

### Types

Core types defined in `src/types/index.ts`:
- Card, CardInPlay
- Player, PlayerZones
- GameState
- EncounterZone
- DragItem, DropZoneType

## Installation

```bash
npm install
```

## Configuration

Create `.env` file in the ui directory:

```env
REACT_APP_API_URL=http://localhost:5000/api
```

## Running

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## Build

```bash
npm run build
```

## API Integration

The UI communicates with the backend via the `gameAPI` client in `src/utils/api.ts`. All endpoints are documented in the backend's OpenAPI specification.

### Key Endpoints Used

- `GET /api/games` - List games
- `GET /api/games/{id}` - Get game state
- `POST /api/games/{id}/draw` - Draw card
- `POST /api/games/{id}/play` - Play card
- `POST /api/games/{id}/move` - Move card between zones
- `POST /api/games/{id}/rotate` - Rotate card
- `POST /api/games/{id}/counter` - Update card counter

## Styling

Global styles and component-specific CSS use a consistent color scheme:
- Primary: #daa520 (gold)
- Background: Dark blues and blacks with transparency
- Accents: Responsive hover states and transitions

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development

### Code Quality

- TypeScript strict mode enabled
- ESLint configuration included
- Component-based architecture

### Debugging

Console logging available for:
- Card drag operations
- API calls
- Game state updates

## Future Enhancements

- [ ] WebSocket support for real-time multiplayer
- [ ] Animation library integration
- [ ] Sound effects
- [ ] Game replay system
- [ ] Player statistics tracking
- [ ] Spectator mode
