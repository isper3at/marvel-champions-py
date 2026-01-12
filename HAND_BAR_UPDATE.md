# Hand Bar UI Update - Slay the Spire Style

## Overview
The game board UI has been restructured to display the player's hand across the bottom of the screen, similar to Slay the Spire.

## Key Changes

### Layout Structure

**Before:**
- All players shown vertically on screen
- Each player had their deck, hand, discard, and play area displayed inline
- Hand mixed in with other UI elements

**After:**
- **Top section (scrollable):**
  - Game Board title
  - Encounter cards zone (center top)
  - Other players' zones (compact view with deck, discard, play area)
  
- **Bottom section (fixed hand bar):**
  - Left side: Player stats (deck count, discard count, play area count)
  - Right side: Horizontal scrollable hand of cards with Play/Discard buttons

### Component Changes

#### GameView Component (`app.js`)
- Separated current player from other players
- Added `myPlayer` and `otherPlayers` logic to identify self vs opponents
- Restructured layout into:
  - `game-container` (flex column)
  - `game-area` (scrollable, shows encounter + other players)
  - `hand-bar` (fixed at bottom, shows player's hand)

#### CSS Enhancements (`style.css`)
- **`#root`**: Changed from fixed padding to full viewport height with flex layout
- **`.game-container`**: Flex column taking full screen height
- **`.game-area`**: Scrollable area for game state (flex: 1 to grow)
- **`.hand-bar`**: Fixed position at bottom with:
  - Dark semi-transparent gradient background
  - Top border highlight
  - Flex row layout
  - Max height of 200px with overflow
- **`.hand-cards`**: Horizontal scrollable container for cards
- **`.hand-card`**: Individual card in hand with:
  - Blue gradient background (distinct from other cards)
  - Hover effect: translateY(-8px) with blue glow
  - Compact layout with card name and buttons
  - Play/Discard buttons stacked inside
- **`.hand-info`**: Player stats section on left (deck, discard, play counts)

### User Interactions

1. **Draw a card**: Click the deck number in left info section or drag from hand
2. **Play a card**: Click "Play" button on card in hand bar
3. **Discard a card**: Click "Discard" button on card in hand bar
4. **Drag and drop**: Still supported - drag from hand to opponent zones
5. **View full deck**: Click "Open" button under other players' deck stacks
6. **Hover effects**: Cards in hand bar lift up and glow when hovered

### Visual Improvements

- **Hand bar styling**: Blue-tinted card backgrounds with hover animations
- **Player stats**: Clear display of deck, discard, and play area counts at a glance
- **Encounter zone**: Highlighted with orange-tinted border to distinguish from play areas
- **Other players**: Compact grid layout below encounter zone
- **Responsive**: Works on various screen sizes with scrolling in game area and hand bar

## Testing

To see the new layout:

1. Start the server: `python app.py`
2. Open http://127.0.0.1:5000 in browser
3. Create a lobby or join one
4. Load a deck and start the game
5. Observe:
   - Encounter zone at top with cards
   - Other players shown in compact grid
   - Your hand displayed as a scrollable bar at the bottom
   - Hover over cards to see lift/glow effect
   - Click Play/Discard buttons to move cards

## Files Modified

- `static/ui/app.js` - GameView component restructured
- `static/ui/style.css` - Added game-container, hand-bar, and related styles
