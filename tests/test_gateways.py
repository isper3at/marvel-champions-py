"""Tests for gateway implementations"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from src.gateways import LocalImageStorage, MarvelCDBClient
from src.config import ImageStorageConfig, MarvelCDBConfig


class TestLocalImageStorage:
    """Test LocalImageStorage"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def storage_config(self, temp_dir):
        """Create storage config"""
        return ImageStorageConfig(
            storage_path=temp_dir,
            max_image_size=5 * 1024 * 1024
        )
    
    def test_save_and_get_image(self, storage_config):
        """Test saving and retrieving image"""
        storage = LocalImageStorage(storage_config)
        
        image_data = b'fake image data'
        path = storage.save_image('01001a', image_data)
        
        assert path is not None
        assert storage.image_exists('01001a') is True
        
        retrieved_path = storage.get_image_path('01001a')
        assert retrieved_path == path
        
        # Verify file was actually created
        assert Path(path).exists()
        with open(path, 'rb') as f:
            assert f.read() == image_data
    
    def test_image_not_exists(self, storage_config):
        """Test checking non-existent image"""
        storage = LocalImageStorage(storage_config)
        
        assert storage.image_exists('nonexistent') is False
        assert storage.get_image_path('nonexistent') is None
    
    def test_delete_image(self, storage_config):
        """Test deleting image"""
        storage = LocalImageStorage(storage_config)
        
        storage.save_image('01001a', b'fake data')
        assert storage.image_exists('01001a') is True
        
        deleted = storage.delete_image('01001a')
        assert deleted is True
        assert storage.image_exists('01001a') is False
    
    def test_delete_nonexistent_image(self, storage_config):
        """Test deleting image that doesn't exist"""
        storage = LocalImageStorage(storage_config)
        
        deleted = storage.delete_image('nonexistent')
        assert deleted is False
    
    def test_get_all_image_codes(self, storage_config):
        """Test listing all stored images"""
        storage = LocalImageStorage(storage_config)
        
        storage.save_image('01001a', b'data1')
        storage.save_image('01002a', b'data2')
        storage.save_image('01003a', b'data3')
        
        codes = storage.get_all_image_codes()
        assert len(codes) == 3
        assert '01001a' in codes
        assert '01002a' in codes
        assert '01003a' in codes
    
    def test_image_size_limit(self, storage_config):
        """Test image size limit"""
        storage = LocalImageStorage(storage_config)
        
        # Create data larger than limit (5MB)
        large_data = b'x' * (6 * 1024 * 1024)
        
        with pytest.raises(ValueError, match="exceeds maximum"):
            storage.save_image('large', large_data)
    
    def test_sanitize_card_code_with_slash(self, storage_config):
        """Test that card codes with slashes are sanitized"""
        storage = LocalImageStorage(storage_config)
        
        # Card code with slash (some MarvelCDB cards have this)
        storage.save_image('01001a/b', b'data')
        assert storage.image_exists('01001a/b') is True
        
        # Check that file doesn't actually have slash
        path = storage.get_image_path('01001a/b')
        assert '/' not in Path(path).name
    
    def test_save_overwrites_existing(self, storage_config):
        """Test that saving overwrites existing image"""
        storage = LocalImageStorage(storage_config)
        
        storage.save_image('01001a', b'old data')
        path1 = storage.get_image_path('01001a')
        
        storage.save_image('01001a', b'new data')
        path2 = storage.get_image_path('01001a')
        
        # Should be same path
        assert path1 == path2
        
        # Should have new data
        with open(path2, 'rb') as f:
            assert f.read() == b'new data'
    
    def test_supports_png_and_jpg(self, storage_config):
        """Test that storage supports both PNG and JPG"""
        storage = LocalImageStorage(storage_config)
        
        # Save as jpg (default)
        path_jpg = storage.save_image('card1', b'jpg data')
        assert path_jpg.endswith('.jpg')
        
        # Manually create a PNG file
        png_path = Path(storage_config.storage_path) / 'card2.png'
        png_path.write_bytes(b'png data')
        
        # Should find PNG
        assert storage.image_exists('card2') is True
        found_path = storage.get_image_path('card2')
        assert found_path.endswith('.png')


