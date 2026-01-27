from typing import Optional
from PIL import Image
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.boundaries.image_storage import ImageStorage

class GetCardImageInteractor:
    marvelcdb_client: MarvelCDBGateway
    image_store: ImageStorage

    def __init__(self, marvelcdb_client: MarvelCDBGateway, image_store: ImageStorage):
        self.marvelcdb_client = marvelcdb_client
        self.image_store = image_store

    def execute(self, card_id: str) -> Optional[Image.Image]:
        """
        Retrieve the image of a card by its ID
        
        Args:
            card_id: Card identifier
            
        Returns:
            Image of the card or None if not found
        """
        card_image: Optional[Image.Image] = None
        if self.image_store.image_exists(card_id):
            card_image = self.image_store.get_image(card_id)
        else:
            card_image = self.marvelcdb_client.get_card_image(card_id)
            if card_image is not None:
                self.image_store.save_image(card_id, card_image)
        return card_image