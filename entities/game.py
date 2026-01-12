from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Position:
    """2D position on the play field"""
    x: int
    y: int


@dataclass(frozen=True)
class CardInPlay:
    """
    A card on the table with position and visual state.
    No rules about what states mean - just visual representation.
    """
    code: str
    position: Position
    
    # Visual states - no enforcement of what these mean
    rotated: bool = False  # 90 degrees (exhausted? doesn't matter to us)
    flipped: bool = False  # Face down
    
    # Generic counters - use however you want
    counters: dict[str, int] = field(default_factory=dict)  # damage, threat, whatever
    
    def with_position(self, position: Position) -> 'CardInPlay':
        """Create new instance with updated position"""
        return CardInPlay(
            code=self.code,
            position=position,
            rotated=self.rotated,
            flipped=self.flipped,
            counters=self.counters
        )
    
    def with_rotated(self, rotated: bool) -> 'CardInPlay':
        """Create new instance with updated rotation"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            rotated=rotated,
            flipped=self.flipped,
            counters=self.counters
        )
    
    def with_flipped(self, flipped: bool) -> 'CardInPlay':
        """Create new instance with updated flip state"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            rotated=self.rotated,
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
            rotated=self.rotated,
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
    deck: list[str]
    hand: list[str]
    discard: list[str]
    removed: list[str] = ()  # Removed from game
    
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
    No rules about what you can/can't do.
    """
    # Each player has their own zones
    players: list[PlayerZones]
    
    # Shared play area - all cards on the table
    play_area: tuple[CardInPlay, ...]
    
    def get_player(self, player_name: str) -> Optional[PlayerZones]:
        """Get player zones by name"""
        for p in self.players:
            if p.player_name == player_name:
                return p
        return None
    
    def update_player(self, updated_player: PlayerZones) -> 'GameState':
        """Return new GameState with updated player zones"""
        new_players = []
        for p in self.players:
            if p.player_name == updated_player.player_name:
                new_players.append(updated_player)
            else:
                new_players.append(p)
        
        return GameState(
            players=tuple(new_players),
            play_area=self.play_area
        )


@dataclass(frozen=True)
class Game:
    """
    A game session.
    Just tracks state - no rules enforcement.
    """
    id: Optional[str]
    name: str
    deck_ids: tuple[str, ...]  # Reference to the decks being used
    state: GameState
    
    # Audit trail
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Game name cannot be empty")
        if not self.deck_ids:
            raise ValueError("Deck IDs cannot be empty")
