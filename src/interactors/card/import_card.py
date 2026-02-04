"""Interactor to import a card from MarvelCDB."""
from src.entities import Card
from src.boundaries.card_repository import CardRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.boundaries.image_storage import ImageStorage


class ImportCardInteractor:
    """Import a card from MarvelCDB with its image."""
    
    def __init__(
        self,
        card_repo: CardRepository,
        marvelcdb_gateway: MarvelCDBGateway,
        image_storage: ImageStorage
    ):
        self.card_repo = card_repo
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
        # Check if already exists
        existing = self.card_repo.find_by_code(card_code)
        if existing:
            if not self.image_storage.image_exists(card_code):
                self._download_card_image(card_code)
            return existing
        
        # Fetch from MarvelCDB
        card_data = self.marvelcdb.get_card_from_code(card_code)
        
        # Save to repository
        saved_card = self.card_repo.save(card_data)
        
        # Download image
        self._download_card_image(card_code)
        
        return saved_card
    
    def _download_card_image(self, card_code: str):
        """Download and cache a card's image."""
        if self.image_storage.image_exists(card_code):
            return
        
        try:
            image = self.marvelcdb.get_card_image(card_code)
            if image:
                self.image_storage.save_image(card_code, image)
        except Exception as e:
            print(f"Failed to download image for {card_code}: {e}")
