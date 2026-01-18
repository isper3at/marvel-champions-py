"""
Position entity - represents 2D coordinates on the play field.
"""

from dataclasses import dataclass
from enum import Enum

class FlipState(Enum):
    FACE_UP = 'face_up'
    FACE_DOWN = 'face_down'

@dataclass(frozen=True)
class Position:
    """
    2D position on the play field.
    
    Immutable coordinate pair used to track card positions
    on the virtual game board.
    
    Attributes:
        x: X coordinate (horizontal position)
        y: Y coordinate (vertical position)
        rotation: Angle of rotation in degrees
        flip_state: Orientation of the card (e.g., face up/down)
    
    Example:
        >>> pos = Position(x=100, y=200)
        >>> assert pos.x == 100
        >>> assert pos.y == 200
        >>> assert pos.rotation == 0
        >>> assert pos.flip_state == FlipState.FACE_UP
    """
    x: int
    y: int
    rotation: int = 0
    flip_state: FlipState = FlipState.FACE_UP

    def __post_init__(self):
        """Validate coordinates"""
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            raise ValueError("Position coordinates must be integers")
        
    def flip(self) -> 'Position':
        """Return new Position with updated flip state"""
        new_flip_state = (FlipState.FACE_DOWN
                           if self.flip_state == FlipState.FACE_UP 
                           else FlipState.FACE_UP)
        return Position(
            x=self.x,
            y=self.y,
            rotation=self.rotation,
            flip_state=new_flip_state
        )