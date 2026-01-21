
from dataclasses import dataclass
from dataclasses import dataclass
from src.entities.play_zone import PlayZone
from typing import Dict, List
from src.entities.deck_in_play import DeckInPlay

@dataclass(frozen=True)
class GameState :
    zones: Dict[str, PlayZone] #map of player to zone, or 'encounter' for encounter zone
    decks_in_play: List[DeckInPlay]  # Tuple of DeckInPlay IDs currently active in the game