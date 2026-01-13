import requests
import time
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from src.config import MarvelCDBConfig
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway


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
    
    def set_session_cookie(self, cookie: str) -> None:
        """Set the session cookie for authenticated requests"""
        # Try multiple common cookie names
        for cookie_name in ['laravel_session', 'session', 'PHPSESSID', 'marvelcdb_session']:
            self.session.cookies.set(cookie_name, cookie, domain='marvelcdb.com')
    
    def get_user_decks(self) -> List[Dict[str, Any]]:
        """
        Retrieve user's deck list from MarvelCDB.
        Returns: [{'id': '...', 'name': '...'}, ...]
        """
        self._rate_limit()
        
        try:
            url = f"{self.config.base_url}/decklists/mine"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            decks = []
            # Try multiple selector patterns for deck listings
            for deck_elem in soup.select('tr.decklist, .decklist-item, .deck-row'):
                try:
                    # Find the link to the deck
                    deck_link = deck_elem.select_one('a[href*="decklist"]')
                    if not deck_link:
                        continue
                    
                    deck_id = self._extract_deck_id_from_url(deck_link.get('href', ''))
                    deck_name = deck_link.get_text(strip=True)
                    
                    if deck_id and deck_name:
                        decks.append({
                            'id': deck_id,
                            'name': deck_name
                        })
                except Exception as e:
                    print(f"Error parsing deck element: {e}")
                    continue
            
            return decks
            
        except requests.RequestException as e:
            print(f"Error fetching user decks: {e}")
            return []
    
    def get_deck_cards(self, deck_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve card list for a deck.
        Returns: [{'code': '...', 'quantity': 3}, ...]
        """
        self._rate_limit()
        
        try:
            url = f"{self.config.base_url}/decklist/view/{deck_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            cards = []
            
            # Try to find cards in the deck listing
            # MarvelCDB typically shows cards in a table or list
            for card_elem in soup.select('tr.card-container, .card-line, [data-code]'):
                try:
                    # Extract card code
                    code = card_elem.get('data-code')
                    if not code:
                        code_elem = card_elem.select_one('[data-code]')
                        if code_elem:
                            code = code_elem.get('data-code')
                    
                    # Extract quantity
                    quantity_elem = card_elem.select_one('.qty, .quantity, td.qty')
                    quantity = 1
                    if quantity_elem:
                        qty_text = quantity_elem.get_text(strip=True)
                        if qty_text and qty_text.isdigit():
                            quantity = int(qty_text)
                    
                    if code:
                        cards.append({
                            'code': code,
                            'quantity': quantity
                        })
                except Exception as e:
                    print(f"Error parsing card element: {e}")
                    continue
            
            return cards
            
        except requests.RequestException as e:
            print(f"Error fetching deck cards: {e}")
            return []
    
    def get_card_info(self, card_code: str) -> Dict[str, Any]:
        """
        Retrieve basic card info (code, name, text).
        Returns: {'code': '...', 'name': '...', 'text': '...'}
        """
        self._rate_limit()
        
        try:
            url = f"{self.config.base_url}/card/{card_code}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract card name
            name = None
            name_elem = soup.select_one('h1.card-name, h1, .card-title')
            if name_elem:
                name = name_elem.get_text(strip=True)
            
            # Extract card text for accessibility
            text = None
            text_elem = soup.select_one('.card-text, .card-ability, [class*="text"]')
            if text_elem:
                text = text_elem.get_text(strip=True)
            
            return {
                'code': card_code,
                'name': name or card_code,
                'text': text
            }
            
        except requests.RequestException as e:
            print(f"Error fetching card info: {e}")
            return {
                'code': card_code,
                'name': card_code,
                'text': None
            }
    
    def get_card_image_url(self, card_code: str) -> Optional[str]:
        """Get the image URL for a card"""
        self._rate_limit()
        
        try:
            url = f"{self.config.base_url}/card/{card_code}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for card image
            img = soup.select_one('img.card-image, img[alt*="card"], .card-preview img')
            if img and img.get('src'):
                src = img['src']
                # Handle relative URLs
                if src.startswith('//'):
                    return 'https:' + src
                elif src.startswith('/'):
                    return self.config.base_url + src
                return src
            
            return None
            
        except requests.RequestException as e:
            print(f"Error getting card image URL: {e}")
            return None
    
    def download_card_image(self, image_url: str) -> bytes:
        """Download card image binary data"""
        self._rate_limit()
        
        try:
            response = self.session.get(image_url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"Error downloading image: {e}")
            raise
    
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


