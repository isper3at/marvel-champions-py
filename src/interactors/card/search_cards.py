"""Interactor to search cards by name."""
from typing import List
from src.entities import Card
from src.boundaries.card_repository import CardRepository


class SearchCardsInteractor:
    """Search for cards by name substring."""
    
    def __init__(self, card_repo: CardRepository):
        self.card_repo = card_repo
    
    def execute(self, name: str) -> List[Card]:
        """
        Search cards by name.
        
        Args:
            name: Name or partial name to search for
            
        Returns:
            List of matching Card entities
        """
        return self.card_repo.search_by_name(name)
