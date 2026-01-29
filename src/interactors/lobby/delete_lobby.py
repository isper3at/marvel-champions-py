"""Interactor to delete a lobby."""
import uuid
from src.boundaries.repository import GameRepository


class DeleteLobbyInteractor:
    """Delete a lobby (host only)."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str, username: str) -> bool:
        """
        Delete a lobby.
        
        Args:
            game_id: Lobby ID
            username: Username (must be host)
            
        Returns:
            True if deleted, False otherwise
            
        Raises:
            ValueError: If user is not host
        """
        try:
            game_uuid = uuid.UUID(game_id)
        except ValueError:
            return False
        
        game = self.game_repo.find_by_id(game_uuid)
        if not game:
            return False
        
        # Verify user is host
        if username != game.host:
            raise ValueError("Only host can delete lobby")
        
        return self.game_repo.delete(game_uuid)
