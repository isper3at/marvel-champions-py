"""Interactor to list all games."""
from typing import List
from src.entities import Game
from src.boundaries.repository import GameRepository


class ListGamesInteractor:
    """Retrieve all games from the repository."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self) -> List[Game]:
        """
        Get all games.
        
        Returns:
            List of all Game entities
        """
        return self.game_repo.find_all()
