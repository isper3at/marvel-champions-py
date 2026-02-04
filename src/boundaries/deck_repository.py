from abc import ABC, abstractmethod
from typing import Optional, List
from src.entities import Deck, DeckList, EncounterDeck

class DeckRepository(ABC):
    """Repository interface for Deck entity"""
    
    @abstractmethod
    def find_list_by_id(self, code: str) -> Optional[DeckList]:
        """
        Find a deck list by its code
        
        Args:
            code: DeckList identifier
            
        Returns:
            DeckList entity or None if not found
        """
        pass
        
    @abstractmethod
    def find_by_id(self, deck_id: str) -> Optional[Deck]:
        """
        Find a deck by its ID
        
        Args:
            deck_id: Deck identifier
            
        Returns:
            Deck entity or None if not found
        """
        pass
    
    @abstractmethod
    def save(self, deck: Deck) -> Deck:
        """Save a deck and return the saved entity"""
        pass

    @abstractmethod
    def save_deck_list(self, deck_list: DeckList) -> DeckList:
        """Save a deck list and return the saved entity"""
        pass

    @abstractmethod
    def save_encounter_module(self, encounter_module: EncounterDeck) -> EncounterDeck:
        """Save an encounter module and return the saved entity"""
        pass
    
    @abstractmethod
    def delete(self, deck_id: str) -> bool:
        """Delete a deck by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Deck]:
        """Find all decks"""
        pass

    @abstractmethod
    def find_encounter_module_by_id(self, module_name: str) -> Optional[EncounterDeck]:
        """Find an encounter deck by its ID"""
        pass