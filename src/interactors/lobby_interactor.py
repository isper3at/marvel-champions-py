"""
Lobby Interactor - Business logic for game lobby operations.

Responsibilities:
- Create lobbies
- Manage players joining/leaving
- Handle deck selection
- Manage ready status
- Start games when ready
"""

from typing import Optional, List
import random
from datetime import datetime

from src.boundaries.repository import GameRepository, DeckRepository
from src.entities import (
    Game, GameState, GamePhase, Player, PlayZone
)


class LobbyInteractor:
    """Business logic for lobby operations"""
    
    def __init__(
        self,
        game_repository: GameRepository,
        deck_repository: DeckRepository
    ):
        self.game_repo = game_repository
        self.deck_repo = deck_repository
    
    def create_lobby(self, name: str, host: str) -> Game:
        """
        Create a new game lobby.
        
        Args:
            name: Game name
            host: Username of the host
            
        Returns:
            Created Game in LOBBY status
        """
        # Create host as first player
        host_player = Player(
            username=host,
            is_host=True,
            is_ready=False
        )
        
        game = Game(
            id=None,
            name=name,
            status=GamePhase.LOBBY,
            host=host,
            players=(host_player,),
            created_at=datetime.utcnow()
        )
        
        return self.game_repo.save(game)
    
    def list_lobbies(self) -> List[Game]:
        """Get all lobbies (games with status=LOBBY)"""
        all_games = self.game_repo.find_all()
        return [g for g in all_games if g.status == GamePhase.LOBBY]
    
    def get_lobby(self, game_id: str) -> Optional[Game]:
        """Get a lobby by ID"""
        game = self.game_repo.find_by_id(game_id)
        
        if game and game.status == GamePhase.LOBBY:
            return game
        
        return None
    
    def join_lobby(self, game_id: str, username: str) -> Game:
        """
        Join an existing lobby.
        
        Args:
            game_id: Lobby to join
            username: Player username
            
        Returns:
            Updated Game
            
        Raises:
            ValueError: If lobby not found or player already in lobby
        """
        game = self.get_lobby(game_id)
        if not game:
            raise ValueError("Lobby not found or game already started")
        
        # Add player
        updated_game = game.add_player(username)
        
        return self.game_repo.save(updated_game)
    
    def leave_lobby(self, game_id: str, username: str) -> Optional[Game]:
        """
        Leave a lobby.
        
        If the host leaves, the lobby is deleted.
        If last player leaves, the lobby is deleted.
        
        Returns:
            Updated Game or None if lobby deleted
        """
        game = self.get_lobby(game_id)
        if not game:
            return None
        
        # If host leaves or last player, delete lobby
        if username == game.host or len(game.lobby_players) == 1:
            self.game_repo.delete(game_id)
            return None
        
        # Remove player
        updated_game = game.remove_player(username)
        
        return self.game_repo.save(updated_game)
    
    def choose_deck(self, game_id: str, username: str, deck_id: str) -> Game:
        """
        Choose a deck for a player.
        
        Args:
            game_id: Lobby ID
            username: Player username
            deck_id: Deck to use
            
        Returns:
            Updated Game
        """
        game = self.get_lobby(game_id)
        if not game:
            raise ValueError("Lobby not found")
        
        # Verify deck exists
        deck = self.deck_repo.find_by_id(deck_id)
        if not deck:
            raise ValueError("Deck not found")
        
        # Update player's deck
        player = game.get_lobby_player(username)
        if not player:
            raise ValueError("Player not in lobby")
        
        updated_player = player.with_deck(deck_id)
        updated_game = game.update_lobby_player(updated_player)
        
        return self.game_repo.save(updated_game)
    
    def set_encounter_deck(self, game_id: str, username: str, encounter_deck_id: str) -> Game:
        """
        Set the encounter deck (host only).
        
        Args:
            game_id: Lobby ID
            username: Username (must be host)
            encounter_deck_id: Encounter deck to use
            
        Returns:
            Updated Game
        """
        game = self.get_lobby(game_id)
        if not game:
            raise ValueError("Lobby not found")
        
        # Verify user is host
        if username != game.host:
            raise ValueError("Only host can set encounter deck")
        
        # Verify deck exists
        deck = self.deck_repo.find_by_id(encounter_deck_id)
        if not deck:
            raise ValueError("Encounter deck not found")
        
        # Update game
        from dataclasses import replace
        updated_game = replace(game, encounter_deck_id=encounter_deck_id)
        
        return self.game_repo.save(updated_game)
    
    def toggle_ready(self, game_id: str, username: str) -> Game:
        """
        Toggle player's ready status.
        
        Cannot ready if no deck chosen.
        
        Args:
            game_id: Lobby ID
            username: Player username
            
        Returns:
            Updated Game
        """
        game = self.get_lobby(game_id)
        if not game:
            raise ValueError("Lobby not found")
        
        player = game.get_lobby_player(username)
        if not player:
            raise ValueError("Player not in lobby")
        
        # Cannot ready without a deck
        if not player.deck_id and not player.is_ready:
            raise ValueError("Choose a deck before readying up")
        
        updated_player = player.toggle_ready()
        updated_game = game.update_lobby_player(updated_player)
        
        return self.game_repo.save(updated_game)
    
    def start_game(self, game_id: str, username: str) -> Game:
        """
        Start the game (host only).
        
        Transitions from LOBBY to IN_PROGRESS.
        Initializes game state with player decks.
        
        Args:
            game_id: Lobby ID
            username: Username (must be host)
            
        Returns:
            Updated Game with status=IN_PROGRESS
        """
        game = self.get_lobby(game_id)
        if not game:
            raise ValueError("Lobby not found")
        
        # Verify user is host
        if username != game.host:
            raise ValueError("Only host can start game")
        
        # Verify can start
        if not game.can_start():
            reasons = []
            if not game.lobby_players:
                reasons.append("no players")
            if not game.encounter_deck_id:
                reasons.append("no encounter deck")
            if not game.all_players_ready():
                reasons.append("not all players ready")
            
            raise ValueError(f"Cannot start game: {', '.join(reasons)}")
        
        # Load and shuffle decks
        player_zones = []
        deck_ids = []
        
        for lobby_player in game.lobby_players:
            # Load deck
            deck_result = self.deck_repo.find_by_id(lobby_player.deck_id)
            if not deck_result:
                raise ValueError(f"Deck not found for {lobby_player.username}")
            
            deck = deck_result
            deck_ids.append(lobby_player.deck_id)
            
            # Get card codes and shuffle
            card_codes = deck.get_card_codes()
            random.shuffle(card_codes)
            
            # Create player zones
            zones = PlayZone(
                player_name=lobby_player.username,
                deck=tuple(card_codes),
                hand=(),
                discard=(),
                removed=()
            )
            player_zones.append(zones)
        
        # Create initial game state
        initial_state = GameState(
            players=tuple(player_zones),
            play_area=()
        )
        
        # Update game to IN_PROGRESS
        from dataclasses import replace
        started_game = replace(
            game,
            status=GamePhase.IN_PROGRESS,
            deck_ids=tuple(deck_ids),
            state=initial_state,
            updated_at=datetime.utcnow()
        )
        
        return self.game_repo.save(started_game)
    
    def delete_lobby(self, game_id: str, username: str) -> bool:
        """
        Delete a lobby (host only).
        
        Args:
            game_id: Lobby ID
            username: Username (must be host)
            
        Returns:
            True if deleted
        """
        game = self.get_lobby(game_id)
        if not game:
            return False
        
        # Verify user is host
        if username != game.host:
            raise ValueError("Only host can delete lobby")
        
        return self.game_repo.delete(game_id)