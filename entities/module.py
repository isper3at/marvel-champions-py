from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class ModuleCard:
    """Represents a card in a module with quantity"""
    code: str
    quantity: int
    
    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")


@dataclass(frozen=True)
class Module:
    """
    Immutable domain entity representing an encounter module.
    Modules are mixed into encounter decks for variety.
    """
    id: Optional[str]
    name: str
    set_code: str
    cards: tuple[ModuleCard, ...]
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Module name cannot be empty")
        if not self.set_code:
            raise ValueError("Set code cannot be empty")
    
    def total_cards(self) -> int:
        """Calculate total number of cards in module"""
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """Get list of all card codes with quantities expanded"""
        codes = []
        for mod_card in self.cards:
            codes.extend([mod_card.code] * mod_card.quantity)
        return codes
