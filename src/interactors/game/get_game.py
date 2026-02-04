"""Interactor to get a game by ID."""
from typing import Optional
import uuid
from src.entities import Game
from src.boundaries.game_repository import GameRepository


class GetGameInteractor:
    """Retrieve a game by ID."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str) -> Optional[Game]:
        """
        Get a game by ID.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Game entity or None if not found
        """
        try:
            game_uuid = uuid.UUID(game_id)
            return self.game_repo.find_by_id(game_uuid)
        except ValueError:
            return None
