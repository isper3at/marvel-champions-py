import requests
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import time
import json
import re
from bs4 import BeautifulSoup

class MarvelCDBGateway(ABC):
    """External Business Interface for MarvelCDB API"""
    
    @abstractmethod
    def get_cards(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_decks(self, deck_id: int) -> Dict[str, Any]:
        pass


class MarvelCDBClient(MarvelCDBGateway):
    """Concrete implementation of MarvelCDB gateway"""
    
    def __init__(self, config):
        """Initialize with configuration object"""
        self.config = config
        # config may be a dataclass (from config.py) or a dict; prefer attributes
        self.base_url = getattr(config, 'base_url', None) or (config.get('marvelcdb_base_url') if isinstance(config, dict) else 'http://marvelcdb.com/')
        self.session = requests.Session()
        self.rate_limit = getattr(config, 'rate_limit_period', None) or (config.get('rate_limit_period') if isinstance(config, dict) else 10)
        self.rate_limit_calls = getattr(config, 'rate_limit_calls', None) or (config.get('rate_limit_calls') if isinstance(config, dict) else 10)
        self.request_delay = getattr(config, 'request_delay', None) or (config.get('request_delay') if isinstance(config, dict) else 0)
        self.last_request_time = 0
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        if self.request_delay > 0:
            time.sleep(self.request_delay)
        self.last_request_time = time.time()
    
    def _parse_html_response(self, html: str) -> Dict[str, Any]:
        """
        Parse MarvelCDB HTML response when JSON API is not available.
        Attempts to extract deck data from HTML using BeautifulSoup.
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try to find deck data in script tags (modern SPAs store JSON in window.__data)
            script_tags = soup.find_all('script', type='application/json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and ('cards' in data or 'decklist' in data):
                        return data
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Fallback: extract meta information from HTML
            deck_data = {'cards': [], 'parsed_from_html': True}
            
            # Try to extract title
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                deck_data['name'] = title_tag.get_text(strip=True)
            
            # Try to extract cards from data attributes or structured markup
            card_elements = soup.find_all('div', class_=re.compile('card|deck-card', re.I))
            for elem in card_elements:
                card_name = elem.get_text(strip=True)
                if card_name:
                    deck_data['cards'].append({
                        'name': card_name,
                        'quantity': 1,
                        'parsed_from_html': True
                    })
            
            return deck_data
        
        except Exception as e:
            raise Exception(f"Failed to parse HTML response: {e}")
    
    def get_cards(self, card_id: int) -> List[Dict[str, Any]]:
        """Retrieve a specific card by ID"""
        try:
            self._apply_rate_limit()
            response = self.session.get(f"{self.base_url}/card/{card_id}")
            response.raise_for_status()
            
            # Try JSON first
            if response.headers.get('Content-Type', '').startswith('application/json'):
                return response.json()
            else:
                # Fall back to HTML parsing
                return self._parse_html_response(response.text)
        
        except requests.RequestException as e:
            raise Exception(f"Failed to retrieve cards: {e}")
    
    def get_decks(self, deck_id: int) -> Dict[str, Any]:
        """Retrieve a specific deck by ID"""
        try:
            self._apply_rate_limit()
            # Try API endpoint first
            response = self.session.get(f"{self.base_url}/api/public/decklist/{deck_id}")
            response.raise_for_status()
            
            # Check if response is JSON
            if response.headers.get('Content-Type', '').startswith('application/json'):
                return response.json()
            
            # If not JSON, fall back to HTML parsing
            return self._parse_html_response(response.text)
        
        except requests.RequestException:
            # Fallback: try HTML deck page
            try:
                self._apply_rate_limit()
                response = self.session.get(f"{self.base_url}/decklist/{deck_id}")
                response.raise_for_status()
                return self._parse_html_response(response.text)
            except requests.RequestException as e:
                raise Exception(f"Failed to retrieve deck {deck_id}: {e}")
