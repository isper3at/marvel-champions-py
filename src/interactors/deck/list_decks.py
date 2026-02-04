"""Interactor to list all decks."""
from typing import List
from src.entities import Deck
from src.boundaries.deck_repository import DeckRepository


class ListDecksInteractor:
    """Retrieve all decks from the repository."""
    
    def __init__(self, deck_repo: DeckRepository):
        self.deck_repo = deck_repo
    
    def execute(self) -> List[Deck]:
        """
        Get all decks.
        
        Returns:
            List of all Deck entities
        """
        return self.deck_repo.find_all()
