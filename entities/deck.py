from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class DeckCard:
    """A card reference with quantity"""
    code: str
    quantity: int
    
    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")


@dataclass(frozen=True)
class Deck:
    """
    A collection of cards.
    No aspect, hero, or deck-building rules enforced.
    Players can build whatever they want.
    """
    id: Optional[str]
    name: str
    cards: tuple[DeckCard, ...]
    
    # Optional reference to where this came from
    source_url: Optional[str] = None  # e.g., MarvelCDB link
    
    # Audit trail
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Deck name cannot be empty")
    
    def total_cards(self) -> int:
        """Calculate total number of cards in deck"""
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """Get list of all card codes with quantities expanded"""
        codes = []
        for deck_card in self.cards:
            codes.extend([deck_card.code] * deck_card.quantity)
        return codes