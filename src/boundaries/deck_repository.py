from abc import ABC, abstractmethod
from typing import Optional, List
from src.entities import Deck, DeckList, EncounterDeck

class DeckRepository(ABC):
    """Repository interface for Deck entity"""
        
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
    def save(self, deck_list: DeckList) -> DeckList:
        """Save a deck list and return the saved entity"""
        pass

    @abstractmethod
    def delete(self, deck_id: str) -> bool:
        """Delete a deck by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[DeckList]:
        """Find all decks"""
        pass

    def find_all_modules(self) -> List[DeckList]:
        """Find all encounter modules"""
        pass

    def find_all_player_decks(self) -> List[DeckList]:
        """Find all player decks"""
        pass