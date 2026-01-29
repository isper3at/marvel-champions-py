"""Interactor to get a deck by ID."""
from typing import Optional
from src.entities import Deck
from src.boundaries.repository import DeckRepository


class GetDeckInteractor:
    """Retrieve a deck by its ID."""
    
    def __init__(self, deck_repo: DeckRepository):
        self.deck_repo = deck_repo
    
    def execute(self, deck_id: str) -> Optional[Deck]:
        """
        Get a deck by its ID.
        
        Args:
            deck_id: Deck identifier
            
        Returns:
            Deck entity or None if not found
        """
        return self.deck_repo.find_by_id(deck_id)
