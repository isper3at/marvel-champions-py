"""Interactor to get a card image."""
from typing import Optional
from PIL import Image
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.boundaries.image_storage import ImageStorage


class GetCardImageInteractor:
    """Get a card's image, downloading if necessary."""
    
    def __init__(
        self,
        marvelcdb_gateway: MarvelCDBGateway,
        image_storage: ImageStorage
    ):
        self.marvelcdb = marvelcdb_gateway
        self.image_storage = image_storage
    
    def execute(self, card_code: str) -> Optional[Image.Image]:
        """
        Get card image, downloading if not cached.
        
        Args:
            card_code: Card identifier
            
        Returns:
            Image object or None if not found
        """
        if self.image_storage.image_exists(card_code):
            return self.image_storage.get_image(card_code)
        
        try:
            image = self.marvelcdb.get_card_image(card_code)
            if image:
                self.image_storage.save_image(card_code, image)
            return image
        except Exception:
            return None