class TestMarvelCDBClient:
    """Test MarvelCDBClient gateway"""
    
    @pytest.fixture
    def config(self):
        """Create MarvelCDB config"""
        return MarvelCDBConfig(
            base_url='https://marvelcdb.com',
            rate_limit_calls=10,
            rate_limit_period=60,
            request_delay=0.1
        )
    
    @pytest.fixture
    def client(self, config):
        """Create client"""
        return MarvelCDBClient(config)
    
    def test_set_session_cookie(self, client):
        """Test setting session cookie"""
        client.set_session_cookie('test_cookie_value')
        
        # Check that cookie was set (try common names)
        cookie_found = False
        for cookie_name in ['laravel_session', 'session', 'PHPSESSID', 'marvelcdb_session']:
            if cookie_name in client.session.cookies:
                cookie_found = True
                break
        
        assert cookie_found
    
    def test_rate_limiting(self, client):
        """Test that rate limiting delays requests"""
        import time
        
        # Mock the actual request
        with patch.object(client.session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'<html></html>'
            
            start = time.time()
            
            # Make two requests
            client._rate_limit()
            client._rate_limit()
            
            elapsed = time.time() - start
            
            # Should have delayed at least request_delay seconds
            assert elapsed >= client.config.request_delay
    
    @patch('requests.Session.get')
    def test_get_card_info_success(self, mock_get, client):
        """Test successful card info retrieval"""
        # Mock HTML response
        html = '''
        <html>
            <h1 class="card-name">Spider-Man</h1>
            <div class="card-text">Response ability text</div>
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_card_info('01001a')
        
        assert result['code'] == '01001a'
        assert result['name'] == 'Spider-Man'
        assert 'Response ability' in result['text']
    
    @patch('requests.Session.get')
    def test_get_card_info_failure(self, mock_get, client):
        """Test card info retrieval failure"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(ValueError, match="Failed to fetch"):
            client.get_card_info('01001a')
    
    @patch('requests.Session.get')
    def test_get_card_image_url(self, mock_get, client):
        """Test getting card image URL"""
        html = '''
        <html>
            <img class="card-image" src="//example.com/card.jpg" />
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        url = client.get_card_image_url('01001a')
        
        assert url == 'https://example.com/card.jpg'
    
    @patch('requests.Session.get')
    def test_get_card_image_url_relative(self, mock_get, client):
        """Test getting card image with relative URL"""
        html = '''
        <html>
            <img class="card-image" src="/images/card.jpg" />
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        url = client.get_card_image_url('01001a')
        
        assert url == 'https://marvelcdb.com/images/card.jpg'
    
    @patch('requests.Session.get')
    def test_download_card_image(self, mock_get, client):
        """Test downloading card image"""
        image_data = b'\x89PNG\r\n\x1a\n...'  # Fake PNG data
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = image_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.download_card_image('https://example.com/card.png')
        
        assert result == image_data
    
    @patch('requests.Session.get')
    def test_download_card_image_failure(self, mock_get, client):
        """Test card image download failure"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            client.download_card_image('https://example.com/card.png')
    
    @patch('requests.Session.get')
    def test_get_deck_cards(self, mock_get, client):
        """Test getting deck cards"""
        html = '''
        <html>
            <tr class="card-container" data-code="01001a">
                <td class="qty">3</td>
            </tr>
            <tr class="card-container" data-code="01002a">
                <td class="qty">2</td>
            </tr>
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_deck_cards('12345')
        
        assert len(result) == 2
        assert result[0]['code'] == '01001a'
        assert result[0]['quantity'] == 3
        assert result[1]['code'] == '01002a'
        assert result[1]['quantity'] == 2
    
    @patch('requests.Session.get')
    def test_get_user_decks(self, mock_get, client):
        """Test getting user's deck list"""
        html = '''
        <html>
            <tr class="decklist">
                <a href="/decklist/view/12345">My Spider-Man Deck</a>
            </tr>
            <tr class="decklist">
                <a href="/decklist/view/67890">My Iron Man Deck</a>
            </tr>
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_user_decks()
        
        assert len(result) == 2
        assert result[0]['id'] == '12345'
        assert result[0]['name'] == 'My Spider-Man Deck'
    
    def test_extract_deck_id_from_url(self, client):
        """Test extracting deck ID from URL"""
        url1 = '/decklist/view/12345'
        assert client._extract_deck_id_from_url(url1) == '12345'
        
        url2 = 'https://marvelcdb.com/decklist/view/67890'
        assert client._extract_deck_id_from_url(url2) == '67890'
        
        url3 = ''
        assert client._extract_deck_id_from_url(url3) is None
