import requests
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import time

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
        self.base_url = config.get('marvelcdb_base_url', 'http://marvelcdb.com/')
        self.session = requests.Session()
        self.rate_limit = config.get('rate_limit_period', 10)  # requests per second
        self.rate_limit_calls = config.get('rate_limit_calls', 10)  # number of requests
        self.request_delay = config.get('request_delay', 0)  # delay between requests in seconds
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
    
    def get_cards(self, card_id: int) -> List[Dict[str, Any]]:
        """Retrieve a specific card by ID"""
        try:
            self._apply_rate_limit()
            response = self.session.get(f"{self.base_url}/card/{card_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to retrieve cards: {e}")
    
    def get_decks(self, deck_id: int) -> Dict[str, Any]:
        """Retrieve a specific deck by ID"""
        try:
            self._apply_rate_limit()
            response = self.session.get(f"{self.base_url}/deck/{deck_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to retrieve deck {deck_id}: {e}")
