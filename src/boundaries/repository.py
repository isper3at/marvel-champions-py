from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
from src.entities import Card, Deck, Game, DeckList, EncounterDeck


class CardRepository(ABC):
    """Repository interface for Card entity"""
    
    @abstractmethod
    def find_by_code(self, code: str) -> Optional[Card]:
        """Find a card by its unique code"""
        pass
    
    @abstractmethod
    def find_by_codes(self, codes: List[str]) -> List[Card]:
        """Find multiple cards by their codes"""
        pass
    
    @abstractmethod
    def save(self, card: Card) -> Card:
        """Save a card and return the saved entity"""
        pass
    
    @abstractmethod
    def save_all(self, cards: List[Card]) -> List[Card]:
        """Save multiple cards"""
        pass
    
    @abstractmethod
    def exists(self, code: str) -> bool:
        """Check if a card exists"""
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Card]:
        """Find all cards with pagination"""
        pass
    
    @abstractmethod
    def search_by_name(self, name: str) -> List[Card]:
        """Search cards by name (partial match)"""
        pass


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

class GameRepository(ABC):
    """Repository interface for Game entity"""
    
    @abstractmethod
    def find_by_id(self, game_id: uuid.UUID) -> Optional[Game]:
        """Find a game by its ID"""
        pass
    
    @abstractmethod
    def save(self, game: Game) -> Game:
        """Save a game and return the saved entity"""
        pass
    
    @abstractmethod
    def delete(self, game_id: str) -> bool:
        """Delete a game by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Game]:
        """Find all games"""
        pass
    
    @abstractmethod
    def find_recent(self, limit: int = 10) -> List[Game]:
        """Find recent games"""
        pass
