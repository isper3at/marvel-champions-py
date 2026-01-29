"""Interactor to save a game."""
from src.entities import Game
from src.boundaries.repository import GameRepository


class SaveGameInteractor:
    """Save a game to the repository."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game: Game) -> Game:
        """
        Save a game.
        
        Args:
            game: Game entity to save
            
        Returns:
            Saved Game entity
        """
        return self.game_repo.save(game)
