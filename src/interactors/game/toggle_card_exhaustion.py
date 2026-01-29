"""Interactor to toggle card exhaustion."""
from typing import Optional
import uuid
from src.entities import Game, GameState
from src.boundaries.repository import GameRepository


class ToggleCardExhaustionInteractor:
    """Toggle a card's exhaustion state."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str, card_code: str) -> Optional[Game]:
        """
        Toggle a card's rotation state (exhaust/ready).
        
        Args:
            game_id: Game ID
            card_code: Card to toggle
            
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
        
        new_play_area = tuple(
            card.with_exhausted(not card.exhausted) if card.code == card_code else card
            for card in game.state.play_area
        )
        
        new_state = GameState(
            players=game.state.players,
            play_area=new_play_area
        )
        
        from dataclasses import replace
        updated_game = replace(game, state=new_state)
        
        return self.game_repo.save(updated_game)
