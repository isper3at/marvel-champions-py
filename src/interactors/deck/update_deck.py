"""Interactor to update a deck."""
from src.entities import Deck
from src.boundaries.deck_repository import DeckRepository


class UpdateDeckInteractor:
    """Update an existing deck."""
    
    def __init__(self, deck_repo: DeckRepository):
        self.deck_repo = deck_repo
    
    def execute(self, deck: Deck) -> Deck:
        """
        Update a deck.
        
        Args:
            deck: Updated Deck entity
            
        Returns:
            Saved Deck entity
        """
        return self.deck_repo.save(deck)
