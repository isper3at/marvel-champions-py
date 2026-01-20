"""
Updated Game entity with lobby support.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from src.entities import GameStatus, LobbyPlayer, GameState

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