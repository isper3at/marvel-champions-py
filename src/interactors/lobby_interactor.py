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
import uuid
import random
from datetime import datetime

from src.boundaries.repository import GameRepository, DeckRepository
from src.gateways.marvelcdb_client import MarvelCDBClient
from src.entities import Game, GamePhase, Player, PlayZone, EncounterDeck


class LobbyInteractor:
    """Business logic for lobby operations"""
    
    def __init__(
        self,
        game_repository: GameRepository,
        deck_repository: DeckRepository,
        marvelcdb_api: MarvelCDBClient
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
        # Create host as first player with UUID-based string ID
        host_player = Player(
            name=host,
            is_host=True,
            is_ready=False
        )
        
        game = Game(
            name=name,
            host=host,
            players=(host_player,)
        )
        
        return self.game_repo.save(game)
    
    def list_lobbies(self) -> List[Game]:
        """Get all lobbies (games with status=LOBBY)"""
        all_games = self.game_repo.find_all()
        return [g for g in all_games if g.phase == GamePhase.LOBBY]
    
    def get_lobby(self, game_id: uuid.UUID) -> Optional[Game]:
        """Get a lobby by ID"""
        game = self.game_repo.find_by_id(game_id)
        
        if game and game.phase == GamePhase.LOBBY:
            return game
        
        return None
    
    def _get_player_by_name(self, game: Game, name: str) -> Optional[Player]:
        """Find a player in the game by name"""
        for player in game.players:
            if player.name == name:
                return player
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
        
        # Check if player already in lobby
        if self._get_player_by_name(game, username):
            raise ValueError(f"Player {username} already in lobby")
        
        # Create new player
        new_player = Player(
            name=username,
            is_host=False,
            is_ready=False
        )
        
        # Add player
        updated_game = game.add_player(new_player)
        
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
        if username == game.host or len(game.players) == 1:
            self.game_repo.delete(str(game.id))
            return None
        
        # Find and remove player
        player = self._get_player_by_name(game, username)
        if not player:
            return game  # Player not in lobby, return unchanged
        
        updated_game = game.remove_player(player)
        
        return self.game_repo.save(updated_game)
    
    def build_encounter_deck(self, module_names: List[str]) -> EncounterDeck:
        """
        Build a random encounter deck for the lobby.
        
        Args:
            game_id: Lobby ID
            deck_ids: List of encounter deck IDs to choose from
        """
        encounter_deck = None
        for module_name in module_names:
            if not encounter_deck:
                encounter_deck = self.marvelcdb_api.get_module(module_name)
            else:
                encounter_deck = encounter_deck.join_encounter_deck(self.marvelcdb_api.get_module(module_name))
            
        return encounter_deck
    
    def set_encounter_deck(self, game_id: str, encounter_deck: EncounterDeck) -> Game:
        """
        Set the encounter deck for the lobby.
        
        Args:
            game_id: Lobby ID
            encounter_deck: Encounter deck to use.
        """
        game = self.get_lobby(game_id)
        if not game:
            raise ValueError("Lobby not found or game already started")

        # Update encounter deck
        updated_game = game.set_encounter_deck(encounter_deck)

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
        
        # Find player and update with deck
        player = self._get_player_by_name(game, username)
        if not player:
            raise ValueError("Player not in lobby")
        
        updated_player = player.play_deck(deck)
        updated_game = game.update_player(updated_player)
        
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
        
        player = self._get_player_by_name(game, username)
        if not player:
            raise ValueError("Player not in lobby")
        
        # Cannot ready without a deck
        if player.deck is None and not player.is_ready:
            raise ValueError("Choose a deck before readying up")
        
        updated_player = player.toggle_ready()
        updated_game = game.update_player(updated_player)
        
        return self.game_repo.save(updated_game)
    
    def start_game(self, game_id: str, username: str) -> Game:
        """
        Start the game (host only).
        
        Transitions from LOBBY to IN_PROGRESS.
        
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
            if not game.players:
                reasons.append("no players")
            if not game.all_players_ready():
                reasons.append("not all players ready")
            if not game.encounter_deck:
                reasons.append("no encounter deck selected")
            
            raise ValueError(f"Cannot start game: {', '.join(reasons)}")
        
        # Start the game
        started_game = game.start_game()
        
        return self.game_repo.save(started_game)

    def delete_lobby(self, game_id: uuid.UUID, username: str) -> bool:
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
        
        return self.game_repo.delete(game.id)