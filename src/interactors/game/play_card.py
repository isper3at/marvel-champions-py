"""Interactor to play a card to the table."""
from typing import Optional
import uuid
from src.entities import Game, CardInPlay, Position, PlayZone, GameState
from src.boundaries.repository import GameRepository


class PlayCardInteractor:
    """Play a card from a player's hand to the table."""
    
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
    
    def execute(
        self,
        game_id: str,
        player_name: str,
        card_code: str,
        position: Position
    ) -> Optional[Game]:
        """
        Play a card from a player's hand to the table.
        
        Args:
            game_id: Game ID
            player_name: Name of player
            card_code: Card to play
            position: Position on table
            
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
        if not player or card_code not in player.hand:
            return game
        
        # Remove from hand (remove first occurrence only)
        hand_list = list(player.hand)
        try:
            hand_list.remove(card_code)
        except ValueError:
            return game
        
        updated_player = PlayZone(
            player_name=player.player_name,
            deck=player.deck,
            hand=tuple(hand_list),
            discard=player.discard,
            removed=player.removed
        )
        
        # Add to play area
        card_in_play = CardInPlay(code=card_code, position=position)
        new_play_area = game.state.play_area + (card_in_play,)
        
        # Update state
        new_state = GameState(
            players=tuple(
                updated_player if p.player_name == player_name else p
                for p in game.state.players
            ),
            play_area=new_play_area
        )
        
        from dataclasses import replace
        updated_game = replace(game, state=new_state)
        
        return self.game_repo.save(updated_game)
