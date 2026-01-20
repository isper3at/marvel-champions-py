"""
Deck Interactor - Business logic for deck operations.

This module implements the Interactor layer for deck management. It coordinates
operations between:
- Repository: Persistent storage of Deck entities
- MarvelCDB Gateway: Importing decks from the external deck-building site
- CardInteractor: Ensuring all deck cards are imported before deck is saved

Key responsibilities:
- Import decks from MarvelCDB (with automatic card import)
- Create/update/delete user-created decks
- Provide complete deck data (deck + card entities)

All operations maintain the principle that decks and cards are immutable entities.
Modifications return new instances rather than mutating existing ones.
"""

from typing import Optional, List
from src.boundaries.repository import DeckRepository, CardRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.entities import Deck, DeckCard
from .card_interactor import CardInteractor


class DeckInteractor:
    """
    Coordinates deck operations across repository and gateway boundaries.
    
    DeckInteractor is responsible for:
    1. Importing decks from MarvelCDB (external deck builder site)
    2. Creating and managing user decks
    3. Ensuring all deck cards are available locally
    4. Providing complete deck information (deck + card entities)
    
    The key principle: This interactor intelligently manages the relationship
    between Deck entities (which reference cards by code) and Card entities
    (which contain card metadata).
    
    Attributes:
        deck_repo: Repository for persisting decks
        card_interactor: Interactor for managing cards
        marvelcdb: Gateway to MarvelCDB API
    
    Example Usage:
        >>> interactor = DeckInteractor(deck_repo, card_interactor, gateway)
        >>> deck = interactor.create_deck('My Deck', [('01001a', 2), ('01002b', 1)])
        >>> full_deck = interactor.get_deck_with_cards('deck123')
    """
    
    def __init__(
        self,
        deck_repository: DeckRepository,
        card_interactor: CardInteractor,
        marvelcdb_gateway: MarvelCDBGateway
    ):
        self.deck_repo = deck_repository
        self.card_interactor = card_interactor
        self.marvelcdb = marvelcdb_gateway
    
    def import_deck_from_marvelcdb(self, deck_id: str) -> Deck:
        """
        Import a deck from MarvelCDB, including all its cards.
        
        This operation:
        1. Fetches deck composition from MarvelCDB
        2. Imports all cards in the deck (with images)
        3. Creates Deck entity referencing the cards
        4. Saves deck to repository
        
        Process:
        - Checks if deck exists in repository first (returns if found)
        - Fetches fresh deck list from MarvelCDB
        - Bulk imports all cards (efficient, minimizes API calls)
        - Creates DeckCard entries for each card with proper quantities
        - Saves to repository with link back to source
        
        Args:
            deck_id: MarvelCDB deck ID (from URL: marvelcdb.com/decklist/view/{deck_id})
            
        Returns:
            Deck entity with all cards imported and cached
            
        Raises:
            ValueError: If deck not found on MarvelCDB
            Exception: If MarvelCDB API fails
            
        Example:
            >>> deck = interactor.import_deck_from_marvelcdb('12345')
            >>> assert deck.total_cards() > 0
            >>> assert deck.source_url  # Contains link to original
        """
        # Fetch deck cards
        deck_details = self.marvelcdb.get_deck_details(deck_id)
        
        if not deck_details:
            raise ValueError(f"No cards found for deck {deck_id}")
                
        # Save deck
        saved_deck = self.deck_repo.save(deck_details)
        
        return saved_deck
    
    def get_deck(self, deck_id: str) -> Optional[Deck]:
        """
        Retrieve a deck by its ID.
        
        This returns the Deck entity which contains card references (codes)
        but not the full Card entities. Use get_deck_with_cards() if you need
        the complete card data.
        
        Args:
            deck_id: Deck identifier
            
        Returns:
            Deck entity or None if not found
        """
        return self.deck_repo.find_by_id(deck_id)
    
    def get_all_decks(self) -> List[Deck]:
        """
        Retrieve all decks from the repository.
        
        Returns:
            List of all Deck entities
        """
        return self.deck_repo.find_all()
    
    def update_deck(self, deck: Deck) -> Deck:
        """
        Save an updated deck to the repository.
        
        Since Deck entities are immutable, you typically modify them using
        dataclasses.replace() and then call this method to persist changes.
        
        Args:
            deck: Deck entity to save
            
        Returns:
            Saved deck (may have updated timestamp/id from repository)
            
        Example:
            >>> import dataclasses
            >>> updated_deck = dataclasses.replace(
            ...     deck,
            ...     name='New Name'
            ... )
            >>> saved = interactor.update_deck(updated_deck)
        """
        return self.deck_repo.save(deck)
    
    def delete_deck(self, deck_id: str) -> bool:
        """
        Delete a deck from the repository.
        
        Args:
            deck_id: Deck to delete
            
        Returns:
            True if deletion succeeded, False if deck not found
        """
        return self.deck_repo.delete(deck_id)
    
    def get_deck_with_cards(self, deck_id: str) -> Optional[tuple[Deck, List]]:
        """
        Get a deck along with all its Card entities.
        
        This is the primary way to get complete deck information suitable for
        displaying to users. It combines:
        - Deck metadata (name, timestamps)
        - Complete Card entities (names, text, etc)
        
        Process:
        1. Fetch Deck entity (contains card codes and quantities)
        2. Fetch all Card entities for those codes
        3. Return both for complete information
        
        Args:
            deck_id: Deck to retrieve
            
        Returns:
            Tuple of (Deck, List[Card]) with all cards, or None if deck not found
            Cards list may contain duplicates matching deck quantities.
            
        Example:
            >>> result = interactor.get_deck_with_cards('deck123')
            >>> if result:
            ...     deck, cards = result
            ...     for card in cards:
            ...         print(f"Card: {card.name}")
        """
        deck = self.deck_repo.find_by_id(deck_id)
        if not deck:
            return None
        
        # Get all card entities
        card_codes = deck.get_card_codes()
        cards = self.card_interactor.get_cards(card_codes)
        
        return deck, cards