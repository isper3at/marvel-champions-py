# Marvel Champions Backend - Developer Guide

## Quick Navigation

### Understanding the Architecture

The codebase follows the **EBI (Entities-Boundaries-Interactors)** pattern:

```
API Controllers
      ↓
Interactors (Business Logic)
      ↓
Entities (Data) ← Boundaries (External)
                  - Repositories
                  - Gateways
                  - Storage
```

### Finding Information

#### How Entities Work
- **Read**: `src/entities/game.py` (most comprehensive example)
- **Key Concept**: Immutable dataclasses that represent pure data
- **Philosophy**: Entities hold data; they don't enforce rules

#### How Interactors Work
- **Read**: `src/interactors/game_interactor.py`
- **Key Concept**: Smart coordinators that manage state transformations
- **Philosophy**: No rules enforcement; just state management

#### How Data Flows
1. **Card Import**: `CardInteractor.import_card_from_marvelcdb()` 
   - Fetches from MarvelCDB → Creates Card entity → Saves to repository
2. **Deck Creation**: `DeckInteractor.create_deck()` 
   - Gets cards → Creates Deck entity → Saves to repository
3. **Game Play**: `GameInteractor.draw_card()` 
   - Gets Game → Modifies state → Returns new Game → Saves to repository

---

## Common Tasks

### Add a New Game Action

**Example**: "Add ability to flip a card face-down"

