"""Tests for gateway implementations"""

import pytest
from src.gateways import LocalImageStorage


class TestLocalImageStorage:
    """Test LocalImageStorage"""
    
    def test_save_and_get_image(self, image_storage_config):
        """Test saving and retrieving image"""
        storage = LocalImageStorage(image_storage_config)
        
        image_data = b'fake image data'
        path = storage.save_image('01001a', image_data)
        
        assert path is not None
        assert storage.image_exists('01001a') is True
        
        retrieved_path = storage.get_image_path('01001a')
        assert retrieved_path == path
    
    def test_image_not_exists(self, image_storage_config):
        """Test checking non-existent image"""
        storage = LocalImageStorage(image_storage_config)
        
        assert storage.image_exists('nonexistent') is False
        assert storage.get_image_path('nonexistent') is None
    
    def test_delete_image(self, image_storage_config):
        """Test deleting image"""
        storage = LocalImageStorage(image_storage_config)
        
        storage.save_image('01001a', b'fake data')
        assert storage.image_exists('01001a') is True
        
        deleted = storage.delete_image('01001a')
        assert deleted is True
        assert storage.image_exists('01001a') is False
    
    def test_get_all_image_codes(self, image_storage_config):
        """Test listing all stored images"""
        storage = LocalImageStorage(image_storage_config)
        
        storage.save_image('01001a', b'data1')
        storage.save_image('01002a', b'data2')
        storage.save_image('01003a', b'data3')
        
        codes = storage.get_all_image_codes()
        assert len(codes) == 3
        assert '01001a' in codes
    
    def test_image_size_limit(self, image_storage_config):
        """Test image size limit"""
        storage = LocalImageStorage(image_storage_config)
        
        # Create data larger than limit (5MB)
        large_data = b'x' * (6 * 1024 * 1024)
        
        with pytest.raises(ValueError):
            storage.save_image('large', large_data)
    
    def test_sanitize_card_code(self, image_storage_config):
        """Test that card codes with slashes are sanitized"""
        storage = LocalImageStorage(image_storage_config)
        
        # Card code with slash
        storage.save_image('01001a/b', b'data')
        assert storage.image_exists('01001a/b') is True