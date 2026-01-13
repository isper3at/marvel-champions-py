"""
Game entity models for Marvel Champions.

This module defines the core data structures for representing game state:
- Position: 2D coordinates on the play field
- CardInPlay: A card placed on the table with visual state
- PlayerZones: A player's card collection areas (deck, hand, discard, removed)
- GameState: The complete state of an active game
- Game: A game session with metadata

Design Philosophy:
- No rules enforcement - these are state containers only
- Visual state is explicit (rotation, flip, counters)
- Immutable (frozen dataclasses) for safe state management
- Generic design - works with any card game, not just Marvel Champions
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Position:
    """
    2D position on the play field.
    
    Used to track where cards are positioned during gameplay.
    
    Attributes:
        x: Horizontal coordinate (0 = left)
        y: Vertical coordinate (0 = top)
    """
    x: int
    y: int


@dataclass(frozen=True)
class CardInPlay:
    """
    A card placed on the table with position and visual state.
    
    This class represents a card that has been played to the game board.
    It tracks the card's position, visual appearance, and counters.
    
    Important: This class does NOT enforce game rules. It's purely a state
    container. A card can be rotated, flipped, or have any counters regardless
    of game logic. The frontend/rules engine decides what these states mean.
    
    Attributes:
        code: Card code (unique identifier)
        position: 2D coordinates on the play field
        rotated: Whether card is rotated 90 degrees (visual state only)
        flipped: Whether card is face-down (visual state only)
        counters: Generic counter dictionary for any game counters (e.g., damage,
                 threat, tokens). Counter types and meanings are application-defined.
    
    Example:
        >>> card = CardInPlay(
        ...     code='01001',
        ...     position=Position(x=10, y=20),
        ...     rotated=False,
        ...     counters={'damage': 3}
        ... )
        >>> # Rotate the card (returns new immutable instance)
        >>> rotated_card = card.with_rotated(True)
        >>> # Add a damage counter
        >>> damaged = card.add_counter('damage', 2)
    """
    code: str
    position: Position
    rotated: bool = False  # Visual state: rotated 90 degrees
    flipped: bool = False  # Visual state: face down
    counters: dict[str, int] = field(default_factory=dict)  # Generic counters
    
    def with_position(self, position: Position) -> 'CardInPlay':
        """
        Create new instance with updated position.
        
        Since CardInPlay is frozen (immutable), this returns a new instance
        rather than modifying the existing one.
        
        Args:
            position: New Position for the card
            
        Returns:
            New CardInPlay instance with updated position
            
        Example:
            >>> card = CardInPlay(code='01001', position=Position(0, 0))
            >>> moved = card.with_position(Position(10, 20))
            >>> assert moved.position.x == 10
        """
        return CardInPlay(
            code=self.code,
            position=position,
            rotated=self.rotated,
            flipped=self.flipped,
            counters=self.counters
        )
    
    def with_rotated(self, rotated: bool) -> 'CardInPlay':
        """
        Create new instance with updated rotation state.
        
        Used to represent cards that are exhausted or in a rotated state.
        The semantic meaning of "rotated" is determined by game logic.
        
        Args:
            rotated: True if card should be rotated 90 degrees
            
        Returns:
            New CardInPlay instance with updated rotation
            
        Example:
            >>> card = CardInPlay(code='01001', position=Position(0, 0))
            >>> exhausted = card.with_rotated(True)
            >>> assert exhausted.rotated is True
        """
        return CardInPlay(
            code=self.code,
            position=self.position,
            rotated=rotated,
            flipped=self.flipped,
            counters=self.counters
        )
    
    def with_flipped(self, flipped: bool) -> 'CardInPlay':
        """
        Create new instance with updated flip state.
        
        Used for face-down cards or hidden information. The semantic meaning
        is determined by game logic.
        
        Args:
            flipped: True if card should be face-down
            
        Returns:
            New CardInPlay instance with updated flip state
        """
        return CardInPlay(
            code=self.code,
            position=self.position,
            rotated=self.rotated,
            flipped=flipped,
            counters=self.counters
        )
    
    def add_counter(self, counter_type: str, amount: int = 1) -> 'CardInPlay':
        """
        Create new instance with added counter.
        
        Counters are generic and can represent any game effect (damage, threat, tokens, etc).
        The meaning of counter types is entirely application-defined.
        
        Args:
            counter_type: Name of the counter (e.g., 'damage', 'threat')
            amount: How many to add (default 1). Can be negative to decrease.
            
        Returns:
            New CardInPlay instance with updated counters
            
        Example:
            >>> card = CardInPlay(code='01001', position=Position(0, 0))
            >>> with_damage = card.add_counter('damage', 3)
            >>> assert with_damage.counters['damage'] == 3
            >>> more_damage = with_damage.add_counter('damage', 2)
            >>> assert more_damage.counters['damage'] == 5
        """
        new_counters = dict(self.counters)
        new_counters[counter_type] = new_counters.get(counter_type, 0) + amount
        
        return CardInPlay(
            code=self.code,
            position=self.position,
            rotated=self.rotated,
            flipped=self.flipped,
            counters=new_counters
        )


@dataclass(frozen=True)
class PlayerZones:
    """
    One player's card collection areas.
    
    In a multiplayer game, each player has their own zones for managing
    their cards. This class tracks a single player's card locations.
    
    Attributes:
        player_name: Display name for the player
        deck: Cards remaining in deck (drawn from front)
        hand: Cards in player's hand
        discard: Cards in discard/trash pile
        removed: Cards removed from game (can't be recovered)
    
    Note: All card collections are immutable tuples. Use the helper methods
    to get new PlayerZones instances with updated collections.
    
    Example:
        >>> zones = PlayerZones(
        ...     player_name='Alice',
        ...     deck=('card1', 'card2', 'card3'),
        ...     hand=('hand_card1',),
        ...     discard=(),
        ...     removed=()
        ... )
        >>> # Draw a card
        >>> zones, drawn = zones.draw_card()
        >>> assert drawn == 'card1'
        >>> assert zones.deck == ('card2', 'card3')
    """
    player_name: str
    deck: tuple[str, ...]  # Cards to draw from (front is next drawn)
    hand: tuple[str, ...]  # Cards in hand
    discard: tuple[str, ...]  # Discarded cards
    removed: tuple[str, ...] = ()  # Removed from game permanently
    
    def draw_card(self) -> tuple['PlayerZones', Optional[str]]:
        """
        Draw a card from this player's deck.
        
        Returns a new PlayerZones instance with the card moved from deck to hand.
        If the deck is empty, returns the same state and None as the drawn card.
        
        Returns:
            Tuple of (new_zones_with_card_in_hand, card_code_drawn)
            The card_code_drawn is None if deck was empty.
            
        Example:
            >>> zones = PlayerZones(
            ...     player_name='Alice',
            ...     deck=('card1', 'card2'),
            ...     hand=('hand1',),
            ...     discard=()
            ... )
            >>> new_zones, drawn = zones.draw_card()
            >>> assert drawn == 'card1'
            >>> assert 'card1' in new_zones.hand
            >>> assert 'card1' not in new_zones.deck
        """
        if not self.deck:
            return self, None
        
        drawn = self.deck[0]
        new_deck = self.deck[1:]
        new_hand = self.hand + (drawn,)
        
        return PlayerZones(
            player_name=self.player_name,
            deck=new_deck,
            hand=new_hand,
            discard=self.discard,
            removed=self.removed
        ), drawn
    
    def shuffle_discard_into_deck(self) -> 'PlayerZones':
        """
        Shuffle discard pile back into the deck.
        
        When a player runs out of cards to draw, they can shuffle their discard
        pile to create a new deck. This is common in deck-building games.
        
        Returns:
            New PlayerZones with shuffled deck and empty discard
            
        Example:
            >>> zones = PlayerZones(
            ...     player_name='Alice',
            ...     deck=('last_card',),
            ...     hand=(),
            ...     discard=('card1', 'card2', 'card3')
            ... )
            >>> new_zones = zones.shuffle_discard_into_deck()
            >>> assert len(new_zones.deck) == 4  # last_card + 3 from discard
            >>> assert len(new_zones.discard) == 0
        """
        import random
        combined = list(self.deck) + list(self.discard)
        random.shuffle(combined)
        
        return PlayerZones(
            player_name=self.player_name,
            deck=tuple(combined),
            hand=self.hand,
            discard=(),
            removed=self.removed
        )


@dataclass(frozen=True)
class GameState:
    """
    Complete snapshot of a game at a point in time.
    
    GameState is immutable and represents one complete state of the game,
    tracking all player information and the shared play area. This class
    contains NO game rules - it's a pure data structure for state representation.
    
    This design allows for:
    - Easy undo/redo (just keep old GameState instances)
    - Deterministic state management (immutability prevents side effects)
    - Clean separation of state from rules (rules are in interactors)
    
    Attributes:
        players: List of PlayerZones, one for each player in the game
        play_area: All CardInPlay objects currently visible on the table
    
    Note: Game rules (what moves are valid, when to draw, etc) are NOT enforced
    here. That logic lives in GameInteractor. This class just stores and provides
    access to the data.
    
    Example:
        >>> player1 = PlayerZones('Alice', deck=('c1', 'c2'), hand=(), discard=())
        >>> player2 = PlayerZones('Bob', deck=('c3', 'c4'), hand=(), discard=())
        >>> card = CardInPlay(code='01001', position=Position(0, 0))
        >>> state = GameState(
        ...     players=[player1, player2],
        ...     play_area=(card,)
        ... )
        >>> assert state.get_player('Alice').player_name == 'Alice'
    """
    players: list[PlayerZones]  # Each player's card zones
    play_area: tuple[CardInPlay, ...]  # Cards on the table
    
    def get_player(self, player_name: str) -> Optional[PlayerZones]:
        """
        Find a player's zones by name.
        
        Args:
            player_name: The name to search for
            
        Returns:
            PlayerZones for the named player, or None if not found
            
        Example:
            >>> state = GameState(
            ...     players=[PlayerZones('Alice', (), (), ())],
            ...     play_area=()
            ... )
            >>> alice = state.get_player('Alice')
            >>> assert alice.player_name == 'Alice'
        """
        for p in self.players:
            if p.player_name == player_name:
                return p
        return None
    
    def update_player(self, updated_player: PlayerZones) -> 'GameState':
        """
        Create a new GameState with one player's zones updated.
        
        This is the primary way to modify player state. It returns a completely
        new GameState instance with the specified player updated while keeping
        all other players unchanged (and the play_area unchanged).
        
        Args:
            updated_player: The new PlayerZones to replace the existing one
            
        Returns:
            New GameState with updated player (matched by player_name)
            
        Raises:
            Note: No error if player not found - just returns state unchanged.
            This is intentional to support flexible game state management.
            
        Example:
            >>> alice = PlayerZones('Alice', deck=('c1',), hand=(), discard=())
            >>> state = GameState(players=[alice], play_area=())
            >>> new_alice = alice.shuffle_discard_into_deck()
            >>> new_state = state.update_player(new_alice)
            >>> assert new_state.get_player('Alice') == new_alice
            >>> assert state != new_state  # Original is unchanged
        """
        new_players = []
        for p in self.players:
            if p.player_name == updated_player.player_name:
                new_players.append(updated_player)
            else:
                new_players.append(p)
        
        return GameState(
            players=tuple(new_players),
            play_area=self.play_area
        )


@dataclass(frozen=True)
class Game:
    """
    A game session entity representing a Marvel Champions game in progress.
    
    Game is the top-level entity containing a GameState plus metadata about
    the session (id, name, timestamps). Like all entities, it's immutable.
    
    This class enforces minimal validation:
    - Game name cannot be empty
    - At least one deck must be specified
    
    No other rules are enforced here (that's in GameInteractor).
    
    Attributes:
        id: Unique identifier for this game session (from database)
        name: Display name for the game (e.g., "Alice vs Bob")
        deck_ids: Tuple of deck identifiers being used in this game
        state: Current GameState with all player info and play area
        created_at: Timestamp when game was started
        updated_at: Timestamp of last state change
    
    Architecture Note:
    This follows the EBI (Entities-Boundaries-Interactors) pattern:
    - Entity: Game holds data and enforces data invariants
    - Boundaries: Repositories persist Game, Gateways may import external data
    - Interactors: GameInteractor contains game rules and state transitions
    
    Example:
        >>> alice = PlayerZones('Alice', deck=('c1',), hand=(), discard=())
        >>> state = GameState(players=[alice], play_area=())
        >>> game = Game(
        ...     id='game123',
        ...     name='Alice vs AI',
        ...     deck_ids=('deck1', 'deck2'),
        ...     state=state
        ... )
        >>> assert game.name == 'Alice vs AI'
        >>> # Game state is never modified - create new Game instance with
        >>> # new_state = modified_game_state
        >>> # new_game = dataclasses.replace(game, state=new_state)
    """
    id: Optional[str]
    name: str
    deck_ids: tuple[str, ...]
    state: GameState
    
    # Audit trail for tracking when game was created and last modified
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """
        Validate invariants when creating a Game.
        
        This runs automatically after the dataclass initializes. It ensures
        that the game name is not empty and at least one deck is specified.
        
        Raises:
            ValueError: If name is empty or no deck_ids provided
        """
        if not self.name:
            raise ValueError("Game name cannot be empty")
        if not self.deck_ids:
            raise ValueError("Deck IDs cannot be empty")
