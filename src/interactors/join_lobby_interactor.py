from src.boundaries.repository import GameRepository
from src.entities import Game, GamePhase, Player

class JoinLobbyInteractor:
    """
    Single responsibility: Join an existing game lobby.
    
    Example:
        >>> interactor = JoinLobbyInteractor(game_repo)
        >>> game = interactor.execute(game_id='game123', player_id='p01')
    """
    def __init__(self, game_repository: GameRepository):
        self.game_repo = game_repository
    
    def execute(self, game_id: str, player: Player) -> Game:
        game = self.game_repo.find_by_id(game_id)
        if not game:
            raise ValueError("Game not found")
        
        if game.phase != GamePhase.LOBBY:
            raise ValueError("Can only join games in lobby phase")
        
        """If the player is not already in the game"""
        if any(p.id == player.id for p in game.players):
            raise ValueError("Player already in lobby")