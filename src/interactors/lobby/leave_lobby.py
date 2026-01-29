"""Interactor to leave a lobby."""
from typing import Optional
import uuid
from src.entities import Game, GamePhase
from src.boundaries.repository import GameRepository


class LeaveLobbyInteractor:
    """Leave a lobby."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str, username: str) -> Optional[Game]:
        """
        Leave a lobby.
        
        If host leaves or last player leaves, lobby is deleted.
        
        Args:
            game_id: Lobby ID
            username: Player username
            
        Returns:
            Updated Game or None if lobby deleted
        """
        try:
            game_uuid = uuid.UUID(game_id)
        except ValueError:
            return None
        
        game = self.game_repo.find_by_id(game_uuid)
        
        if not game:
            return None
        
        # If host leaves or last player, delete lobby
        if username == game.host or len(game.players) == 1:
            self.game_repo.delete(game_uuid)
            return None
        
        # Find and remove player
        player = next((p for p in game.players if p.name == username), None)
        if not player:
            return game
        
        updated_game = game.remove_player(player)
        
        return self.game_repo.save(updated_game)
