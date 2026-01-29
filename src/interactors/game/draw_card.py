"""Interactor to draw a card."""
from typing import Optional
import uuid
from src.entities import Game
from src.boundaries.repository import GameRepository


class DrawCardInteractor:
    """Draw a card from a player's deck."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(self, game_id: str, player_name: str) -> Optional[Game]:
        """
        Draw a card from a player's deck into their hand.
        
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
        
        # Get the player
        player = game.state.get_player(player_name)
        if not player:
            return game
        
        # Draw card from player's deck
        updated_player, drawn_card = player.draw_card()
        
        if not drawn_card:
            # No card to draw (deck empty)
            return game
        
        # Update game state with new player zones
        new_state = game.state.update_player(updated_player)
        
        from dataclasses import replace
        updated_game = replace(game, state=new_state)
        
        return self.game_repo.save(updated_game)
