import requests
import time
import re
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.config import MarvelCDBConfig
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.entities import Card, Deck, DeckCard
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
        
    def get_deck(self, deck_id: str) -> Deck:
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

            cards = []
            
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
                                cards.append(DeckCard(code=str(card_code), quantity=quantity))
                    
            return Deck(
                id=deck_id,
                name=deck_name,
                cards=cards,
                source_url=url
            )
            
        except requests.RequestException as e:
            print(f"Error fetching deck cards: {e}")
            return Deck(id="-1", name="Unknown Deck", cards=[], source_url=None)
    
    def get_card_from_code(self, card_code: str) -> Card:
        """Fetch card info from MarvelCDB by card code"""
        self._rate_limit()
        
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
    
    def get_card_image_url(self, card_code: str, local_image_store: LocalImageStorage) -> Optional[str]:
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

        url = f"{self.config.base_url}/bundles/cards/{card_code}.png"
        
        # 2. Send a GET request to the URL, streaming the response content
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # 3. Check if the request was successful (status code 200)
        if response.status_code == 200:
            # 4. Open a local file in write-binary mode ('wb') and write the content
            local_image_store.save_image(card_code, response.content)
            print(f"Image downloaded successfully!")

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