from PIL import Image
from abc import ABC, abstractmethod
from typing import Optional, List


class ImageStorage(ABC):
    """
    Interface for image storage operations.
    Abstracts the storage mechanism (filesystem, S3, etc.)
    """
    
    @abstractmethod
    def save_image(self, card_code: str, card_image: Image.Image) -> str:
        """
        Save card image and return the file path/URL.
        
        Args:
            card_code: Unique card identifier
            card_image: The card image
            
        Returns:
            Path or URL to the saved image
        """
        pass
    
    @abstractmethod
    def get_image(self, card_code: str) -> Optional[Image.Image]:
        """
        Get the path/URL for a card image if it exists.
        
        Args:
            card_code: Unique card identifier
            
        Returns:
            The found Image, or None if not found
        """
        pass
    
    @abstractmethod
    def image_exists(self, card_code: str) -> bool:
        """Check if an image exists for a card"""
        pass
    
    @abstractmethod
    def delete_image(self, card_code: str) -> bool:
        """Delete a card image"""
        pass
    
    @abstractmethod
    def get_all_image_codes(self) -> List[str]:
        """Get list of all card codes that have images"""
        pass
