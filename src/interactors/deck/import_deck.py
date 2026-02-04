"""Interactor to import a deck from MarvelCDB."""
from src.entities import Deck
from src.boundaries.deck_repository import DeckRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway


class ImportDeckInteractor:
    """Import a deck from MarvelCDB."""
    
    def __init__(
        self,
        deck_repo: DeckRepository,
        marvelcdb_gateway: MarvelCDBGateway
    ):
        self.deck_repo = deck_repo
        self.marvelcdb = marvelcdb_gateway
    
    def execute(self, deck_id: str) -> Deck:
        """
        Import a deck from MarvelCDB.
        
        Args:
            deck_id: MarvelCDB deck ID
            
        Returns:
            Imported Deck entity
        """
        deck_list = self.marvelcdb.get_deck(deck_id)
        
        if not deck_list:
            raise ValueError(f"No deck found for {deck_id}")
        
        # Convert DeckList to Deck and save
        deck = self.marvelcdb.get_deck(deck_id)
        saved_deck = self.deck_repo.save(deck)
        
        return saved_deck
