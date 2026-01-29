"""Interactor to shuffle discard into deck."""
from typing import Optional
import uuid
from src.entities import Game
from src.boundaries.repository import GameRepository


class ShuffleDiscardInteractor:
    """Shuffle a player's discard pile back into their deck."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str, player_name: str) -> Optional[Game]:
        """
        Shuffle a player's discard pile back into their deck.
        
        Args:
            game_id: Game ID
            player_name: Name of player
            
        Returns:
            Updated Game or None if game not found
        """
        try:
            game_uuid = uuid.UUID(game_id)
        except ValueError:
            return None
        
        game = self.game_repo.find_by_id(game_uuid)
        if not game:
            return None
        
        player = game.state.get_player(player_name)
        if not player:
            return game
        
        shuffled_player = player.shuffle_discard_into_deck()
        new_state = game.state.update_player(shuffled_player)
        
        from dataclasses import replace
        updated_game = replace(game, state=new_state)
        
        return self.game_repo.save(updated_game)
