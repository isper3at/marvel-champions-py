from typing import Optional
from src.entities import Card
from src.boundaries.repository import CardRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway


class GetCardInteractor:
    """
    Interactor for retrieving a Card.
    """
    card_repo: CardRepository
    marvelcdb_client: MarvelCDBGateway

    def __init__(self, card_repo: CardRepository, marvelcdb_client: MarvelCDBGateway):
        self.card_repo = card_repo
        self.marvelcdb_client = marvelcdb_client

    def get(self, card_id: str, update: bool=False) -> Optional[Card]:
        """
        Retrieve a card by its ID.
        
        This returns the Card entity.
        
        Args:
            card_id: Card identifier
            update: Whether to fetch the latest data from MarvelCDB
            
        Returns:
            Card entity or None if not found
        """


        found_card = self.card_repo.find_by_code(card_id)
        
        if update or found_card is None:
            found_card = fetched_deck = self.marvelcdb_client.get_card_from_code(card_id)
            self.card_repo.save(found_card)

        return found_card