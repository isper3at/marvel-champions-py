"""
Lobby entities for game setup phase.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class GameStatus(Enum):
    """Game lifecycle status"""
    LOBBY = "lobby"              # Players joining and choosing decks
    IN_PROGRESS = "in_progress"  # Game being played
    FINISHED = "finished"        # Game completed


@dataclass(frozen=True)
class LobbyPlayer:
    """
    Player in a lobby.
    Immutable - create new instance for changes.
    """
    username: str
    deck_id: Optional[str] = None
    is_ready: bool = False
    is_host: bool = False
    
    def __post_init__(self):
        if not self.username:
            raise ValueError("Username cannot be empty")
    
    def with_deck(self, deck_id: str) -> 'LobbyPlayer':
        """Create new instance with deck selected"""
        return LobbyPlayer(
            username=self.username,
            deck_id=deck_id,
            is_ready=self.is_ready,
            is_host=self.is_host
        )
    
    def toggle_ready(self) -> 'LobbyPlayer':
        """Create new instance with ready toggled"""
        return LobbyPlayer(
            username=self.username,
            deck_id=self.deck_id,
            is_ready=not self.is_ready,
            is_host=self.is_host
        )
    
    def is_ready_to_start(self) -> bool:
        """Check if player is ready to start game"""
        return self.deck_id is not None and self.is_ready