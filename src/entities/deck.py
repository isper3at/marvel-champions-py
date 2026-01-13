from dataclasses import dataclass
from typing import Optional
from datetime import datetime


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
    code: str  # Card identifier from MarvelCDB
    quantity: int  # How many copies in the deck
    
    def __post_init__(self):
        """Validate that quantity is at least 1."""
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")


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
        id: Unique identifier (from database)
        name: Display name for the deck
        cards: Tuple of DeckCard entries (immutable)
        source_url: Optional link to external deck (e.g., MarvelCDB)
        created_at: When deck was created
        updated_at: When deck was last modified
    
    Architecture:
    - Entity: This class (data structure)
    - Interactor: DeckInteractor handles deck operations
    - Boundary: MarvelCDB gateway imports external decks
    - Repository: Stores decks for persistence
    
    Example:
        >>> deck_card = DeckCard(code='01001a', quantity=2)
        >>> deck = Deck(
        ...     id='deck123',
        ...     name='Spider-Man Control',
        ...     cards=(deck_card,)
        ... )
        >>> assert deck.total_cards() == 2
        >>> assert '01001a' in deck.get_card_codes()
    """
    id: Optional[str]
    name: str
    cards: tuple[DeckCard, ...]  # Immutable list of card entries
    
    # Optional reference to where this deck came from
    source_url: Optional[str] = None  # e.g., "https://marvelcdb.com/deck/view/12345"
    
    # Audit trail for tracking creation and modifications
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate that deck has a non-empty name."""
        if not self.name:
            raise ValueError("Deck name cannot be empty")
    
    def total_cards(self) -> int:
        """
        Calculate total number of card copies in this deck.
        
        Returns the sum of all quantities across all DeckCard entries.
        
        Returns:
            Total count of cards (accounting for quantities)
            
        Example:
            >>> deck = Deck(
            ...     id='deck1',
            ...     name='My Deck',
            ...     cards=(
            ...         DeckCard('01001a', 2),
            ...         DeckCard('01002b', 1)
            ...     )
            ... )
            >>> assert deck.total_cards() == 3
        """
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """
        Get list of all card codes with quantities expanded.
        
        Returns a flat list where each card code appears once for each copy
        in the deck. This is useful for shuffling/drawing operations.
        
        Returns:
            List of card codes (with duplicates per quantity)
            
        Example:
            >>> deck = Deck(
            ...     id='deck1',
            ...     name='My Deck',
            ...     cards=(
            ...         DeckCard('01001a', 2),
            ...         DeckCard('01002b', 1)
            ...     )
            ... )
            >>> codes = deck.get_card_codes()
            >>> assert codes.count('01001a') == 2
            >>> assert codes.count('01002b') == 1
            >>> assert len(codes) == 3
        """
        codes = []
        for deck_card in self.cards:
            codes.extend([deck_card.code] * deck_card.quantity)
        return codes