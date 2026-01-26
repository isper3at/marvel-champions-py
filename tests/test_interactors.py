"""Tests for interactor business logic"""

import pytest
from src.interactors import CardInteractor, DeckInteractor, GameInteractor
from src.repositories import MongoCardRepository, MongoDeckRepository, MongoGameRepository
from src.gateways import LocalImageStorage
from src.entities import Card, Deck, DeckCard, Position


class TestCardInteractor:
    """Test CardInteractor"""
    
    def test_get_card(self, test_db):
        """Test getting a card"""
        repo = MongoCardRepository(test_db)
        repo.save(Card(code='01001a', name='Spider-Man'))
        
        # Mock gateway and storage
        class MockGateway:
            def get_card_info(self, code):
                return {'code': code, 'name': 'Mock', 'text': None}
        
        class MockStorage:
            def image_exists(self, code):
                return False
        
        interactor = CardInteractor(repo, MockGateway(), MockStorage())
        
        card = interactor.get_card('01001a')
        assert card is not None
        assert card.name == 'Spider-Man'
    
    def test_search_cards(self, test_db):
        """Test searching cards"""
        repo = MongoCardRepository(test_db)
        repo.save_all([
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Spider-Woman'),
        ])
        
        class MockGateway:
            pass
        
        class MockStorage:
            pass
        
        interactor = CardInteractor(repo, MockGateway(), MockStorage())
        
        results = interactor.search_cards('spider')
        assert len(results) == 2