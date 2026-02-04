"""Interactor to toggle player ready status."""
import uuid
from src.entities import Game
from src.boundaries.game_repository import GameRepository


class ToggleReadyInteractor:
    """Toggle player's ready status in lobby."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str, username: str) -> Game:
        """
        Toggle player's ready status.
        
        Cannot ready without a deck chosen.
        
        Args:
            game_id: Lobby ID
            username: Player username
            
        Returns:
            Updated Game
            
        Raises:
            ValueError: If lobby or player not found, or validation fails
        """
        try:
            game_uuid = uuid.UUID(game_id)
        except ValueError:
            raise ValueError("Invalid game ID")
        
        game = self.game_repo.find_by_id(game_uuid)
        if not game:
            raise ValueError("Lobby not found")
        
        player = next((p for p in game.players if p.name == username), None)
        if not player:
            raise ValueError("Player not in lobby")
        
        # Cannot ready without a deck
        if player.deck is None and not player.is_ready:
            raise ValueError("Choose a deck before readying up")
        
        updated_player = player.toggle_ready()
        updated_game = game.update_player(updated_player)
        
        return self.game_repo.save(updated_game)
