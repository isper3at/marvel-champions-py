"""Interactor to start a game."""
import uuid
from src.entities import Game
from src.boundaries.game_repository import GameRepository


class StartGameInteractor:
    """Start a game from lobby phase."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str, username: str) -> Game:
        """
        Start the game (host only).
        
        Transitions from LOBBY to IN_PROGRESS.
        
        Args:
            game_id: Lobby ID
            username: Username (must be host)
            
        Returns:
            Updated Game with status=IN_PROGRESS
            
        Raises:
            ValueError: If validation fails
        """
        try:
            game_uuid = uuid.UUID(game_id)
        except ValueError:
            raise ValueError("Invalid game ID")
        
        game = self.game_repo.find_by_id(game_uuid)
        if not game:
            raise ValueError("Lobby not found")
        
        # Verify user is host
        if username != game.host:
            raise ValueError("Only host can start game")
        
        # Verify can start
        if not game.can_start():
            reasons = []
            if not game.players:
                reasons.append("no players")
            if not game.all_players_ready():
                reasons.append("not all players ready")
            if not game.encounter_deck:
                reasons.append("no encounter deck selected")
            
            raise ValueError(f"Cannot start game: {', '.join(reasons)}")
        
        # Start the game
        started_game = game.start_game()
        
        return self.game_repo.save(started_game)
