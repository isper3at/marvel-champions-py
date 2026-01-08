from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class MarvelCDBGateway(ABC):
    """
    Gateway interface for MarvelCDB external service.
    Similar to a DAO but for external APIs.
    """
    
    @abstractmethod
    def set_session_cookie(self, cookie: str) -> None:
        """Set the session cookie for authenticated requests"""
        pass
    
    @abstractmethod
    def get_user_decks(self) -> List[Dict[str, Any]]:
        """
        Retrieve user's deck list from MarvelCDB.
        Returns raw data that will be converted to domain entities.
        """
        pass
    
    @abstractmethod
    def get_deck_details(self, deck_id: str) -> Dict[str, Any]:
        """
        Retrieve full deck details including card list.
        Returns raw data that will be converted to domain entities.
        """
        pass
    
    @abstractmethod
    def get_card_data(self, card_code: str) -> Dict[str, Any]:
        """
        Retrieve card data from MarvelCDB.
        Returns raw data that will be converted to Card entity.
        """
        pass
    
    @abstractmethod
    def get_card_image_url(self, card_code: str) -> Optional[str]:
        """Get the image URL for a card"""
        pass
    
    @abstractmethod
    def download_card_image(self, image_url: str) -> bytes:
        """Download card image binary data"""
        pass
    
    @abstractmethod
    def search_cards(self, query: str) -> List[Dict[str, Any]]:
        """Search for cards by name"""
        pass
