"""
Card Interactor - Business logic for card operations.

Responsibilities:
- Import cards from MarvelCDB
- Manage card data in repository
- Download and store card images
- Search and retrieve cards
"""

from typing import Optional, List
from src.boundaries.repository import CardRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.boundaries.image_storage import ImageStorage
from src.entities import Card


class CardInteractor:
    """Business logic for card operations"""
    
    def __init__(
        self,
        card_repository: CardRepository,
        marvelcdb_gateway: MarvelCDBGateway,
        image_storage: ImageStorage
    ):
        self.card_repo = card_repository
        self.marvelcdb = marvelcdb_gateway
        self.image_storage = image_storage
    
    def import_card_from_marvelcdb(self, card_code: str) -> Card:
        """
        Import a card from MarvelCDB, including image.
        
        Steps:
        1. Check if card already exists
        2. Fetch card info from MarvelCDB
        3. Create Card entity
        4. Save to repository
        5. Download and save image
        
        Returns:
            Imported Card entity
        """
        # Check if already exists
        existing = self.card_repo.find_by_code(card_code)
        if existing:
            # Already have it, just ensure image exists
            if not self.image_storage.image_exists(card_code):
                self._download_card_image(card_code)
            return existing
        
        # Fetch from MarvelCDB
        card_data = self.marvelcdb.get_card_info(card_code)
        
        # Create entity
        card = Card(
            code=card_data['code'],
            name=card_data['name'],
            text=card_data.get('text')
        )
        
        # Save to repository
        saved_card = self.card_repo.save(card)
        
        # Download image
        self._download_card_image(card_code)
        
        return saved_card
    
    def import_cards_bulk(self, card_codes: List[str]) -> List[Card]:
        """
        Import multiple cards efficiently.
        
        Args:
            card_codes: List of card codes to import
            
        Returns:
            List of imported Card entities
        """
        # Filter out cards we already have
        existing_codes = set()
        for code in card_codes:
            if self.card_repo.exists(code):
                existing_codes.add(code)
        
        codes_to_import = [c for c in card_codes if c not in existing_codes]
        
        if not codes_to_import:
            # All cards already exist
            return self.card_repo.find_by_codes(card_codes)
        
        # Import new cards
        new_cards = []
        for code in codes_to_import:
            try:
                card = self.import_card_from_marvelcdb(code)
                new_cards.append(card)
            except Exception as e:
                print(f"Failed to import card {code}: {e}")
        
        # Return all cards (existing + new)
        return self.card_repo.find_by_codes(card_codes)
    
    def get_card(self, card_code: str) -> Optional[Card]:
        """Get a card by code"""
        return self.card_repo.find_by_code(card_code)
    
    def get_cards(self, card_codes: List[str]) -> List[Card]:
        """Get multiple cards by codes"""
        return self.card_repo.find_by_codes(card_codes)
    
    def search_cards(self, name: str) -> List[Card]:
        """Search cards by name"""
        return self.card_repo.search_by_name(name)
    
    def get_card_image_path(self, card_code: str) -> Optional[str]:
        """Get path to card image, downloading if needed"""
        path = self.image_storage.get_image_path(card_code)
        if path:
            return path
        
        # Try to download it
        try:
            self._download_card_image(card_code)
            return self.image_storage.get_image_path(card_code)
        except Exception:
            return None
    
    def _download_card_image(self, card_code: str):
        """Internal method to download and save card image"""
        if self.image_storage.image_exists(card_code):
            return  # Already have it
        
        try:
            image_url = self.marvelcdb.get_card_image_url(card_code)
            if not image_url:
                print(f"No image URL found for card {card_code}")
                return
            
            image_data = self.marvelcdb.download_card_image(image_url)
            self.image_storage.save_image(card_code, image_data)
        except Exception as e:
            print(f"Failed to download image for {card_code}: {e}")