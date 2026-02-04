from typing import Optional
from src.entities import DeckList
from src.entities import DeckCard
from src.boundaries.game_repository import DeckRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway


class GetDeckList():
    """
    Interactor for retrieving a DeckList.
    """
    deck_repo: DeckRepository
    marvelcdb_client: MarvelCDBGateway

    def __init__(self, deck_repo: DeckRepository, marvelcdb_client: MarvelCDBGateway):
        self.deck_repo = deck_repo
        self.marvelcdb_client = marvelcdb_client

    def get(self, deck_id: str, update: bool) -> Optional[DeckList]:
        """
        Retrieve a DeckList by its ID.
        
        This returns the DeckList entity.
        
        Args:
            deck_id: Deck identifier
            update: Whether to fetch the latest data from MarvelCDB
            
        Returns:
            DeckList entity or None if not found
        """


        found_deck_list = self.deck_repo.find_list_by_id(deck_id)
        
        if update or found_deck_list is None:
            found_deck_list = fetched_deck = self.marvelcdb_client.get_deck_list(deck_id)
            self.deck_repo.save_deck_list(found_deck_list)

        return found_deck_list