1. **Add method to CardInPlay** (if it's a card state change)
   ```python
   def with_face_down(self, face_down: bool) -> 'CardInPlay':
       # Similar to with_rotated()
   ```

2. **Add method to GameInteractor**
   ```python
   def set_card_face_down(self, game_id: str, card_code: str, face_down: bool) -> Optional[Game]:
       # Similar to toggle_card_rotation()
   ```

3. **Add controller endpoint** (in `src/controllers/game_controller.py`)
   ```python
   @game_bp.route('/games/<game_id>/cards/<card_code>/face-down', methods=['PUT'])
   def set_face_down():
       # Call game_interactor.set_card_face_down()
   ```

4. **Add tests** in `tests/`
   - Test the new method in test_interactors_advanced.py
   - Test the API in test_controllers.py

### Add a New Counter Type

**Example**: "Add 'threat' counters to cards"

1. **Use CardInPlay.add_counter()** - it's already generic!
   ```python
   game = interactor.add_counter_to_card(
       game_id=game.id,
       card_code='01001a',
       counter_type='threat',  # Just use a new name!
       amount=2
   )
   ```

2. **UI interprets the counter** - No backend changes needed!
   - The counter is stored in `CardInPlay.counters` dict
   - UI decides what "threat" means visually
   - Players decide what it means in rules

### Import Cards from MarvelCDB

```python
# Single card
card = card_interactor.import_card_from_marvelcdb('01001a')

# Multiple cards
cards = card_interactor.import_cards_bulk(['01001a', '01002b', '01003c'])

# Gets card by code (if already imported)
card = card_interactor.get_card('01001a')

# Search for cards
cards = card_interactor.search_cards('Spider')  # Case-insensitive
```

### Create and Play a Game

```python
# 1. Create deck with specific cards
deck = deck_interactor.create_deck(
    'My Spider-Man Deck',
    [('01001a', 2), ('01002b', 1), ('01003c', 3)]  # (code, qty)
)

# 2. Create game
game = game_interactor.create_game(
    game_name='Alice vs Bob',
    deck_ids=[deck.id, deck.id],  # Both players use same deck
    player_names=['Alice', 'Bob']
)

# 3. Perform actions
game = game_interactor.draw_card(game.id, 'Alice')
game = game_interactor.play_card_to_table(
    game_id=game.id,
    player_name='Alice',
    card_code='01001a',
    position=Position(x=1, y=2)
)
game = game_interactor.add_counter_to_card(
    game_id=game.id,
    card_code='01001a',
    counter_type='damage',
    amount=3
)
```

---

## Key Design Decisions Explained

### 1. Why No Rules Enforcement?

**Problem**: Different game variants, house rules, expansions have different rules.

**Solution**: Backend tracks state only; UI/Players enforce rules.

**Benefit**: 
- One backend serves multiple game variants
- Easy to add new cards with different rules
- Players can experiment with house rules

**Example**:
```python
# This is ALLOWED (no validation)
game_interactor.play_card_to_table(
    game_id, 'Alice', 'expensive_card', position
)
# Even if Alice only has 2 resources and card costs 5
# Backend doesn't know about resource costs!
```

### 2. Why Immutability?

**Problem**: State bugs, concurrent access issues, hard to undo/redo.

**Solution**: All entities are frozen dataclasses. Methods return new instances.

**Benefit**:
- No accidental state corruption
- Safe for concurrent access
- Easy to implement undo/redo
- Easier to test

**Example**:
```python
player = PlayerZones(...)  # Original unchanged
new_player, drawn = player.draw_card()  # Returns new instance
# player is still unchanged
# new_player has the card in hand
```

### 3. Why Separate Entities, Boundaries, Interactors?

**Entities**: Pure data (immutable, no dependencies)
- Examples: Card, Deck, Game, PlayerZones

**Boundaries**: External integrations (repositories, gateways, storage)
- Examples: CardRepository, MarvelCDBGateway, ImageStorage

**Interactors**: Business logic coordination
- Examples: CardInteractor, DeckInteractor, GameInteractor

**Benefit**: Clean separation of concerns
- Easy to test (mock the boundaries)
- Easy to swap implementations (different DB, API)
- Entities don't depend on infrastructure

---

## Testing

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_interactors_advanced.py -v

# Specific test
pytest tests/test_interactors_advanced.py::test_draw_card -v

# Coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Adding Tests

**For a new method**:
1. Add test in `test_interactors_advanced.py` (for interactor methods)
2. Or add test in `test_controllers.py` (for API endpoints)
3. Test both success and edge cases (empty deck, missing player, etc.)

**Example**:
```python
def test_draw_card_with_empty_deck(game_interactor):
    game = game_interactor.create_game(...)
    # Empty player deck manually
    updated_game = game_interactor.draw_card(game.id, 'Alice')
    # Verify no change when deck empty
```

---

## Architecture Patterns

### Immutability Pattern
```python
# ❌ Never do this:
player.hand = player.hand + ('new_card',)  # EntityError - frozen!

# ✅ Do this:
new_hand = player.hand + ('new_card',)
new_player = PlayerZones(
    player_name=player.player_name,
    deck=player.deck,
    hand=new_hand,
    discard=player.discard,
    removed=player.removed
)
```

### State Transformation Pattern
```python
# ✅ All game actions follow this pattern:
def operation(self, game_id, ...):
    game = self.repo.find(game_id)  # Load current state
    # ... transform state ...
    new_state = GameState(...)
    new_game = Game(..., state=new_state, ...)
    return self.repo.save(new_game)  # Save new state
```

### Coordinator Pattern
```python
# ✅ Interactors coordinate between boundaries:
def import_deck_from_marvelcdb(self, deck_id):
    cards = self.marvelcdb.get_deck_cards(deck_id)  # Boundary 1
    self.card_interactor.import_cards_bulk(codes)  # Other interactor
    return self.deck_repo.save(deck)  # Boundary 2
```

---

## Debugging Tips

### "Where does X come from?"

1. **Look in Entities** (`src/entities/`) - Is it a core data structure?
2. **Look in Interactors** (`src/interactors/`) - Is it a business operation?
3. **Look in Controllers** (`src/controllers/`) - Is it an API endpoint?
4. **Look in Boundaries** (`src/boundaries/`) - Is it external integration?

### "Why does this test fail?"

1. Check the error message first (it's usually clear)
2. Look at the test setup - ensure mock data is correct
3. Check entity invariants - `__post_init__` validation
4. Check immutability - methods should return new instances

### "How do I...?"

1. **Store new data**: Add to Entity, add Repository method
2. **Change game state**: Add Interactor method
3. **Expose via API**: Add Controller endpoint
4. **Fetch external data**: Use/extend Gateway

---

## Code Style

### Docstrings
All classes and methods should have docstrings explaining:
- **What** it does (not "do something")
- **Why** (design decision)
- **How** (examples for complex logic)
- **Args/Returns** with types and meaning

### Naming
- **Classes**: PascalCase (Card, Game, PlayerZones)
- **Methods**: snake_case (draw_card, play_card_to_table)
- **Constants**: UPPER_SNAKE_CASE
- **Private methods**: _snake_case (e.g., _download_card_image)

### Type Hints
Use type hints on all methods:
```python
def draw_card(self, game_id: str, player_name: str) -> Optional[Game]:
    ...
```

---

## Common Gotchas

### ❌ Gotcha 1: Modifying Entities Directly
```python
# ❌ WRONG - Entities are frozen!
card.position = Position(1, 2)  # Error!

# ✅ RIGHT - Use transformation methods
new_card = card.with_position(Position(1, 2))
```

### ❌ Gotcha 2: Forgetting Immutability in Tests
```python
# ❌ WRONG - Test assumes state changed
game = game_interactor.draw_card(game.id, 'Alice')
assert game.state.get_player('Alice').hand  # Might not be updated!

# ✅ RIGHT - Use returned value
updated_game = game_interactor.draw_card(game.id, 'Alice')
assert updated_game.state.get_player('Alice').hand
```

### ❌ Gotcha 3: Assuming Rules Enforcement
```python
# ❌ WRONG - Expecting validation
game = game_interactor.play_card_to_table(...)
assert card_actually_in_hand()  # No validation happens!

# ✅ RIGHT - Backend doesn't validate
# UI or player rules should prevent invalid moves
```

---

## Getting Help

1. **Understanding flow**: Check `DESIGN_PHILOSOPHY.md`
2. **API endpoints**: Check `src/controllers/`
3. **Business logic**: Check `src/interactors/`
4. **Data structures**: Check `src/entities/`
5. **External integration**: Check `src/boundaries/` and `src/gateways/`
6. **Tests**: Check `tests/` for usage examples

All files have comprehensive docstrings with examples!
