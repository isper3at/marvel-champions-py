from typing import Optional
from src.entities import Deck
from src.boundaries.repository import DeckRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway


class GetDeckInteractor():
    """
    Interactor for retrieving a Deck by its ID.
    """
    deck_repo: DeckRepository
    marvelcdb_client: MarvelCDBGateway

    def __init__(self, deck_repo: DeckRepository, marvelcdb_client: MarvelCDBGateway):
        self.deck_repo = deck_repo
        self.marvelcdb_client = marvelcdb_client

    def get(self, deck_id: str, update: bool) -> Optional[Deck]:
        """
        Retrieve a deck by its ID.
        
        This returns the Deck entity which contains card references (codes)
        but not the full Card entities. Use get_deck_with_cards() if you need
        the complete card data.
        
        Args:
            deck_id: Deck identifier
            update: Whether to fetch the latest data from MarvelCDB
            
        Returns:
            Deck entity or None if not found
        """

        found_deck: Optional[Deck] = None
        found_deck = self.deck_repo.find_by_id(deck_id)
        
        if found_deck is None or update:
            # Fetch from MarvelCDB
            fetched_deck = self.marvelcdb_client.get_deck(deck_id)
            if fetched_deck is not None:
                self.deck_repo.save(fetched_deck)

        return fetched_deck