# Drag and Drop UI Overhaul - Maximized Game Board

## Overview
The game board UI has been completely restructured to maximize play space and make all cards in all zones draggable and droppable.

## Key Changes

### 1. Layout Reorganization

**Game Area (90% of screen)**
- Encounter zone at top (large, prominent)
- Other players' boards displayed in a responsive grid (1-2 columns depending on screen)
- Each player board shows:
  - **Play Area** (large, takes most space)
  - **Deck/Discard info** (compact, bottom of board)

**Hand Bar (10% of screen)**
- Left side: Deck, Discard count zone, Play Area count zone (compact)
- Right side: Horizontally scrollable hand cards

### 2. All Cards Now Draggable

**From Hand:**
- Drag to own Play Area or Discard
- Drag to opponent zones
- Click Play/Discard buttons for quick actions

**From Other Zones:**
- Encounter cards: Draggable (can send to any zone)
- Play Areas: Draggable (any player's play area)
- Discard Zones: Draggable (cards can be recycled)

**Drop Zones:**
- Encounter zone (accepts from anywhere)
- Player play areas (accepts from anywhere)
- Discard zones (accepts from anywhere)
- Hand bar discard/play droplets (small drop zones for quick access)

### 3. Visual Improvements

**Large Cards (120x160px)**
- Encounter cards
- Player play areas
- Hover: Scale up 5%, blue glow
- All have grab cursor, change to grabbing when dragging

**Standard Cards (92x128px)**
- Discard piles
- Other smaller zones
- Hover: Scale up 3%, subtle blue glow

**Drop Zone Visual Feedback**
- Dashed borders with colored tints:
  - Encounter: Orange tint
  - Play areas: Green tint
  - Discard: Blue tint
- Show "Drop here" text when empty
- Flex layout to handle many cards

**Hand Bar**
- Compact deck stack (60x80px)
- Discard/Play small zones (60x60px) for quick drops
- Horizontally scrollable hand cards
- Semi-transparent dark background with top border

### 4. Technical Implementation

#### Component Changes (app.js)
- Restructured game area to use CSS Grid for other players
- Made all cards have `draggable:true` attribute
- Each card includes drag data: `{fromPlayer, fromZone, index}`
- Drop zones include `onDragOver` (prevent default) and `onDrop` (parse data, call moveCard)
- Encounter cards handled with `fromPlayer: -1` marker
- Index calculation for other players: `otherPlayers.indexOf(p) + 1` (0 is myPlayer)

#### CSS Changes (style.css)
- `.game-container`: Flex column, full height
- `.game-area`: Flex 1, scrollable, contains encounter + other players
- `.encounter-cards`: Large min-height (240px), flex wrap with large cards
- `.other-players`: CSS Grid `repeat(auto-fit, minmax(400px, 1fr))`
- `.play-cards`: Green-tinted drop zone, large min-height
- `.large-card`: 120x160px with hover scale/glow
- `.hand-bar`: Fixed at bottom, compact heights
- `.hand-cards`: Scrollable row of cards
- Drop zones: Dashed borders, colored tints, "Drop here" text

### 5. User Experience Flow

1. **Draw Phase**: Click deck in hand bar → card appears in hand
2. **Play Phase**: 
   - Option A: Click "Play" button on card in hand → goes to your play area
   - Option B: Drag card from hand to your play area zone
   - Option C: Drag card from hand to opponent zone (if supported)
3. **Discard Phase**:
   - Option A: Click "Discard" button on card → goes to discard
   - Option B: Drag card to discard zone in hand bar
   - Option C: Drag card from any zone to discard
4. **Combat**: Drag encounter cards or opponent cards around (for tracking)

### 6. Responsive Design

- **Desktop (1200px+)**: Two-column grid for other players
- **Tablet (800px-1199px)**: One-column or two-column depending on screen width
- **Mobile (< 800px)**: Single column, hand bar scrolls horizontally
- Game area scrolls vertically if needed
- Hand bar has max-height with horizontal scroll overflow

## Files Modified

- `static/ui/app.js` - GameView component with all cards draggable
- `static/ui/style.css` - Maximized game board layout, large drop zones, hover effects

## Testing

1. Start server: `python app.py`
2. Create/join lobby, load deck, start game
3. Try dragging:
   - Cards from hand → play area
   - Cards from hand → discard
   - Encounter cards → any zone
   - Cards between player zones
4. Drop zones show visual feedback (dashed border, text)
5. All drag operations update state immediately
6. Hover effects show cards are draggable

## Next Steps (Optional)

- Add card count badges to zones
- Add animation when cards are played/discarded
- Add sound effects for drag/drop
- Add card preview on hover (zoom/modal)
- Add undo functionality
- Add turn order/combat phase indicators
