"""
Deck Interactor - Business logic for deck operations.

Responsibilities:
- Import decks from MarvelCDB
- Create/update/delete decks
- Ensure all deck cards are imported
"""

from typing import Optional, List
from src.boundaries.repository import DeckRepository, CardRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.entities import Deck, DeckCard
from .card_interactor import CardInteractor


class DeckInteractor:
    """Business logic for deck operations"""
    
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
        Import a deck from MarvelCDB.
        
        Steps:
        1. Fetch deck cards from MarvelCDB
        2. Import all cards (ensures we have card data and images)
        3. Create Deck entity
        4. Save to repository
        
        Returns:
            Imported Deck entity
        """
        # Fetch deck cards
        deck_cards = self.marvelcdb.get_deck_cards(deck_id)
        
        if not deck_cards:
            raise ValueError(f"No cards found for deck {deck_id}")
        
        # Import all cards
        card_codes = [c['code'] for c in deck_cards]
        self.card_interactor.import_cards_bulk(card_codes)
        
        # Create deck entity
        deck = Deck(
            id=None,
            name=f"Imported Deck {deck_id}",  # MarvelCDB doesn't always give us the name easily
            cards=tuple(
                DeckCard(code=c['code'], quantity=c['quantity'])
                for c in deck_cards
            ),
            source_url=f"https://marvelcdb.com/decklist/view/{deck_id}"
        )
        
        # Save deck
        saved_deck = self.deck_repo.save(deck)
        
        return saved_deck
    
    def get_user_decks_from_marvelcdb(self, session_cookie: str) -> List[dict]:
        """
        Get list of user's decks from MarvelCDB.
        
        Args:
            session_cookie: MarvelCDB session cookie
            
        Returns:
            List of deck info: [{'id': '...', 'name': '...'}, ...]
        """
        self.marvelcdb.set_session_cookie(session_cookie)
        return self.marvelcdb.get_user_decks()
    
    def create_deck(self, name: str, card_codes_with_qty: List[tuple[str, int]]) -> Deck:
        """
        Create a new deck.
        
        Args:
            name: Deck name
            card_codes_with_qty: List of (card_code, quantity) tuples
            
        Returns:
            Created Deck entity
        """
        # Ensure all cards exist
        card_codes = [code for code, _ in card_codes_with_qty]
        self.card_interactor.import_cards_bulk(card_codes)
        
        # Create deck
        deck = Deck(
            id=None,
            name=name,
            cards=tuple(
                DeckCard(code=code, quantity=qty)
                for code, qty in card_codes_with_qty
            )
        )
        
        return self.deck_repo.save(deck)
    
    def get_deck(self, deck_id: str) -> Optional[Deck]:
        """Get a deck by ID"""
        return self.deck_repo.find_by_id(deck_id)
    
    def get_all_decks(self) -> List[Deck]:
        """Get all decks"""
        return self.deck_repo.find_all()
    
    def update_deck(self, deck: Deck) -> Deck:
        """Update an existing deck"""
        return self.deck_repo.save(deck)
    
    def delete_deck(self, deck_id: str) -> bool:
        """Delete a deck"""
        return self.deck_repo.delete(deck_id)
    
    def get_deck_with_cards(self, deck_id: str) -> Optional[tuple[Deck, List]]:
        """
        Get a deck with all its card entities.
        
        Returns:
            Tuple of (Deck, List[Card]) or None if deck not found
        """
        deck = self.deck_repo.find_by_id(deck_id)
        if not deck:
            return None
        
        # Get all card entities
        card_codes = deck.get_card_codes()
        cards = self.card_interactor.get_cards(card_codes)
        
        return deck, cards