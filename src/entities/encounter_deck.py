from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import datetime

from src.entities.card import Card
from src.entities.deck import Deck

@dataclass(frozen=True)
class EncounterDeck(Deck):
    """
    A collection of cards forming a playable encounter deck.
    
    Attributes:
        name: Display name for the deck
        villian_cards: List of villain cards
        main_scheme_cards: List of main scheme cards
        scenario_cards: List of scenario cards
        saved_names: Tuple of saved names/aliases for this deck configuration
                     (used for save/load functionality)
    """
    name: str
    villian_cards: List[Card] = field(default_factory=list)
    main_scheme_cards: List[Card] = field(default_factory=list)
    scenario_cards: List[Card] = field(default_factory=list)
    saved_names: Tuple[str, ...] = field(default_factory=tuple)

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
            updated_at=datetime.datetime.now(datetime.UTC),
            saved_names=self.saved_names
        )
    
    def add_saved_name(self, name: str) -> 'EncounterDeck':
        """Add a new saved name/alias to this encounter deck"""
        if name in self.saved_names:
            return self  # Name already exists
        
        return EncounterDeck(
            id=self.id,
            name=self.name,
            cards=self.cards,
            villian_cards=self.villian_cards,
            main_scheme_cards=self.main_scheme_cards,
            scenario_cards=self.scenario_cards,
            source_url=self.source_url,
            created_at=self.created_at,
            updated_at=datetime.datetime.now(datetime.UTC),
            saved_names=self.saved_names + (name,)
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
            updated_at=datetime.datetime.now(datetime.UTC),
            saved_names=self.saved_names
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
            updated_at=datetime.datetime.now(datetime.UTC),
            saved_names=self.saved_names
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
            updated_at=datetime.datetime.now(datetime.UTC),
            saved_names=self.saved_names
        )