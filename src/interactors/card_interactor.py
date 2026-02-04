"""
Card Interactor - Business logic for card operations.

This module implements the Interactor layer from the EBI (Entities-Boundaries-Interactors)
architecture. It coordinates card operations across multiple boundaries:
- Repository: Persistent storage of card entities
- MarvelCDB Gateway: Fetching authoritative card data from external API
- Image Storage: Managing card image files

The CardInteractor contains all business logic for:
- Importing new cards from MarvelCDB
- Caching and deduplication (avoiding redundant imports)
- Managing card images alongside metadata
- Searching and retrieving cards

All operations work with Card entities (immutable data) and never modify them directly.
Each operation returns new entities or lists, maintaining functional purity.
"""

from typing import Optional, List
from src.boundaries.game_repository import CardRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.boundaries.image_storage import ImageStorage
from src.entities import Card


class CardInteractor:
    """
    Coordinates card operations across repository and gateway boundaries.
    
    CardInteractor is the central coordinator for all card-related operations.
    It determines when to fetch from the external MarvelCDB API, when to use
    the local cache, and when to download/manage images.
    
    The key principle: CardInteractor is "smart" about minimizing external
    API calls and redundant work, while EntityCard is "dumb" and just holds data.
    
    Attributes:
        card_repo: Repository for persisting cards
        marvelcdb: Gateway to MarvelCDB API
        image_storage: Interface for storing/retrieving card images
    
    Example Usage:
        >>> interactor = CardInteractor(repo, gateway, storage)
        >>> card = interactor.import_card_from_marvelcdb('01001a')
        >>> path = interactor.get_card_image_path('01001a')
    """
    
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
        Import a card from MarvelCDB, including downloading its image.
        
        This operation is idempotent - calling it multiple times with the same
        card_code will return the same card without redundant API calls.
        
        Process:
        1. Check if card exists in local repository
        2. If exists: ensure image is present, return existing card
        3. If not: Fetch card info from MarvelCDB API
        4. Create Card entity and save to repository
        5. Download and cache card image
        
        Args:
            card_code: MarvelCDB card code (e.g., "01001a")
            
        Returns:
            Card entity from the repository
            
        Raises:
            Exception: If MarvelCDB API fails or card not found
            
        Example:
            >>> card = interactor.import_card_from_marvelcdb('01001a')
            >>> assert card.code == '01001a'
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
        Import multiple cards efficiently, minimizing API calls.
        
        This operation:
        - Filters out cards already in repository
        - Imports only new cards
        - Returns all requested cards (existing + newly imported)
        
        Handles per-card failures gracefully - if one card import fails,
        continues with others and returns what was successfully imported.
        
        Args:
            card_codes: List of card codes to import
            
        Returns:
            List of Card entities (may be less than input if some failed)
            
        Example:
            >>> codes = ['01001a', '01002b', '01003c']
            >>> cards = interactor.import_cards_bulk(codes)
            >>> assert len(cards) <= len(codes)
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
        """
        Retrieve a card by its code from the repository.
        
        This is a simple lookup that returns the card if it's been previously
        imported, or None if it hasn't been imported yet.
        
        Args:
            card_code: Card identifier to look up
            
        Returns:
            Card entity or None if not found
            
        Example:
            >>> card = interactor.get_card('01001a')
            >>> if card:
            ...     print(f"Found: {card.name}")
        """
        return self.card_repo.find_by_code(card_code)
    
    def get_cards(self, card_codes: List[str]) -> List[Card]:
        """
        Retrieve multiple cards by their codes.
        
        Args:
            card_codes: List of card codes to retrieve
            
        Returns:
            List of Card entities (may be less than input if some not found)
            
        Example:
            >>> cards = interactor.get_cards(['01001a', '01002b'])
            >>> assert len(cards) <= 2
        """
        return self.card_repo.find_by_codes(card_codes)
    
    def search_cards(self, name: str) -> List[Card]:
        """
        Search for cards by name substring.
        
        Performs a case-insensitive search against card names in the repository.
        
        Args:
            name: Name or partial name to search for
            
        Returns:
            List of matching Card entities
            
        Example:
            >>> cards = interactor.search_cards('Spider')
            >>> # Returns all cards with 'Spider' in name
        """
        return self.card_repo.search_by_name(name)
    
    def get_card_image_path(self, card_code: str) -> Optional[str]:
        """
        Get the file path to a card's image, downloading if necessary.
        
        If image is already cached, returns path immediately. If not cached,
        attempts to download it from MarvelCDB. If download fails, returns None.
        
        Args:
            card_code: Card to get image for
            
        Returns:
            File path to image, or None if image unavailable
            
        Example:
            >>> path = interactor.get_card_image_path('01001a')
            >>> if path:
            ...     display_image(path)
        """
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
        """
        Internal helper to download and cache a card's image.
        
        This method:
        - Skips if image already cached
        - Fetches image URL from MarvelCDB
        - Downloads image data
        - Saves to image storage
        
        Failures are logged but don't raise exceptions (graceful degradation).
        
        Args:
            card_code: Card whose image to download
        """
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