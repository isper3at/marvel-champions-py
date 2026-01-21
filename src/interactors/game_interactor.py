"""
Game Interactor - Business logic for game operations.
"""

from typing import Optional, List
import random
from src.boundaries.repository import GameRepository
from src.entities import Game, GameState, GameStatus, PlayerZones, CardInPlay, Position
from .deck_interactor import DeckInteractor


class GameInteractor:
    """
    Coordinates game session management and state transformations.
    """
    
    def __init__(
        self,
        game_repository: GameRepository,
        deck_interactor: DeckInteractor
    ):
        """
        Initialize the GameInteractor with dependencies.
        
        Args:
            game_repository: Repository for persisting games
            deck_interactor: Interactor for loading deck card data
        """
        self.game_repo = game_repository
        self.deck_interactor = deck_interactor
    
    def create_game(
        self,
        game_name: str,
        deck_ids: List[str],
        player_names: List[str]
    ) -> Game:
        """
        Create and initialize a new game.
        """
        if len(deck_ids) != len(player_names):
            raise ValueError("Number of decks must match number of players")
        
        # Load decks and shuffle them
        players = []
        for deck_id, player_name in zip(deck_ids, player_names):
            deck_result = self.deck_interactor.get_deck_with_cards(deck_id)
            if not deck_result:
                raise ValueError(f"Deck {deck_id} not found")
            
            deck, cards = deck_result
            
            # Get all card codes and shuffle
            card_codes = deck.get_card_codes()
            random.shuffle(card_codes)
            
            # Create player zones
            player = PlayerZones(
                player_name=player_name,
                deck=tuple(card_codes),
                hand=(),
                discard=(),
                removed=()
            )
            players.append(player)
        
        # Create game state
        state = GameState(
            players=tuple(players),
            play_area=()
        )
        
        # Create game
        game = Game(
            id=None,
            name=game_name,
            status=GameStatus.IN_PROGRESS,
            host=player_names[0] if player_names else '',
            deck_ids=tuple(deck_ids),
            state=state
        )
        
        return self.game_repo.save(game)
    
    def get_game(self, game_id: str) -> Optional[Game]:
        """Retrieve a game by ID."""
        return self.game_repo.find_by_id(game_id)
    
    def get_all_games(self) -> List[Game]:
        """Retrieve all games from the repository."""
        return self.game_repo.find_all()
    
    def get_recent_games(self, limit: int = 10) -> List[Game]:
        """Get most recently modified games."""
        return self.game_repo.find_recent(limit)
    
    def save_game(self, game: Game) -> Game:
        """Save a game to the repository."""
        return self.game_repo.save(game)
    
    def delete_game(self, game_id: str) -> bool:
        """Delete a game from the repository."""
        return self.game_repo.delete(game_id)
    
    def draw_card(self, game_id: str, player_name: str) -> Optional[Game]:
        """Draw a card from a player's deck into their hand."""
        game = self.game_repo.find_by_id(game_id)
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
        
        # Create updated game using dataclass replace pattern
        from dataclasses import replace
        updated_game = replace(
            game,
            state=new_state
        )
        
        return self.game_repo.save(updated_game)
    
    def shuffle_discard_into_deck(self, game_id: str, player_name: str) -> Optional[Game]:
        """Shuffle a player's discard pile back into their deck."""
        game = self.game_repo.find_by_id(game_id)
        if not game:
            return None
        
        player = game.state.get_player(player_name)
        if not player:
            return game
        
        shuffled_player = player.shuffle_discard_into_deck()
        new_state = game.state.update_player(shuffled_player)
        
        from dataclasses import replace
        updated_game = replace(
            game,
            state=new_state
        )
        
        return self.game_repo.save(updated_game)
    
    def play_card_to_table(
        self,
        game_id: str,
        player_name: str,
        card_code: str,
        position: Position
    ) -> Optional[Game]:
        """Play a card from a player's hand to the table."""
        game = self.game_repo.find_by_id(game_id)
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
        
        updated_player = PlayerZones(
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
        updated_game = replace(
            game,
            state=new_state
        )
        
        return self.game_repo.save(updated_game)
    
    def move_card_on_table(
        self,
        game_id: str,
        card_code: str,
        new_position: Position
    ) -> Optional[Game]:
        """Move a card on the table to a new position."""
        game = self.game_repo.find_by_id(game_id)
        if not game:
            return None
        
        # Find and update the card
        new_play_area = tuple(
            card.with_position(new_position) if card.code == card_code else card
            for card in game.state.play_area
        )
        
        new_state = GameState(
            players=game.state.players,
            play_area=new_play_area
        )
        
        from dataclasses import replace
        updated_game = replace(
            game,
            state=new_state
        )
        
        return self.game_repo.save(updated_game)
    
    def toggle_card_rotation(self, game_id: str, card_code: str) -> Optional[Game]:
        """Toggle a card's rotation state (exhaust/ready)."""
        game = self.game_repo.find_by_id(game_id)
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
        updated_game = replace(
            game,
            state=new_state
        )
        
        return self.game_repo.save(updated_game)
    
    def add_counter_to_card(
        self,
        game_id: str,
        card_code: str,
        counter_type: str,
        amount: int = 1
    ) -> Optional[Game]:
        """Add or modify counters on a card (damage, threat, tokens, etc.)."""
        game = self.game_repo.find_by_id(game_id)
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
        updated_game = replace(
            game,
            state=new_state
        )
        
        return self.game_repo.save(updated_game)