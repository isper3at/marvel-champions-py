from abc import ABC, abstractmethod
from typing import Optional, List
from entities import Card, Deck, Encounter, Module, Game


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
    def find_by_id(self, deck_id: str) -> Optional[Deck]:
        """Find a deck by its ID"""
        pass
    
    @abstractmethod
    def save(self, deck: Deck) -> Deck:
        """Save a deck and return the saved entity"""
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
    def find_by_hero(self, hero_code: str) -> List[Deck]:
        """Find all decks for a specific hero"""
        pass
    
    @abstractmethod
    def find_by_marvelcdb_id(self, marvelcdb_id: str) -> Optional[Deck]:
        """Find a deck by its MarvelCDB ID"""
        pass


class EncounterRepository(ABC):
    """Repository interface for Encounter entity"""
    
    @abstractmethod
    def find_by_id(self, encounter_id: str) -> Optional[Encounter]:
        """Find an encounter by its ID"""
        pass
    
    @abstractmethod
    def save(self, encounter: Encounter) -> Encounter:
        """Save an encounter and return the saved entity"""
        pass
    
    @abstractmethod
    def delete(self, encounter_id: str) -> bool:
        """Delete an encounter by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Encounter]:
        """Find all encounters"""
        pass
    
    @abstractmethod
    def find_by_villain(self, villain_code: str) -> List[Encounter]:
        """Find all encounters for a specific villain"""
        pass


class ModuleRepository(ABC):
    """Repository interface for Module entity"""
    
    @abstractmethod
    def find_by_id(self, module_id: str) -> Optional[Module]:
        """Find a module by its ID"""
        pass
    
    @abstractmethod
    def save(self, module: Module) -> Module:
        """Save a module and return the saved entity"""
        pass
    
    @abstractmethod
    def delete(self, module_id: str) -> bool:
        """Delete a module by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Module]:
        """Find all modules"""
        pass
    
    @abstractmethod
    def find_by_set(self, set_code: str) -> List[Module]:
        """Find all modules for a specific set"""
        pass


class GameRepository(ABC):
    """Repository interface for Game entity"""
    
    @abstractmethod
    def find_by_id(self, game_id: str) -> Optional[Game]:
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
