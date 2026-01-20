"""
Game Interactor - Business logic for game operations.

This module implements the Interactor layer for game session management. It coordinates:
- Repository: Persisting game state
- DeckInteractor: Loading decks and initializing player zones
- Entity layer: Creating and transforming immutable game entities

Key design principles:
- NO game rules enforcement (no validation of legal moves)
- Pure state management (game state is immutable)
- Each operation returns a new Game entity
- All player actions are allowed if they modify the state without errors

The GameInteractor philosophy: "Track state, don't enforce rules. Players know the rules."
This allows for flexible game variations, house rules, and experimenting with different mechanics.

Responsibilities:
- Initialize new games from deck lists and player names
- Persist and retrieve game state
- Provide game action methods that transform state
- Draw cards, play cards, move cards, apply counters
"""

from typing import Optional, List
import random
from src.boundaries.repository import GameRepository
from src.entities import Game, GameState, PlayerZones, CardInPlay, Position
from .deck_interactor import DeckInteractor


class GameInteractor:
    """
    Coordinates game session management and state transformations.
    
    GameInteractor is the central coordinator for all game operations:
    1. Creating new games from decks and players
    2. Retrieving and persisting game state
    3. Applying player actions (draw, play, move, modify cards)
    
    Important: This interactor enforces NO game rules. It's purely a state
    transformer. If you want to play cards that cost 10 with 2 resources, it
    won't stop you. Players (or UI validation) should enforce rules.
    
    This design enables:
    - Testing various rules scenarios
    - Supporting house rules and variants
    - Flexible gameplay (no hardcoded Marvel Champions rules)
    - Easy addition of new card actions
    
    Attributes:
        game_repo: Repository for persisting games
        deck_interactor: Interactor for loading deck information
    
    Example Usage:
        >>> interactor = GameInteractor(repo, deck_interactor)
        >>> game = interactor.create_game('Game 1', ['deck1', 'deck2'], ['Alice', 'Bob'])
        >>> game = interactor.draw_card(game.id, 'Alice')
        >>> game = interactor.play_card_to_table(game.id, 'Alice', '01001a', Position(0, 0))
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
        game: Game
    ) -> Game:
        """
        Create and initialize a new game.
        
        This operation:
        1. Validates that number of decks matches number of players
        2. Loads each deck and its cards
        3. Shuffles each deck into a player's initial deck zone
        4. Creates PlayerZones for each player (deck loaded, hand/discard empty)
        5. Initializes empty play area
        6. Creates Game entity and saves to repository
        
        Process:
        - Load decks in order, matching to player_names
        - Shuffle card codes for each player's deck
        - Create immutable PlayerZones for each player
        - Initialize GameState with all players
        - Create Game entity with empty play area
        - Persist to repository
        
        Args:
            game_name: Display name for the game session
            deck_ids: List of deck IDs (one per player, in order)
            player_names: List of player names (in same order as deck_ids)
            
        Returns:
            Saved Game entity with initialized state
            
        Raises:
            ValueError: If deck/player counts don't match or deck not found
            
        Example:
            >>> game = interactor.create_game(
            ...     'Alice vs Bob',
            ...     ['deck1', 'deck2'],
            ...     ['Alice', 'Bob']
            ... )
            >>> assert len(game.state.players) == 2
            >>> assert game.state.play_area == ()  # Empty initially
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
        """
        Retrieve a game by ID.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Game entity or None if not found
        """
        return self.game_repo.find_by_id(game_id)
    
    def get_all_games(self) -> List[Game]:
        """
        Retrieve all games from the repository.
        
        Returns:
            List of all Game entities
        """
        return self.game_repo.find_all()
    
    def get_recent_games(self, limit: int = 10) -> List[Game]:
        """
        Get most recently modified games.
        
        Args:
            limit: Maximum number of games to return (default 10)
            
        Returns:
            List of Game entities, ordered by most recent first
        """
        return self.game_repo.find_recent(limit)
    
    def save_game(self, game: Game) -> Game:
        """
        Save a game to the repository.
        
        This updates the game state and timestamps. Typically called after
        applying game actions to persist changes.
        
        Args:
            game: Game entity to save
            
        Returns:
            Saved game (may have updated timestamps from repository)
        """
        return self.game_repo.save(game)
    
    def delete_game(self, game_id: str) -> bool:
        """
        Delete a game from the repository.
        
        Args:
            game_id: Game to delete
            
        Returns:
            True if deletion succeeded, False if game not found
        """
        return self.game_repo.delete(game_id)
    
    # ========================================================================
    # Game Actions - Apply state transformations without rules enforcement
    # ========================================================================
    # These methods transform game state. None enforce game rules.
    # Invalid moves (e.g., drawing from empty deck) are handled gracefully.
    # ========================================================================
    
    def draw_card(self, game_id: str, player_name: str) -> Optional[Game]:
        """
        Draw a card from a player's deck into their hand.
        
        If player deck is empty, no change occurs and game is returned unchanged.
        
        State transformation:
        - Player's deck: Remove first card
        - Player's hand: Add drawn card
        - Everything else: Unchanged
        
        Args:
            game_id: Game to modify
            player_name: Player drawing the card
            
        Returns:
            Updated Game entity or None if game not found
            
        Example:
            >>> game = interactor.draw_card(game.id, 'Alice')
            >>> # If successful, Alice has one more card in hand
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
        """
        Shuffle a player's discard pile back into their deck.
        
        This is useful when a player runs out of cards to draw. After this
        operation:
        - Player's deck: Now contains all original + discarded cards (shuffled)
        - Player's discard: Empty
        
        Args:
            game_id: Game to modify
            player_name: Player whose discard to shuffle
            
        Returns:
            Updated Game entity or None if game not found
        """
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
        Play a card from a player's hand to the table.
        
        This operation:
        - Removes card from player's hand (first occurrence)
        - Adds CardInPlay to the shared play_area at the given position
        - No validation that player actually has the card
        
        State transformation:
        - Player's hand: Card removed
        - Play area: New CardInPlay added at position
        - All other zones: Unchanged
        
        Args:
            game_id: Game to modify
            player_name: Player playing the card
            card_code: Code of card to play
            position: Position on table (Position object with x, y coordinates)
            
        Returns:
            Updated Game entity or None if game not found
            
        Example:
            >>> pos = Position(x=1, y=2)
            >>> game = interactor.play_card_to_table(game.id, 'Alice', '01001a', pos)
            >>> # Alice's hand card '01001a' is now on table at (1, 2)
        """
        game = self.game_repo.find_by_id(game_id)
        if not game:
            return None
        
        player = game.state.get_player(player_name)
        if not player or card_code not in player.hand:
            return game
        
        # Remove from hand (remove first occurrence only)
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
        """
        Move a card on the table to a new position.
        
        Finds the first CardInPlay with matching code and updates its position.
        
        State transformation:
        - Only updates position of the card
        - Rotation, flip, counters: Unchanged
        - All other game state: Unchanged
        
        Args:
            game_id: Game to modify
            card_code: Code of card to move (first occurrence)
            new_position: New Position (x, y) on table
            
        Returns:
            Updated Game entity or None if game not found
            
        Example:
            >>> new_pos = Position(x=3, y=4)
            >>> game = interactor.move_card_on_table(game.id, '01001a', new_pos)
            >>> # Card is now at the new position
        """
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
        """
        Toggle a card's rotation state (exhaust/ready).
        
        This is purely visual state - rotation itself has no game effects.
        Players decide what rotation means in their rules.
        
        State transformation:
        - Rotated: Toggle (True -> False, False -> True)
        - All other card state: Unchanged
        
        Args:
            game_id: Game to modify
            card_code: Code of card to rotate (first occurrence)
            
        Returns:
            Updated Game entity or None if game not found
            
        Example:
            >>> game = interactor.toggle_card_rotation(game.id, '01001a')
            >>> # Card is now rotated (or unrotated if it was rotated)
        """
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
        """
        Add or modify counters on a card (damage, threat, tokens, etc.).
        
        Counters are generic and application-defined. The meaning of each
        counter type is determined entirely by the UI and player rules.
        
        State transformation:
        - Counters: Updated (added/subtracted)
        - All other card state: Unchanged
        
        Args:
            game_id: Game to modify
            card_code: Code of card to add counter to (first occurrence)
            counter_type: Name of counter (e.g., 'damage', 'threat')
            amount: How many to add (default 1). Can be negative to subtract.
            
        Returns:
            Updated Game entity or None if game not found
            
        Example:
            >>> game = interactor.add_counter_to_card(game.id, '01001a', 'damage', 3)
            >>> # Card now has 3 damage counters
            >>> game = interactor.add_counter_to_card(game.id, '01001a', 'damage', -1)
            >>> # Card now has 2 damage counters
        """
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