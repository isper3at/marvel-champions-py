"""Interactor to import a deck from MarvelCDB."""
from src.entities import DeckList
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway


class ImportDeckInteractor:
    """Import a deck from MarvelCDB."""
    
    def __init__(
        self,
        marvelcdb_gateway: MarvelCDBGateway
    ):
        self.marvelcdb = marvelcdb_gateway
    
    def execute(self, deck_id: str) -> DeckList:
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
        
        return deck_list
