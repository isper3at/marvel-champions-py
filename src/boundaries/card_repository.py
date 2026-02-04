from abc import ABC, abstractmethod
from typing import Optional, List
from src.entities import Card

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