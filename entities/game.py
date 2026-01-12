from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Position:
    """2D position on the play field"""
    x: int
    y: int


@dataclass(frozen=True)
class CardInPlay:
    """
    A card on the table with position and visual state.
    No rules about what states mean - just visual representation.
    """
    code: str
    position: Position
    
    # Visual states - no enforcement of what these mean
    rotated: bool = False  # 90 degrees (exhausted? doesn't matter to us)
    flipped: bool = False  # Face down
    
    # Generic counters - use however you want
    counters: dict[str, int] = field(default_factory=dict)  # damage, threat, whatever
    
    def with_position(self, position: Position) -> 'CardInPlay':
        """Create new instance with updated position"""
        return CardInPlay(
            code=self.code,
            position=position,
            rotated=self.rotated,
            flipped=self.flipped,
            counters=self.counters
        )
    
    def with_rotated(self, rotated: bool) -> 'CardInPlay':
        """Create new instance with updated rotation"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            rotated=rotated,
            flipped=self.flipped,
            counters=self.counters
        )
    
    def with_flipped(self, flipped: bool) -> 'CardInPlay':
        """Create new instance with updated flip state"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            rotated=self.rotated,
            flipped=flipped,
            counters=self.counters
        )
    
    def add_counter(self, counter_type: str, amount: int = 1) -> 'CardInPlay':
        """Add counters to a card"""
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
class GameState:
    """
    Game state - just zones and cards.
    No rules about what you can/can't do.
    """
    # Deck zones (just lists of card codes)
    deck: tuple[str, ...]  # Your deck
    hand: tuple[str, ...]  # Your hand
    discard: tuple[str, ...]  # Discard pile
    
    # Play area
    play_area: tuple[CardInPlay, ...]  # All cards on the table
    
    # Optional: Additional zones if you want
    removed: tuple[str, ...] = ()  # Removed from game
    
    def draw_card(self) -> tuple['GameState', Optional[str]]:
        """Draw a card. Returns new state and drawn card."""
        if not self.deck:
            return self, None
        
        drawn = self.deck[0]
        new_deck = self.deck[1:]
        new_hand = self.hand + (drawn,)
        
        return GameState(
            deck=new_deck,
            hand=new_hand,
            discard=self.discard,
            play_area=self.play_area,
            removed=self.removed
        ), drawn
    
    def shuffle_discard_into_deck(self) -> 'GameState':
        """Shuffle discard pile into deck"""
        import random
        combined = list(self.deck) + list(self.discard)
        random.shuffle(combined)
        
        return GameState(
            deck=tuple(combined),
            hand=self.hand,
            discard=(),
            play_area=self.play_area,
            removed=self.removed
        )
    
    def move_to_discard(self, card_code: str, from_zone: str = 'hand') -> 'GameState':
        """Move a card to discard pile"""
        if from_zone == 'hand':
            if card_code not in self.hand:
                return self
            new_hand = tuple(c for c in self.hand if c != card_code or self.hand.index(c) != self.hand.index(card_code))
            return GameState(
                deck=self.deck,
                hand=new_hand,
                discard=self.discard + (card_code,),
                play_area=self.play_area,
                removed=self.removed
            )
        
        return self


@dataclass(frozen=True)
class Game:
    """
    A game session.
    Just tracks state - no rules enforcement.
    """
    id: Optional[str]
    name: str
    deck_id: str  # Reference to the deck being used
    state: GameState
    
    # Audit trail
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Game name cannot be empty")
        if not self.deck_id:
            raise ValueError("Deck ID cannot be empty")