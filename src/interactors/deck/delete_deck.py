"""Interactor to delete a deck."""
from src.boundaries.deck_repository import DeckRepository


class DeleteDeckInteractor:
    """Delete a deck from the repository."""
    
    def __init__(self, deck_repo: DeckRepository):
        self.deck_repo = deck_repo
    
    def execute(self, deck_id: str) -> bool:
        """
        Delete a deck by ID.
        
        Args:
            deck_id: Deck to delete
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        return self.deck_repo.delete(deck_id)
