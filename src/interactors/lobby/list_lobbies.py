"""Interactor to list lobbies."""
from typing import List
from src.entities import Game, GamePhase
from src.boundaries.game_repository import GameRepository


class ListLobbiesInteractor:
    """Get all active lobbies."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self) -> List[Game]:
        """
        Get all lobbies.
        
        Returns:
            List of Games in LOBBY phase
        """
        all_games = self.game_repo.find_all()
        return [g for g in all_games if g.phase == GamePhase.LOBBY]
