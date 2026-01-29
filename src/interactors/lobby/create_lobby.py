"""Interactor to create a lobby."""
from src.entities import Game, GamePhase, Player
from src.boundaries.repository import GameRepository


class CreateLobbyInteractor:
    """Create a new game lobby."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, name: str, host: str) -> Game:
        """
        Create a new game lobby.
        
        Args:
            name: Game name
            host: Username of the host
            
        Returns:
            Created Game in LOBBY phase
        """
        host_player = Player(
            name=host,
            is_host=True,
            is_ready=False
        )
        
        game = Game(
            name=name,
            host=host,
            players=(host_player,)
        )
        
        return self.game_repo.save(game)
