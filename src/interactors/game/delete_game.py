"""Interactor to delete a game."""
import uuid
from src.boundaries.repository import GameRepository


class DeleteGameInteractor:
    """Delete a game from the repository."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str) -> bool:
        """
        Delete a game by ID.
        
        Args:
            game_id: Game to delete
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            game_uuid = uuid.UUID(game_id)
            return self.game_repo.delete(game_uuid)
        except ValueError:
            return False
