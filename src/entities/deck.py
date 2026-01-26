from dataclasses import dataclass, field
from typing import Optional
import datetime

from src.entities.card import Card

@dataclass(frozen=True)
class DeckCard:
    """
    A single card entry in a deck with its quantity.
    
    DeckCard represents one line in a deck list - a specific card code
    along with how many copies of that card are in the deck. This is
    used to efficiently store deck compositions without duplicating
    card data for each copy.
    
    Attributes:
        code: Card identifier (e.g., "01001a")
        quantity: How many copies of this card are in the deck
    
    Example:
        >>> deck_card = DeckCard(code='01001a', quantity=2)
        >>> assert deck_card.quantity == 2
        # This means 2 copies of card 01001a in the deck
    """
    code: str
    name: str
    quantity: int
    
    def __post_init__(self):
        """Validate that quantity is at least 1."""
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")

@dataclass(frozen=True)
class DeckList:
    """
    A simple list of DeckCard entries.
    
    DeckList is used to represent a collection of cards in a deck
    without additional metadata. It is useful for intermediate
    representations, such as when fetching deck data from external
    sources.
    
    Attributes:
        id: Unique identifier for the deck list
        name: Display name for the deck list
        cards: List of DeckCard entries
    
    Example:
        >>> deck_list = DeckList(
        ...     id='deck123',
        ...     name='Test Deck List',
        ...     cards=[
        ...         DeckCard(code='01001a', name='1', quantity=2),
        ...         DeckCard(code='01002a', name='2', quantity=1),
        ...     ]
        ... )
    """
    cards: list[DeckCard]
    id: str
    name: str
    
    def card_count(self) -> int:
        """
        Get total number of unique card entries in the deck list.
        
        Returns the count of distinct DeckCard entries.
        """
        count=0
        for card in self.cards:
            count += card.quantity
        return count
    
@dataclass(frozen=True)
class Deck:
    """
    A collection of cards forming a playable deck.
    
    Deck represents a Marvel Champions deck that a player can use in games.
    It contains no game rules or deck-building constraints - just a list of
    cards. This allows for:
    - Experimental/house-ruled deck building
    - Proxying and testing different combinations
    - Flexibility for different game variants
    
    Attributes:
        id: Unique identifier (required, must match MarvelCDB id if imported)
        name: Display name for the deck
        cards: List of DeckCard entries
        source_url: Optional link to external deck (e.g., MarvelCDB)
        created_at: When deck was created
        updated_at: When deck was last modified
    
    Example:
        >>> deck_card = DeckCard(code='01001a', quantity=2)
        >>> deck = Deck(
        ...     id='marvelcdb-12345',
        ...     name='Spider-Man Control',
        ...     cards=[deck_card]
        ... )
        >>> assert deck.total_cards() == 2
        >>> assert '01001a' in deck.get_card_codes()
    """
    id: str
    name: str
    cards: list[Card]
    source_url: Optional[str] = None
    created_at: Optional[datetime.datetime] = field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        """Validate that deck has a non-empty name."""
        if not self.name:
            raise ValueError("Deck name cannot be empty")
        if not self.id:
            raise ValueError("Deck id cannot be empty")
    
    def total_cards(self) -> int:
        """
        Calculate total number of card copies in this deck.
        
        Returns the sum of all quantities across all DeckCard entries.
        """
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """
        Get list of all card codes with quantities expanded.
        
        Returns a flat list where each card code appears once for each copy
        in the deck. This is useful for shuffling/drawing operations.
        """
        codes = []
        for deck_card in self.cards:
            codes.extend([deck_card.code] * deck_card.quantity)
        return codes