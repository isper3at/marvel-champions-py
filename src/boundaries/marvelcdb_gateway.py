from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from src.entities import Deck, Card


class MarvelCDBGateway(ABC):
    """
    Gateway interface for MarvelCDB external service.
    Similar to a DAO but for external APIs.
    """
    
    @abstractmethod
    def get_deck_details(self, deck_id: str) -> Deck:
        """
        Retrieve full deck details including card list.
        Returns raw data that will be converted to domain entities.
        """
        pass
    
    @abstractmethod
    def get_card_data(self, card_code: str) -> Card:
        """
        Retrieve card data from MarvelCDB.
        Returns raw data that will be converted to Card entity.
        """
        pass
    
    @abstractmethod
    def download_card_image(self, image_url: str) -> bytes:
        """Download card image binary data"""
        pass
