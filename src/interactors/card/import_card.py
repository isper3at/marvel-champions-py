"""Interactor to import a card from MarvelCDB."""
from src.entities import Card
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.boundaries.image_storage import ImageStorage


class ImportCardInteractor:
    """Import a card from MarvelCDB with its image."""
    
    def __init__(
        self,
        marvelcdb_gateway: MarvelCDBGateway,
        image_storage: ImageStorage
    ):
        self.marvelcdb = marvelcdb_gateway
        self.image_storage = image_storage
    
    def execute(self, card_code: str) -> Card:
        """
        Import a card from MarvelCDB with its image.
        
        Idempotent - calling multiple times returns the same card.
        
        Args:
            card_code: MarvelCDB card code (e.g., "01001a")
            
        Returns:
            Card entity from the repository
        """
        # Fetch from MarvelCDB
        card_data = self.marvelcdb.get_card_from_code(card_code)

        # Download image
        self._download_card_image(card_code)
        
        return card_data
    
    def _download_card_image(self, card_code: str):
        """Download and cache a card's image."""
        if self.image_storage.image_exists(card_code):
            return
        
        try:
            image = self.marvelcdb.get_card_image(card_code)
            print(f"Downloaded image for {card_code}, saving to storage...")
            if image:
                self.image_storage.save_image(card_code, image)
        except Exception as e:
            print(f"Failed to download image for {card_code}: {e}")
