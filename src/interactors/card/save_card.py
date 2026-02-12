"""Interactor to import a deck from MarvelCDB."""
from src.entities import Card
from src.boundaries.card_repository import CardRepository


class SaveCardInteractor:
    """Save a card to a CardRepository."""
    
    def __init__(
        self,
        card_repository: CardRepository
    ):
        self.card_repository = card_repository
    
    def execute(self, card: Card) -> bool:
        saved_card = self.card_repository.save(card)

        if not saved_card:
            raise ValueError(f"Failed to save deck list: {card.name}")
            return False

        return True