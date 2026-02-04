"""Interactor to get a card by code."""
from typing import Optional
from src.entities import Card
from src.boundaries.card_repository import CardRepository


class GetCardInteractor:
    """Retrieve a card by its code from the repository."""
    
    def __init__(self, card_repo: CardRepository):
        self.card_repo = card_repo
    
    def execute(self, card_code: str) -> Optional[Card]:
        """
        Get a card by its code.
        
        Args:
            card_code: Card identifier
            
        Returns:
            Card entity or None if not found
        """
        return self.card_repo.find_by_code(card_code)
