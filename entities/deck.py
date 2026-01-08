from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class DeckCard:
    """Represents a card in a deck with quantity"""
    code: str
    quantity: int
    
    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")
        if self.quantity > 3:
            raise ValueError("Card quantity cannot exceed 3")


@dataclass(frozen=True)
class Deck:
    """
    Immutable domain entity representing a player deck.
    """
    id: Optional[str]
    name: str
    hero_code: str
    aspect: str  # justice, aggression, protection, leadership
    cards: tuple[DeckCard, ...]
    
    # Optional MarvelCDB reference
    marvelcdb_id: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Deck name cannot be empty")
        if not self.hero_code:
            raise ValueError("Hero code cannot be empty")
        if self.aspect not in ['justice', 'aggression', 'protection', 'leadership']:
            raise ValueError(f"Invalid aspect: {self.aspect}")
    
    def total_cards(self) -> int:
        """Calculate total number of cards in deck"""
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """Get list of all card codes with quantities expanded"""
        codes = []
        for deck_card in self.cards:
            codes.extend([deck_card.code] * deck_card.quantity)
        return codes
