from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class CardType(Enum):
    HERO = "hero"
    ALTER_EGO = "alter_ego"
    ALLY = "ally"
    EVENT = "event"
    SUPPORT = "support"
    UPGRADE = "upgrade"
    RESOURCE = "resource"
    VILLAIN = "villain"
    MINION = "minion"
    SIDE_SCHEME = "side_scheme"
    ATTACHMENT = "attachment"
    TREACHERY = "treachery"
    OBLIGATION = "obligation"
    ENVIRONMENT = "environment"


@dataclass(frozen=True)
class Card:
    """
    Immutable domain entity representing a Marvel Champions card.
    This is the core domain object with no external dependencies.
    """
    code: str
    name: str
    type: CardType
    text: Optional[str] = None
    cost: Optional[int] = None
    
    # Hero/Ally stats
    thwart: Optional[int] = None
    attack: Optional[int] = None
    defense: Optional[int] = None
    health: Optional[int] = None
    hand_size: Optional[int] = None
    
    # Villain/Minion stats
    scheme: Optional[int] = None
    threat: Optional[int] = None
    
    # Resource
    resource_physical: int = 0
    resource_mental: int = 0
    resource_energy: int = 0
    resource_wild: int = 0
    
    # Metadata
    pack_code: Optional[str] = None
    faction_code: Optional[str] = None
    traits: tuple[str, ...] = ()
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validation logic"""
        if not self.code:
            raise ValueError("Card code cannot be empty")
        if not self.name:
            raise ValueError("Card name cannot be empty")
    
    def is_hero(self) -> bool:
        return self.type == CardType.HERO
    
    def is_ally(self) -> bool:
        return self.type == CardType.ALLY
    
    def is_event(self) -> bool:
        return self.type == CardType.EVENT
    
    def is_upgrade(self) -> bool:
        return self.type == CardType.UPGRADE
    
    def is_support(self) -> bool:
        return self.type == CardType.SUPPORT
    
    def has_resource(self) -> bool:
        return (self.resource_physical + self.resource_mental + 
                self.resource_energy + self.resource_wild) > 0
    
    def total_resources(self) -> int:
        return (self.resource_physical + self.resource_mental + 
                self.resource_energy + self.resource_wild)
