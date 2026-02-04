"""
CardInPlay entity - represents a card on the game board with state.
"""

from dataclasses import dataclass
from typing import List
from .card import Card
from .position import Position
from .token import Token
from uuid import uuid4


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
    card_id: str
    position: Position
    
    def __post_init__(self):
        object.__setattr__(self, 'card_id', uuid4().hex)

    @staticmethod
    def from_card(card: Card, position: Position) -> 'CardInPlay':
        """Create a CardInPlay instance from a Card and Position."""
        return CardInPlay(
            card_id=uuid4().hex,
            card=card,
            position=position
        )

    @property
    def id(self) -> str:
        """Return the unique ID of this CardInPlay instance"""
        return self.card_id    

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
            card_id=self.card_id,
            card=self.card,
            position=new_position
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
            card_id=self.card_id,
            card=self.card,
            position=new_position,
        )
        
    def flip(self) -> 'CardInPlay':
        """Return new instance with updated flip state"""
        new_position = self.position.flip()
        return CardInPlay(
            card_id=self.card_id,
            card=self.card,
            position=new_position
            )