from dataclasses import dataclass, field
import random
from typing import List, Optional, Tuple
import datetime

from src.entities.card import Card
from src.entities.deck import Deck
from src.entities.encounter_deck import EncounterDeck
from src.entities.position import Position

@dataclass(frozen=True)
class EncounterDeckInPlay:
    """
    A collection of cards forming a playable encounter deck.
    """
    encounterDeck: EncounterDeck
    draw_position: Position  # Position of the draw pile on the play field
    discard_position: Position  # Position of the discard pile on the play field
    draw_pile: Tuple[str, ...]  # Tuple of card codes in draw pile
    discard_pile: Tuple[str, ...]  # Tuple of card codes in discard pile

    @classmethod
    def from_deck(cls, encounterDeck: EncounterDeck, shuffle: bool = True) -> 'EncounterDeckInPlay':
        draw_pile = tuple(encounterDeck.get_card_codes())
        if shuffle:
            draw_pile = random.shuffle(list(draw_pile))
            
        return cls(
            encounterDeck=encounterDeck,
            draw_position=Position(x=0, y=0),#TODO find a default
            discard_position=Position(x=1, y=0),#TODO find a default
            draw_pile=draw_pile,
            discard_pile=()
        )

    def add_villian_card(self, card: Card) -> 'EncounterDeck':
        """Add a villain card to the encounter deck"""
        new_villian_cards = self.villian_cards + [card]
        return EncounterDeck(
            id=self.id,
            name=self.name,
            cards=self.cards,
            villian_cards=new_villian_cards,
            main_scheme_cards=self.main_scheme_cards,
            other_scheme_cards=self.other_scheme_cards,
            source_url=self.source_url,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
        )
        
    def add_main_scheme_card(self, card: Card) -> 'EncounterDeck':
        """Add a main scheme card to the encounter deck"""
        new_main_scheme_cards = self.main_scheme_cards + [card]
        return EncounterDeck(
            id=self.id,
            name=self.name,
            cards=self.cards,
            villian_cards=self.villian_cards,
            main_scheme_cards=new_main_scheme_cards,
            other_scheme_cards=self.other_scheme_cards,
            source_url=self.source_url,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
        )
        
    def add_scenario_card(self, card: Card) -> 'EncounterDeck':
        """Add a scenario card to the encounter deck"""
        new_scenario_cards = self.scenario_cards + [card]
        return EncounterDeck(
            id=self.id,
            name=self.name,
            cards=self.cards,
            villian_cards=self.villian_cards,
            main_scheme_cards=self.main_scheme_cards,
            scenario_cards=new_scenario_cards,
            source_url=self.source_url,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
        )
        
    