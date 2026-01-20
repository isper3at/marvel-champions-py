"""
Player entity
"""
from dataclasses import dataclass
from typing import Optional

from src.entities.deck_in_play import DeckInPlay
from .deck import Deck

@dataclass(frozen=True)
class Player:
    """
    Represents a player in the game.
    
    Immutable - create new instance for state changes.
    
    Attributes:
        id: Unique identifier for the player
        name: Display name for the player
        deck: Optional deck assigned to the player
    """
    id: str
    name: str
    is_host: bool = False
    is_ready: bool = False
    deck: Optional[Deck] = None
    deck_in_play: Optional['DeckInPlay'] = None
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("ID cannot be empty")
        if not self.name:
            raise ValueError("Name cannot be empty")

    def select_deck(self, deck_id: str) -> 'Player':
        """Select a deck (lobby only)"""
        return Player(
            username=self.username,
            is_host=self.is_host,
            deck_id=deck_id,
            is_ready=self.is_ready,
            deck_in_play=self.deck_in_play
        )
    
    def toggle_ready(self) -> 'Player':
        """Toggle ready state (lobby only)"""
        return Player(
            username=self.username,
            is_host=self.is_host,
            deck_id=self.deck_id,
            is_ready=not self.is_ready,
            deck_in_play=self.deck_in_play
        )
    
    def is_ready_to_start(self) -> bool:
        """Check if ready to start game (lobby only)"""
        return self.deck_id is not None and self.is_ready
    
    def play_deck(self) -> 'Player':
        """Assign a deck in play to the player (game start)"""
        return Player(
            username=self.username,
            is_host=self.is_host,
            deck_id=self.deck_id,
            is_ready=self.is_ready,
            deck_in_play= DeckInPlay.from_deck(self.deck)
        )