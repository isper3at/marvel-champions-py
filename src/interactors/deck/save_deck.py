"""Interactor to import a deck from MarvelCDB."""
from src.entities import DeckList, Deck
from src.boundaries.deck_repository import DeckRepository


class SaveDeckInteractor:
    """Import a deck from MarvelCDB."""
    
    def __init__(
        self,
        deck_repository: DeckRepository
    ):
        self.deck_repository = deck_repository
    
    def execute(self, deck_list: DeckList) -> bool:
        saved_list = self.deck_repository.save(deck_list)

        if not saved_list:
            raise ValueError(f"Failed to save deck list: {deck_list.name}")
            return False

        return True