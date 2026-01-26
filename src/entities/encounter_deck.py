from dataclasses import dataclass, field
from typing import List, Optional
import datetime

from src.entities.card import Card
from src.entities.deck import Deck

@dataclass(frozen=True)
class EncounterDeck(Deck):
    """
    A collection of cards forming a playable encounter deck.
    """
    name: str
    villian_cards: List[Card] = field(default_factory=list)
    main_scheme_cards: List[Card] = field(default_factory=list)
    scenario_cards: List[Card] = field(default_factory=list)

    def join_encounter_deck(self, other_encounter_deck: 'EncounterDeck') -> 'EncounterDeck':
        return EncounterDeck(
            id=self.id,
            name=self.name,
            cards=self.cards + other_encounter_deck.cards,
            villian_cards=self.villian_cards + other_encounter_deck.villian_cards,
            main_scheme_cards=self.main_scheme_cards + other_encounter_deck.main_scheme_cards,
            scenario_cards=self.scenario_cards + other_encounter_deck.scenario_cards,
            source_url=self.source_url,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC)
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
            scenario_cards=self.scenario_cards,
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
            scenario_cards=self.scenario_cards,
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
        
    