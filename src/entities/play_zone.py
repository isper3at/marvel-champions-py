"""
PlayZone entity - represents a zone on the play field where cards and decks can be manipulated.
"""

from dataclasses import dataclass
from typing import Tuple
from .deck_in_play import DeckInPlay
from .card_in_play import CardInPlay

@dataclass(frozen=True)
class PlayZone:
    """
    Represents a zone on the play field.
    
    Immutable - create new instance for state changes.
    
    Attributes:
        id: Unique identifier for the play zone
        name: Display name for the zone
    """
    decks_in_play: Tuple[str, DeckInPlay]  # Tuple of Deck IDs in this zone
    cards_in_play: Tuple[str, CardInPlay]  # Tuple of CardInPlay IDs in this zone