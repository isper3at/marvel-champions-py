from PIL import Image
from abc import ABC, abstractmethod
from src.entities import Card, DeckList
from src.entities.encounter_deck import EncounterDeck


class MarvelCDBGateway(ABC):
    """
    Gateway interface for MarvelCDB external service.
    Similar to a DAO but for external APIs.
    """
    @abstractmethod
    def get_module(self, module_code: str) -> EncounterDeck:
        """
        Retrieve module data from MarvelCDB.
        Returns raw data that will be converted to domain entities.
        """
        pass

    @abstractmethod
    def get_deck(self, deck_list_id: str) -> DeckList:
        """
        Retrieve deck list data from MarvelCDB.
        Returns raw data that will be converted to DeckList entity.
        """
        pass
    
    @abstractmethod
    def get_card_from_code(self, card_code: str) -> Card:
        """
        Retrieve card data from MarvelCDB.
        Returns raw data that will be converted to Card entity.
        """
        pass
    
    @abstractmethod
    def get_card_image(self, image_url: str) -> Image.Image:
        """Download card image"""
        pass
