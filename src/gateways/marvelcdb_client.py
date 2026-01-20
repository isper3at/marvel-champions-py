import requests
import time
import re
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.config import MarvelCDBConfig
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.entities import Card
from .local_image_storage import LocalImageStorage

class MarvelCDBClient(MarvelCDBGateway):
    """
    Implementation of MarvelCDB gateway.
    Handles web scraping with rate limiting.
    """
    
    def __init__(self, config: MarvelCDBConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.request_delay:
            time.sleep(self.config.request_delay - elapsed)
        self.last_request_time = time.time()
        
    def get_deck_cards(self, deck_id: str) -> Dict[str, int]:
        """
        Parse MarvelCDB deck HTML and extract card codes with quantities.
        
        Args:
            html: HTML string from MarvelCDB deck page
            
        Returns:
            Dictionary mapping card_code -> quantity
            
        Example:
            >>> html = '''<div>1x <a data-code="19020">Gamora</a></div>'''
            >>> parse_deck_html(html)
            {'19020': 1}
        """
        self._rate_limit()
        
        try:
            url = f"{self.config.base_url}/decklist/view/{deck_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            deck_name = soup.find_all('h1', class_='decklist-header')[0].get_text(strip=True)
            deck_meta = soup.find('div', class_='deck-meta')

            cards = {}
            
            deck_content = soup.find_all(class_='deck-content')
            
            for section in deck_content: #column
                for type in section.find_all('div'):
                    for card_div in type.find_all('div'):
                        # Get the text content
                        text = card_div.get_text(strip=True)
                        
                        # Check if this div starts with a quantity pattern (e.g., "1x", "2x", "3x")
                        quantity_match = re.match(r'^(\d+)x\s+', text)
                        
                        if quantity_match:
                            quantity = int(quantity_match.group(1))
                            
                            # Find the <a> tag with data-code attribute
                            link = card_div.find('a', {'data-code': True})
                            
                            if link and link.get('data-code'):
                                card_code = link['data-code']
                                cards[card_code] = quantity
                    
            return cards
            
        except requests.RequestException as e:
            print(f"Error fetching deck cards: {e}")
            return {}
    
    def get_card_from_code(self, card_code: str) -> Card:
        """Fetch card info from MarvelCDB by card code"""
        self._rate_limit()
        
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        try:
            url = f"{self.config.base_url}/card/{card_code}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract card name
            name = None
            name_elem = soup.select_one('a.card-name')
            if name_elem:
                name = name_elem.get_text(strip=True)
            
            # Extract card text for accessibility
            text = None
            text_elem = soup.select_one('div.card-text')#this is a div of <p>
            if text_elem:
                text = text_elem.get_text(strip=True)
            
            return Card(
                code=card_code,
                name=name if name else card_code,
                text=text)
            
        except requests.RequestException as e:
            print(f"Error fetching card info: {e}")
            return Card('-1', 'Unknown Card', 'Unknown')
    
    def get_card_image_url(self, card_code: str, local_image_store: LocalImageStorage = None) -> Optional[str]:
        """
        Extract and download card image from MarvelCDB HTML.
        
        Args:
            html: HTML string from MarvelCDB card/deck page
            card_code: Card code to find image for
            save_dir: Directory to save images (default: 'static/images/cards')
            
        Returns:
            Path to saved image file, or None if not found
            
        Example:
            >>> html = '''<div class="card-thumbnail-wide" style="background-image:url(/bundles/cards/45001a.jpg)"></div>'''
            >>> path = download_card_image(html, '45001a')
            >>> print(path)
            'static/images/cards/45001a.jpg'
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Create save directory if it doesn't exist
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Strategy 1: Look for background-image style with the card code
        # Pattern: background-image:url(/bundles/cards/CARDCODE.jpg)
        elements_with_bg = soup.find_all(style=re.compile(f'background-image.*{card_code}'))
        
        image_url = None
        
        if elements_with_bg:
            # Extract URL from style attribute
            style = elements_with_bg[0].get('style', '')
            url_match = re.search(r'url\((.*?)\)', style)
            if url_match:
                image_url = url_match.group(1).strip('\'"')
        
        # Strategy 2: Look for <img> tags with card code in src
        if not image_url:
            img_tags = soup.find_all('img', src=re.compile(card_code))
            if img_tags:
                image_url = img_tags[0].get('src')
        
        # Strategy 3: Look for any card thumbnail elements
        if not image_url:
            # Common MarvelCDB class patterns
            card_thumbnails = soup.find_all(class_=re.compile('card-thumbnail'))
            for thumbnail in card_thumbnails:
                style = thumbnail.get('style', '')
                if card_code in style:
                    url_match = re.search(r'url\((.*?)\)', style)
                    if url_match:
                        image_url = url_match.group(1).strip('\'"')
                        break
        
        if not image_url:
            print(f"Could not find image URL for card {card_code}")
            return None
        
        # Construct full URL if relative
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            image_url = 'https://marvelcdb.com' + image_url
        
        # Download the image
        try:
            print(f"Downloading image from: {image_url}")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Determine file extension
            if '.png' in image_url.lower():
                ext = '.png'
            elif '.jpg' in image_url.lower() or '.jpeg' in image_url.lower():
                ext = '.jpg'
            else:
                ext = '.jpg'  # Default to jpg
            
            # Save the image
            filename = f"{card_code}{ext}"
            filepath = save_path / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Image saved to: {filepath}")
            return str(filepath)
            
        except requests.RequestException as e:
            print(f"Error downloading image: {e}")
            return None
    
    def _extract_deck_id_from_url(self, url: str) -> Optional[str]:
        """Extract deck ID from URL"""
        if not url:
            return None
        parts = url.split('/')
        # Get last non-empty part
        for part in reversed(parts):
            if part and part.isdigit():
                return part
        return parts[-1] if parts else None
    
    # Additional methods to satisfy the MarvelCDBGateway interface
    def get_card_data(self, card_code: str) -> Dict[str, Any]:
        """Get card data (alias for get_card_info)"""
        return self.get_card_info(card_code)
    
    def get_deck_details(self, deck_id: str) -> Dict[str, Any]:
        """Get deck details (returns card list and deck id)"""
        cards = self.get_deck_cards(deck_id)
        return {'cards': cards, 'id': deck_id}