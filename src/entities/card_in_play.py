"""
CardInPlay entity - represents a card on the game board with state.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from .card import Card
from .position import Position


@dataclass(frozen=True)
class CardInPlay:
    """
    Represents a card in play with its visual and game state.
    
    Immutable - create new instance for state changes.
    
    Attributes:
        code: Card identifier (reference to Card entity)
        position: Where the card is on the board
        exhausted: Whether card is exhausted/tapped (rotated 90°)
        flipped: Whether card is face-down
        counters: Dictionary of counter types to values
    
    Example:
        >>> from .position import Position
        >>> card = CardInPlay(
        ...     code='01001a',
        ...     position=Position(x=100, y=200, rotation=0, flip_state=FlipState.FACE_UP),
        ...     counters={'damage': 3}
        ... )
        >>> updated = card.add_counter('damage', 2)
        >>> assert updated.counters['damage'] == 5
    """
    card: Card
    position: Position
    counters: Dict[str, int] = {}
    
    def __post_init__(self):
        if self.counters is None:
            object.__setattr__(self, 'counters', {})
    
    @property
    def code(self) -> str:
        """Return the card code"""
        return self.card.code
    
    @property
    def name(self) -> str:
        """Return the card name"""
        return self.card.name
    
    def move_to(self, new_position: Position) -> 'CardInPlay':
        """Return new instance with updated position"""
        return CardInPlay(
            card=self.card,
            position=new_position,
            counters=self.counters
        )
        
    def rotate(self, new_rotation: int) -> 'CardInPlay':
        """Return new instance with updated rotation"""
        new_position = Position(
            x=self.position.x,
            y=self.position.y,
            rotation=new_rotation,
            flip_state=self.position.flip_state
        )
        return CardInPlay(
            card=self.card,
            position=new_position,
            counters=self.counters
        )
        
    def flip(self, flipped: bool) -> 'CardInPlay':
        """Return new instance with updated flip state"""
        new_position = self.position.flip()
        return CardInPlay(
            card=self.card,
            position=new_position,
            counters=self.counters
            )
        
    def add_counter(self, counter_type: str, amount: int = 1) -> 'CardInPlay':
        """Add counters to a card"""
        new_counters = dict(self.counters)
        new_counters[counter_type] = new_counters.get(counter_type, 0) + amount
        
        return CardInPlay(
            card=self.card,
            position=self.position,
            counters=new_counters
        )