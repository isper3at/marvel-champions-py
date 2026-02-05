"""Interactor to retrieving a lobby."""
import uuid
from src.boundaries.game_repository import GameRepository
from src.entities.game import Game
from typing import Optional

class GetLobbyInteractor:
    """Get a lobby."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str) -> Optional[Game]:
        """
        Get a lobby.
        
        Args:
            game_id: Lobby ID
            
        Returns:
            True if deleted, False otherwise
            
        Raises:
            ValueError: If user is not host
        """
        try:
            game_uuid = uuid.UUID(game_id)
        except ValueError:
            return None
        
        return self.game_repo.find_by_id(game_uuid)
        
