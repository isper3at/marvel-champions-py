"""Interactor to add a counter to a card."""
from typing import Optional
import uuid
from src.entities import Game, GameState
from src.boundaries.repository import GameRepository


class AddCounterInteractor:
    """Add or modify counters on a card."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(
        self,
        game_id: str,
        card_code: str,
        counter_type: str,
        amount: int = 1
    ) -> Optional[Game]:
        """
        Add or modify counters on a card.
        
        Args:
            game_id: Game ID
            card_code: Card to add counter to
            counter_type: Type of counter (damage, threat, tokens, etc.)
            amount: Number of counters to add
            
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
            card.add_counter(counter_type, amount) if card.code == card_code else card
            for card in game.state.play_area
        )
        
        new_state = GameState(
            players=game.state.players,
            play_area=new_play_area
        )
        
        from dataclasses import replace
        updated_game = replace(game, state=new_state)
        
        return self.game_repo.save(updated_game)
