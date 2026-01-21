"""
Updated Game entity with lobby support.
"""

from dataclasses import dataclass
import enum
from typing import Optional
from datetime import datetime

from .play_zone import PlayZone
from .player import Player
from .deck import Deck

class GamePhase(enum.Enum):
    LOBBY = "lobby"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

@dataclass(frozen=True)
class Game:
    """
    Game entity with lobby support.
    
    Lifecycle:
    1. LOBBY - Players join, choose decks, ready up
    2. IN_PROGRESS - Game is being played
    3. FINISHED - Game completed
    """
    id: str
    name: str
    host: str  # Username of host
    status: GamePhase = GamePhase.LOBBY # initial phase is Lobby
    
    players: tuple[Player, ...] = ()
    player_zones: Optional[dict[str, PlayZone]] = None #player username to PlayZone
    encounter_deck: Optional[Deck] = None
    encounter_zone: Optional[PlayZone] = None

    # Audit trail
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Game name cannot be empty")
        if not self.host:
            raise ValueError("Host cannot be empty")
    
    def start_game(self) -> 'Game':
        """Transition game from LOBBY to IN_PROGRESS"""
        if self.status != GamePhase.LOBBY:
            raise ValueError("Can only start game from lobby phase")
        if not self.encounter_deck:
            raise ValueError("Encounter deck must be set to start game")
        if not self.all_players_ready():
            raise ValueError("All players must be ready to start game")
        
        # Initialize player zones
        new_player_zones = {
            player.name: PlayZone(player_name=player.name)
            for player in self.players
        }
        
        # Initialize encounter zone
        new_encounter_zone = PlayZone(player_name='encounter')
        
        return Game(
            id=self.id,
            name=self.name,
            host=self.host,
            status=GamePhase.IN_PROGRESS,
            players=self.players,
            player_zones=new_player_zones,
            encounter_deck=self.encounter_deck,
            encounter_zone=new_encounter_zone,
            created_at=self.created_at
        )
    
    def add_player(self, player: Player) -> 'Game':
        """Add a player to the lobby"""
        if self.status != GamePhase.LOBBY:
            raise ValueError("Can only add players in lobby phase")
        
        # Check if already in lobby
        if player in self.players:
            raise ValueError(f"Player {player.name} already in lobby")
        else:
            new_players = self.players + (player,)
        
        return Game(
            id=self.id,
            name=self.name,
            host=self.host,
            status=GamePhase.IN_PROGRESS,
            players=new_players,
            encounter_deck=self.encounter_deck,
            updated_at=datetime.utcnow()
        )
    
    def remove_player(self, player: Player) -> 'Game':
        """Remove a player from the game"""

        if(self.host == player.name):
            raise ValueError("Host cannot be removed from the game")

        new_players = self.players - (player,)
        
        #If the game was in progress, also remove their play zone
        new_player_zones = self.player_zones.copy().pop(player.name, None) if self.player_zones else None

        return Game(
            id=self.id,
            name=self.name,
            host=self.host,
            status=self.status,
            players=new_players,
            play_zones=new_player_zones,
            created_at=self.created_at
        )

    def update_player(self, updated_player: Player) -> 'Game':
        """Update a player in the lobby"""
        new_players = tuple(
            updated_player if p.username == updated_player.username else p
            for p in self.players
        )
        
        return Game(
            id=self.id,
            name=self.name,
            host=self.host,
            status=self.status,
            players=new_players,
            play_zones=self.play_zones,
            created_at=self.created_at
        )
    
    def all_players_ready(self) -> bool:
        """Check if all players are ready to start"""
        if not self.players:
            return False

        return all(p.is_ready_to_start() for p in self.players)

    def can_start(self) -> bool:
        """Check if game can be started"""
        return (
            self.status == GamePhase.LOBBY and
            len(self.players) > 0 and
            self.encounter_deck is not None and
            self.all_players_ready()
        )