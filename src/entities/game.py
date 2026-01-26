"""
Updated Game entity with lobby support.
"""

from dataclasses import dataclass, field
import enum
from typing import List, Optional
import datetime
import uuid

from src.entities.encounter_deck import EncounterDeck
from src.entities.encounter_deck_in_play import EncounterDeckInPlay

from .play_zone import PlayZone
from .player import Player


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
    name: str
    host: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    phase: GamePhase = GamePhase.LOBBY
    players: List[Player] = ()
    encounter_deck: Optional[EncounterDeck] = None
    play_zone: Optional[PlayZone] = None
    created_at: Optional[datetime.datetime] = field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Game name cannot be empty")
        if not self.host:
            raise ValueError("Host cannot be empty")
    
    def start_game(self) -> 'Game':
        """Transition game from LOBBY to IN_PROGRESS"""
        if self.phase != GamePhase.LOBBY:
            raise ValueError("Can only start game from lobby phase")
        if not self.players:
            raise ValueError("Must have at least one player to start game")
        if not all(p.is_ready for p in self.players):
            raise ValueError("All players must be ready to start game")
        
        return Game(
            name=self.name,
            host=self.host,
            id=self.id,
            phase=GamePhase.IN_PROGRESS,
            players=self.players,
            encounter_deck=self.encounter_deck,
            play_zone=PlayZone(encounter_deck=EncounterDeckInPlay.from_deck(self.encounter_deck)) if self.encounter_deck else None,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
        )
    
    def add_player(self, player: Player) -> 'Game':
        """Add a player to the lobby"""
        if self.phase != GamePhase.LOBBY:
            raise ValueError("Can only add players in lobby phase")
        
        if player in self.players:
            raise ValueError(f"Player {player.name} already in lobby")
        
        new_players = self.players + (player,)
        
        return Game(
            name=self.name,
            host=self.host,
            id=self.id,
            phase=self.phase,
            players=new_players,
            encounter_deck=self.encounter_deck,
            play_zone=self.play_zone,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
        )
    
    def remove_player(self, player: Player) -> 'Game':
        """Remove a player from the game"""
        if self.host == player.name:
            raise ValueError("Host cannot be removed from the game")
        
        new_players = tuple(p for p in self.players if p.name != player.name)
        
        return Game(
            name=self.name,
            host=self.host,
            id=self.id,
            phase=self.phase,
            players=new_players,
            encounter_deck=self.encounter_deck,
            play_zone=self.play_zone,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
        )
    
    def update_player(self, updated_player: Player) -> 'Game':
        """Update a player in the lobby"""
        new_players = tuple(
            updated_player if p.name == updated_player.name else p
            for p in self.players
        )
        
        return Game(
            name=self.name,
            host=self.host,
            id=self.id,
            phase=self.phase,
            players=new_players,
            encounter_deck=self.encounter_deck,
            play_zone=self.play_zone,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
        )
        
    def set_encounter_deck(self, encounter_deck: EncounterDeck) -> 'Game':
        """Set the encounter deck for the game"""
        return Game(
            name=self.name,
            host=self.host,
            id=self.id,
            phase=self.phase,
            players=self.players,
            encounter_deck=encounter_deck,
            play_zone=self.play_zone,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
        )
    
    def all_players_ready(self) -> bool:
        """Check if all players are ready to start"""
        if not self.players:
            return False
        return all(p.is_ready for p in self.players)
    
    def can_start(self) -> bool:
        """Check if game can be started"""
        return (
            self.phase == GamePhase.LOBBY and
            len(self.players) > 0 and
            self.all_players_ready() and
            self.encounter_deck is not None
        )