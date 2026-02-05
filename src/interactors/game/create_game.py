"""Interactor to create a game."""
from typing import List
import random
from src.entities import Game, GamePhase, PlayZone
from src.boundaries.game_repository import GameRepository
from src.boundaries.deck_repository import DeckRepository

class CreateGameInteractor:
    """Create and initialize a new game."""
    
    def __init__(
        self,
        game_repo: GameRepository,
        deck_repo: DeckRepository
    ):
        self.game_repo = game_repo
        self.deck_repo = deck_repo
    
    def execute(
        self,
        game_name: str,
        deck_ids: List[str],
        player_names: List[str]
    ) -> Game:
        """
        Create and initialize a new game.
        
        Args:
            game_name: Name of the game
            deck_ids: List of deck IDs for each player
            player_names: List of player names
            
        Returns:
            Created Game
            
        Raises:
            ValueError: If deck count doesn't match player count
        """
        if len(deck_ids) != len(player_names):
            raise ValueError("Number of decks must match number of players")
        
        # Load decks and shuffle them
        players = []
        for deck_id, player_name in zip(deck_ids, player_names):
            deck = self.deck_repo.find_by_id(deck_id)
            if not deck:
                raise ValueError(f"Deck {deck_id} not found")
            
            # Get all card codes and shuffle
            card_codes = deck.get_card_codes()
            random.shuffle(card_codes)
            
            # Create player zones
            player = PlayZone(
                player_name=player_name,
                deck=tuple(card_codes),
                hand=(),
                discard=(),
                removed=()
            )
            players.append(player)
        
        # Create game state
        from src.entities import GameState
        state = GameState(
            players=tuple(players),
            play_area=()
        )
        
        # Create game
        game = Game(
            name=game_name,
            phase=GamePhase.IN_PROGRESS,
            host=player_names[0] if player_names else '',
            deck_ids=tuple(deck_ids),
            state=state
        )
        
        return self.game_repo.save(game)
