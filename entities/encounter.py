from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class EncounterCard:
    """Represents a card in an encounter deck with quantity"""
    code: str
    quantity: int
    
    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")


@dataclass(frozen=True)
class Encounter:
    """
    Immutable domain entity representing an encounter set.
    """
    id: Optional[str]
    name: str
    villain_code: str
    cards: tuple[EncounterCard, ...]
    
    # Metadata
    set_code: Optional[str] = None
    difficulty: Optional[str] = None  # standard, expert
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Encounter name cannot be empty")
        if not self.villain_code:
            raise ValueError("Villain code cannot be empty")
    
    def total_cards(self) -> int:
        """Calculate total number of cards in encounter"""
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """Get list of all card codes with quantities expanded"""
        codes = []
        for enc_card in self.cards:
            codes.extend([enc_card.code] * enc_card.quantity)
        return codes
