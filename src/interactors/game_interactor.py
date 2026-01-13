"""
Game Interactor - Business logic for game operations.

Responsibilities:
- Create new games
- Load/save game state
- Perform game actions (draw card, play card, etc.)
- No rules enforcement - just state management
"""

from typing import Optional, List
import random
from src.boundaries.repository import GameRepository
from src.entities import Game, GameState, PlayerZones, CardInPlay, Position
from .deck_interactor import DeckInteractor


class GameInteractor:
    """Business logic for game operations"""
    
    def __init__(
        self,
        game_repository: GameRepository,
        deck_interactor: DeckInteractor
    ):
        self.game_repo = game_repository
        self.deck_interactor = deck_interactor
    
    def create_game(
        self,
        game_name: str,
        deck_ids: List[str],
        player_names: List[str]
    ) -> Game:
        """
        Create a new game.
        
        Args:
            game_name: Name of the game
            deck_ids: List of deck IDs (one per player)
            player_names: List of player names
            
        Returns:
            Created Game entity
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
            deck_ids=tuple(deck_ids),
            state=state
        )
        
        return self.game_repo.save(game)
    
    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a game by ID"""
        return self.game_repo.find_by_id(game_id)
    
    def get_all_games(self) -> List[Game]:
        """Get all games"""
        return self.game_repo.find_all()
    
    def get_recent_games(self, limit: int = 10) -> List[Game]:
        """Get recent games"""
        return self.game_repo.find_recent(limit)
    
    def save_game(self, game: Game) -> Game:
        """Save game state"""
        return self.game_repo.save(game)
    
    def delete_game(self, game_id: str) -> bool:
        """Delete a game"""
        return self.game_repo.delete(game_id)
    
    # ========================================================================
    # Game Actions - No rules enforced, just state manipulation
    # ========================================================================
    
    def draw_card(self, game_id: str, player_name: str) -> Optional[Game]:
        """
        Draw a card for a player.
        
        Returns:
            Updated Game or None if game not found
        """
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
        
        updated_game = Game(
            id=game.id,
            name=game.name,
            deck_ids=game.deck_ids,
            state=new_state,
            created_at=game.created_at
        )
        
        return self.game_repo.save(updated_game)
    
    def shuffle_discard_into_deck(self, game_id: str, player_name: str) -> Optional[Game]:
        """Shuffle a player's discard pile into their deck"""
        game = self.game_repo.find_by_id(game_id)
        if not game:
            return None
        
        player = game.state.get_player(player_name)
        if not player:
            return game
        
        shuffled_player = player.shuffle_discard_into_deck()
        new_state = game.state.update_player(shuffled_player)
        
        updated_game = Game(
            id=game.id,
            name=game.name,
            deck_ids=game.deck_ids,
            state=new_state,
            created_at=game.created_at
        )
        
        return self.game_repo.save(updated_game)
    
    def play_card_to_table(
        self,
        game_id: str,
        player_name: str,
        card_code: str,
        position: Position
    ) -> Optional[Game]:
        """
        Play a card from hand to the table.
        
        Args:
            game_id: Game ID
            player_name: Player playing the card
            card_code: Card to play
            position: Position on the table
            
        Returns:
            Updated Game or None
        """
        game = self.game_repo.find_by_id(game_id)
        if not game:
            return None
        
        player = game.state.get_player(player_name)
        if not player or card_code not in player.hand:
            return game
        
        # Remove from hand
        new_hand = tuple(c for c in player.hand if c != card_code or player.hand.index(c) != player.hand.index(card_code))
        updated_player = PlayerZones(
            player_name=player.player_name,
            deck=player.deck,
            hand=new_hand,
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
        
        updated_game = Game(
            id=game.id,
            name=game.name,
            deck_ids=game.deck_ids,
            state=new_state,
            created_at=game.created_at
        )
        
        return self.game_repo.save(updated_game)
    
    def move_card_on_table(
        self,
        game_id: str,
        card_code: str,
        new_position: Position
    ) -> Optional[Game]:
        """Move a card to a new position on the table"""
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
        
        updated_game = Game(
            id=game.id,
            name=game.name,
            deck_ids=game.deck_ids,
            state=new_state,
            created_at=game.created_at
        )
        
        return self.game_repo.save(updated_game)
    
    def toggle_card_rotation(self, game_id: str, card_code: str) -> Optional[Game]:
        """Toggle card rotation (exhaust/ready)"""
        game = self.game_repo.find_by_id(game_id)
        if not game:
            return None
        
        new_play_area = tuple(
            card.with_rotated(not card.rotated) if card.code == card_code else card
            for card in game.state.play_area
        )
        
        new_state = GameState(
            players=game.state.players,
            play_area=new_play_area
        )
        
        updated_game = Game(
            id=game.id,
            name=game.name,
            deck_ids=game.deck_ids,
            state=new_state,
            created_at=game.created_at
        )
        
        return self.game_repo.save(updated_game)
    
    def add_counter_to_card(
        self,
        game_id: str,
        card_code: str,
        counter_type: str,
        amount: int = 1
    ) -> Optional[Game]:
        """Add counters to a card (damage, threat, etc.)"""
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
        
        updated_game = Game(
            id=game.id,
            name=game.name,
            deck_ids=game.deck_ids,
            state=new_state,
            created_at=game.created_at
        )
        
        return self.game_repo.save(updated_game)