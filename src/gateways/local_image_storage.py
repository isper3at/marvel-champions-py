import os
from pathlib import Path
from typing import Optional, List

from PIL.Image import Image
from src.config import ImageStorageConfig
from src.boundaries.image_storage import ImageStorage


class LocalImageStorage(ImageStorage):
    """
    Local filesystem implementation of ImageStorage.
    Stores card images in the configured directory.
    """
    
    def __init__(self, config: ImageStorageConfig):
        self.config = config
        self.storage_path = Path(config.storage_path)
        # Create directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_image(self, card_code: str, image: Image) -> str:
        """
        Save card image and return the file path.
        
        Args:
            card_code: Unique card identifier
            image_data: Binary image data
            
        Returns:
            Path to the saved image
        """
        # Sanitize card code for filename (replace slashes, etc.)
        safe_code = card_code.replace('/', '_').replace('\\', '_')
        filename = f"{safe_code}.png"
        filepath = self.storage_path / filename
        
        print(f"Saving image for {card_code} to {filepath}...")
        image.save(filepath)
        
        return str(filepath)
    
    def get_image_path(self, card_code: str) -> Optional[str]:
        """
        Get the path for a card image if it exists.
        
        Args:
            card_code: Unique card identifier
            
        Returns:
            Path to the image, or None if not found
        """
        safe_code = card_code.replace('/', '_').replace('\\', '_')
        
        # Try .jpg first
        filename = f"{safe_code}.jpg"
        filepath = self.storage_path / filename
        if filepath.exists():
            return str(filepath)
        
        # Try .png as fallback
        filepath_png = self.storage_path / f"{safe_code}.png"
        if filepath_png.exists():
            return str(filepath_png)
        
        return None
    
    def image_exists(self, card_code: str) -> bool:
        """Check if an image exists for a card"""
        return self.get_image_path(card_code) is not None
    
    def delete_image(self, card_code: str) -> bool:
        """Delete a card image"""
        filepath = self.get_image_path(card_code)
        if filepath:
            try:
                os.remove(filepath)
                return True
            except OSError:
                return False
        return False
    
    def get_all_image_codes(self) -> List[str]:
        """Get list of all card codes that have images"""
        codes = []
        for filepath in self.storage_path.glob('*.jpg'):
            # Remove extension and un-sanitize
            code = filepath.stem.replace('_', '/')
            codes.append(code)
        for filepath in self.storage_path.glob('*.png'):
            code = filepath.stem.replace('_', '/')
            if code not in codes:
                codes.append(code)
        return codes

    def get_image(self, card_code: str) -> Optional[Image]:
        img_path = self.get_image_path(card_code)

        if img_path:
            from PIL import Image
            return Image.open(img_path) 
        return None