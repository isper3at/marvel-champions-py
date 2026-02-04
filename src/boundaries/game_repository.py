from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
from src.entities import Game

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
