"""Interactor to join a lobby."""
from typing import Optional
import uuid
from src.entities import Game, GamePhase, Player
from src.boundaries.game_repository import GameRepository


class JoinLobbyInteractor:
    """Join an existing lobby."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str, username: str) -> Game:
        """
        Join an existing lobby.
        
        Args:
            game_id: Lobby ID
            username: Player username
            
        Returns:
            Updated Game
            
        Raises:
            ValueError: If lobby not found or player already joined
        """
        try:
            game_uuid = uuid.UUID(game_id)
        except ValueError:
            raise ValueError("Invalid game ID")
        
        game = self.game_repo.find_by_id(game_uuid)
        
        if not game or game.phase != GamePhase.LOBBY:
            raise ValueError("Lobby not found or game already started")
        
        # Check if player already in lobby
        if any(p.name == username for p in game.players):
            raise ValueError(f"Player {username} already in lobby")
        
        # Create new player
        new_player = Player(
            name=username,
            is_host=False,
            is_ready=False
        )
        
        # Add player and save
        updated_game = game.add_player(new_player)
        
        return self.game_repo.save(updated_game)
