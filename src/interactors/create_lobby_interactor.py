"""CreateLobbyInteractor - creates a new game lobby"""

from src.boundaries.repository import GameRepository
from src.entities import Game, GamePhase, Player

class CreateLobbyInteractor:
    """
    Single responsibility: Create a new game lobby.
    
    Example:
        >>> interactor = CreateLobbyInteractor(game_repo)
        >>> game = interactor.execute(name='My Game', host='Alice')
    """
    
    def __init__(self, game_repository: GameRepository):
        self.game_repo = game_repository
    
    def execute(self, name: str, host: str) -> Game:
        """
        Create a new lobby.
        
        Args:
            name: Game name
            host: Host username
        
        Returns:
            Created Game in LOBBY phase
        """
        host_player = Player(
            username=host,
            is_host=True,
            is_ready=False
        )
        
        game = Game(
            id=None,
            name=name,
            phase=GamePhase.LOBBY,
            host=host,
            players=(host_player,),
            encounter_deck_id=None
        )
        
        return self.game_repo.save(game)