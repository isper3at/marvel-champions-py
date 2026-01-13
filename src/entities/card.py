from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Card:
    """
    Minimal card representation.
    No rules enforcement - just enough data to identify and display cards.
    Players know the rules; we just need to show them the cards.
    """
    code: str  # Unique identifier (e.g., "01001a")
    name: str  # For accessibility and display
    text: Optional[str] = None  # For accessibility/screen readers
    
    # Audit trail
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validation logic"""
        if not self.code:
            raise ValueError("Card code cannot be empty")
        if not self.name:
            raise ValueError("Card name cannot be empty")