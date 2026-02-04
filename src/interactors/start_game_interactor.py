"""StartGameInteractor - transitions lobby to active game"""

from typing import Optional
from src.boundaries.game_repository import GameRepository, DeckRepository
from src.entities import Game, GamePhase, Player, ActiveGame, DeckInPlay


class StartGameInteractor:
    """
    Single responsibility: Start a game from lobby.
    
    Example:
        >>> interactor = StartGameInteractor(game_repo, deck_repo)
        >>> game = interactor.execute(game_id='game123', host='Alice')
    """
    
    def __init__(
        self,
        game_repository: GameRepository,
        deck_repository: DeckRepository
    ):
        self.game_repo = game_repository
        self.deck_repo = deck_repository
    
    def execute(self, game_id: str, host: str) -> Optional[Game]:
        """
        Start a game from lobby.
        
        Args:
            game_id: Game ID
            host: Host username (must match)
        
        Returns:
            Game in ACTIVE phase or None if not found
        """
        game = self.game_repo.find_by_id(game_id)
        if not game:
            return None
        
        if game.host != host:
            raise ValueError("Only host can start game")
        
        if not game.can_start():
            reasons = []
            if not game.players:
                reasons.append("no players")
            if not game.encounter_deck_id:
                reasons.append("no encounter deck")
            if not game.all_players_ready():
                reasons.append("not all players ready")
            raise ValueError(f"Cannot start game: {', '.join(reasons)}")
        
        # Load decks and create DeckInPlay for each player
        players_with_decks = []
        for player in game.players:
            if not player.deck_id:
                continue
            
            deck = self.deck_repo.find_by_id(player.deck_id)
            if not deck:
                raise ValueError(f"Deck {player.deck_id} not found for {player.username}")
            
            # Create DeckInPlay and shuffle
            deck_in_play = DeckInPlay.from_deck(deck, shuffle=True)
            
            # Create new player with deck in play
            game_player = Player(
                username=player.username,
                is_host=player.is_host,
                deck_id=player.deck_id,
                is_ready=player.is_ready,
                deck_in_play=deck_in_play
            )
            
            players_with_decks.append(game_player)
        
        # Create active game
        active_game = ActiveGame(
            players=tuple(players_with_decks),
            play_area=()
        )
        
        # Transition to ACTIVE phase
        started_game = Game(
            id=game.id,
            name=game.name,
            phase=GamePhase.ACTIVE,
            host=game.host,
            players=tuple(players_with_decks),
            encounter_deck_id=game.encounter_deck_id,
            active_game=active_game,
            created_at=game.created_at,
            updated_at=game.updated_at
        )
        
        return self.game_repo.save(started_game)