"""
Updated Game entity with lobby support.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from src.entities.lobby import GameStatus, LobbyPlayer


@dataclass(frozen=True)
class Position:
    """2D position on the play field"""
    x: int
    y: int


@dataclass(frozen=True)
class CardInPlay:
    """
    Represents a card in play with its state.
    Immutable - create new instance for state changes.
    """
    code: str
    position: Position
    exhausted: bool = False
    flipped: bool = False
    counters: dict[str, int] = None
    
    def __post_init__(self):
        # Handle mutable default
        if self.counters is None:
            object.__setattr__(self, 'counters', {})
    
    def with_position(self, position: Position) -> 'CardInPlay':
        """Create new instance with updated position"""
        return CardInPlay(
            code=self.code,
            position=position,
            exhausted=self.exhausted,
            flipped=self.flipped,
            counters=self.counters
        )
    
    def with_exhausted(self, exhausted: bool) -> 'CardInPlay':
        """Create new instance with updated exhausted state"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            exhausted=exhausted,
            flipped=self.flipped,
            counters=self.counters
        )
    
    def with_flipped(self, flipped: bool) -> 'CardInPlay':
        """Create new instance with updated flip state"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            exhausted=self.exhausted,
            flipped=flipped,
            counters=self.counters
        )
    
    def add_counter(self, counter_type: str, amount: int = 1) -> 'CardInPlay':
        """Add counters to a card"""
        new_counters = dict(self.counters)
        new_counters[counter_type] = new_counters.get(counter_type, 0) + amount
        
        return CardInPlay(
            code=self.code,
            position=self.position,
            exhausted=self.exhausted,
            flipped=self.flipped,
            counters=new_counters
        )


@dataclass(frozen=True)
class PlayerZones:
    """
    One player's zones (deck, hand, discard).
    Each player in a multiplayer game has their own zones.
    """
    player_name: str
    deck: tuple[str, ...]
    hand: tuple[str, ...]
    discard: tuple[str, ...]
    removed: tuple[str, ...] = ()
    
    def draw_card(self) -> tuple['PlayerZones', Optional[str]]:
        """Draw a card from this player's deck"""
        if not self.deck:
            return self, None
        
        drawn = self.deck[0]
        new_deck = self.deck[1:]
        new_hand = self.hand + (drawn,)
        
        return PlayerZones(
            player_name=self.player_name,
            deck=new_deck,
            hand=new_hand,
            discard=self.discard,
            removed=self.removed
        ), drawn
    
    def shuffle_discard_into_deck(self) -> 'PlayerZones':
        """Shuffle discard pile into deck"""
        import random
        combined = list(self.deck) + list(self.discard)
        random.shuffle(combined)
        
        return PlayerZones(
            player_name=self.player_name,
            deck=tuple(combined),
            hand=self.hand,
            discard=(),
            removed=self.removed
        )


@dataclass(frozen=True)
class GameState:
    """
    Game state - supports any number of players.
    Only populated when game status is IN_PROGRESS.
    """
    players: tuple[PlayerZones, ...]
    play_area: tuple[CardInPlay, ...]
    
    def get_player(self, player_name: str) -> Optional[PlayerZones]:
        """Get a specific player's zones"""
        for player in self.players:
            if player.player_name == player_name:
                return player
        return None
    
    def update_player(self, updated_player: PlayerZones) -> 'GameState':
        """Update a player's zones, returning new game state"""
        new_players = tuple(
            updated_player if p.player_name == updated_player.player_name else p
            for p in self.players
        )
        
        return GameState(
            players=new_players,
            play_area=self.play_area
        )


@dataclass(frozen=True)
class Game:
    """
    Game entity with lobby support.
    
    Lifecycle:
    1. LOBBY - Players join, choose decks, ready up
    2. IN_PROGRESS - Game is being played
    3. FINISHED - Game completed
    """
    id: Optional[str]
    name: str
    status: GameStatus
    host: str  # Username of host
    
    # Lobby phase (status = LOBBY)
    lobby_players: tuple[LobbyPlayer, ...] = ()
    encounter_deck_id: Optional[str] = None
    
    # Active game phase (status = IN_PROGRESS)
    deck_ids: tuple[str, ...] = ()
    state: Optional[GameState] = None
    
    # Audit trail
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Game name cannot be empty")
        if not self.host:
            raise ValueError("Host cannot be empty")
    
    def get_lobby_player(self, username: str) -> Optional[LobbyPlayer]:
        """Get a player from the lobby"""
        for player in self.lobby_players:
            if player.username == username:
                return player
        return None
    
    def add_player(self, username: str) -> 'Game':
        """Add a player to the lobby"""
        if self.status != GameStatus.LOBBY:
            raise ValueError("Can only add players in lobby phase")
        
        # Check if already in lobby
        if self.get_lobby_player(username):
            raise ValueError(f"Player {username} already in lobby")
        
        new_player = LobbyPlayer(username=username, is_host=False)
        
        return Game(
            id=self.id,
            name=self.name,
            status=self.status,
            host=self.host,
            lobby_players=self.lobby_players + (new_player,),
            encounter_deck_id=self.encounter_deck_id,
            deck_ids=self.deck_ids,
            state=self.state,
            created_at=self.created_at
        )
    
    def remove_player(self, username: str) -> 'Game':
        """Remove a player from the lobby"""
        if self.status != GameStatus.LOBBY:
            raise ValueError("Can only remove players in lobby phase")
        
        new_players = tuple(p for p in self.lobby_players if p.username != username)
        
        return Game(
            id=self.id,
            name=self.name,
            status=self.status,
            host=self.host,
            lobby_players=new_players,
            encounter_deck_id=self.encounter_deck_id,
            deck_ids=self.deck_ids,
            state=self.state,
            created_at=self.created_at
        )
    
    def update_lobby_player(self, updated_player: LobbyPlayer) -> 'Game':
        """Update a player in the lobby"""
        new_players = tuple(
            updated_player if p.username == updated_player.username else p
            for p in self.lobby_players
        )
        
        return Game(
            id=self.id,
            name=self.name,
            status=self.status,
            host=self.host,
            lobby_players=new_players,
            encounter_deck_id=self.encounter_deck_id,
            deck_ids=self.deck_ids,
            state=self.state,
            created_at=self.created_at
        )
    
    def all_players_ready(self) -> bool:
        """Check if all players are ready to start"""
        if not self.lobby_players:
            return False
        
        return all(p.is_ready_to_start() for p in self.lobby_players)
    
    def can_start(self) -> bool:
        """Check if game can be started"""
        return (
            self.status == GameStatus.LOBBY and
            len(self.lobby_players) > 0 and
            self.encounter_deck_id is not None and
            self.all_players_ready()
        )