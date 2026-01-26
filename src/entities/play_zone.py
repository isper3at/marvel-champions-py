"""
PlayZone entity - Shared play area for all players
"""
from dataclasses import dataclass
from typing import Tuple, Dict, Optional
from .deck_in_play import DeckInPlay
from .card_in_play import CardInPlay
from .dial import Dial
from .encounter_deck_in_play import EncounterDeckInPlay

@dataclass(frozen=True)
class PlayZone:
    """
    Shared play zone where all players interact.
    Contains all decks, cards, and game state elements.
    
    This is a single shared space - not per-player zones.
    """
    encounter_deck: Optional[EncounterDeckInPlay] = None  # The encounter deck
    decks_in_play: Tuple[DeckInPlay, ...] = ()  # All player decks + encounter deck
    cards_in_play: Tuple[CardInPlay, ...] = ()  # All cards on the table
    dials: Tuple[Dial, ...] = ()  # Threat dials, HP dials, etc.

    def set_encounter_deck(self, encounter_deck: EncounterDeckInPlay) -> 'PlayZone':
        """Set the encounter deck for the play zone"""
        return PlayZone(
            encounter_deck=encounter_deck,
            decks_in_play=self.decks_in_play,
            cards_in_play=self.cards_in_play,
            dials=self.dials
        )

    def add_deck(self, deck_in_play: DeckInPlay) -> 'PlayZone':
        """Add a deck to the play zone"""
        return PlayZone(
            encounter_deck=self.encounter_deck,
            decks_in_play=self.decks_in_play + (deck_in_play,),
            cards_in_play=self.cards_in_play,
            dials=self.dials
        )
    
    def add_card(self, card: CardInPlay) -> 'PlayZone':
        """Add a card to the play zone"""
        return PlayZone(
            encounter_deck=self.encounter_deck,
            decks_in_play=self.decks_in_play,
            cards_in_play=self.cards_in_play + (card,),
            dials=self.dials
        )
    
    def remove_card(self, card_code: str) -> 'PlayZone':
        """Remove a card from play zone"""
        new_cards = tuple(c for c in self.cards_in_play if c.code != card_code)
        return PlayZone(
            encounter_deck=self.encounter_deck,
            decks_in_play=self.decks_in_play,
            cards_in_play=new_cards,
            dials=self.dials
        )
    
    def update_card(self, updated_card: CardInPlay) -> 'PlayZone':
        """Update a card in the play zone"""
        new_cards = tuple(
            updated_card if c.code == updated_card.code else c
            for c in self.cards_in_play
        )
        return PlayZone(
            encounter_deck=self.encounter_deck,
            decks_in_play=self.decks_in_play,
            cards_in_play=new_cards,
            dials=self.dials
        )
    
    def get_card(self, card_code: str) -> Optional[CardInPlay]:
        """Get a card by code"""
        for card in self.cards_in_play:
            if card.code == card_code:
                return card
        return None
    
    def get_deck_by_player(self, player_name: str) -> Optional[DeckInPlay]:
        """Get a player's deck by their name"""
        for deck in self.decks_in_play:
            if deck.deck.name == player_name or player_name in deck.deck.name:
                return deck
        return None
    
    def update_deck(self, updated_deck: DeckInPlay) -> 'PlayZone':
        """Update a deck in play"""
        new_decks = tuple(
            updated_deck if d.deck.id == updated_deck.deck.id else d
            for d in self.decks_in_play
        )
        return PlayZone(
            encounter_deck=self.encounter_deck,
            decks_in_play=new_decks,
            cards_in_play=self.cards_in_play,
            dials=self.dials
        )
    
    def add_dial(self, dial: Dial) -> 'PlayZone':
        """Add a dial to the play zone"""
        return PlayZone(
            encounter_deck=self.encounter_deck,
            decks_in_play=self.decks_in_play,
            cards_in_play=self.cards_in_play,
            dials=self.dials + (dial,)
        )