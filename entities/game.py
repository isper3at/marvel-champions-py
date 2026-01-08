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
    Represents a card in play with its state.
    Immutable - create new instance for state changes.
    """
    code: str
    position: Position
    exhausted: bool = False
    damage: int = 0
    threat: int = 0
    tokens: dict[str, int] = field(default_factory=dict)
    
    def with_position(self, position: Position) -> 'CardInPlay':
        """Create new instance with updated position"""
        return CardInPlay(
            code=self.code,
            position=position,
            exhausted=self.exhausted,
            damage=self.damage,
            threat=self.threat,
            tokens=self.tokens
        )
    
    def with_exhausted(self, exhausted: bool) -> 'CardInPlay':
        """Create new instance with updated exhausted state"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            exhausted=exhausted,
            damage=self.damage,
            threat=self.threat,
            tokens=self.tokens
        )
    
    def with_damage(self, damage: int) -> 'CardInPlay':
        """Create new instance with updated damage"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            exhausted=self.exhausted,
            damage=damage,
            threat=self.threat,
            tokens=self.tokens
        )


@dataclass(frozen=True)
class GameState:
    """
    Immutable game state snapshot.
    All mutations create new instances.
    """
    # Player deck zones
    player_deck: tuple[str, ...]
    player_hand: tuple[str, ...]
    player_discard: tuple[str, ...]
    player_field: tuple[CardInPlay, ...]
    
    # Encounter deck zones
    encounter_deck: tuple[str, ...]
    encounter_discard: tuple[str, ...]
    villain_field: tuple[CardInPlay, ...]
    
    # Game metadata
    threat_on_main_scheme: int = 0
    
    def draw_player_card(self) -> tuple['GameState', Optional[str]]:
        """Draw a card from player deck. Returns new state and drawn card."""
        if not self.player_deck:
            return self, None
        
        drawn = self.player_deck[0]
        new_deck = self.player_deck[1:]
        new_hand = self.player_hand + (drawn,)
        
        new_state = GameState(
            player_deck=new_deck,
            player_hand=new_hand,
            player_discard=self.player_discard,
            player_field=self.player_field,
            encounter_deck=self.encounter_deck,
            encounter_discard=self.encounter_discard,
            villain_field=self.villain_field,
            threat_on_main_scheme=self.threat_on_main_scheme
        )
        
        return new_state, drawn
    
    def shuffle_player_discard_into_deck(self) -> 'GameState':
        """Shuffle discard pile into deck"""
        import random
        combined = list(self.player_deck) + list(self.player_discard)
        random.shuffle(combined)
        
        return GameState(
            player_deck=tuple(combined),
            player_hand=self.player_hand,
            player_discard=(),
            player_field=self.player_field,
            encounter_deck=self.encounter_deck,
            encounter_discard=self.encounter_discard,
            villain_field=self.villain_field,
            threat_on_main_scheme=self.threat_on_main_scheme
        )


@dataclass(frozen=True)
class Game:
    """
    Immutable domain entity representing a game session.
    """
    id: Optional[str]
    name: str
    deck_id: str
    encounter_id: str
    module_ids: tuple[str, ...]
    state: GameState
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Game name cannot be empty")
        if not self.deck_id:
            raise ValueError("Deck ID cannot be empty")
        if not self.encounter_id:
            raise ValueError("Encounter ID cannot be empty")
