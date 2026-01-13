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


class TestDeckInteractor:
    """Test DeckInteractor"""
    
    def test_create_deck(self, test_db, image_storage_config):
        """Test creating a deck"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        # Pre-populate cards
        card_repo.save_all([
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Iron Man'),
        ])
        
        class MockGateway:
            pass
        
        class MockStorage:
            def image_exists(self, code):
                return False
        
        card_interactor = CardInteractor(card_repo, MockGateway(), MockStorage())
        deck_interactor = DeckInteractor(deck_repo, card_interactor, MockGateway())
        
        deck = deck_interactor.create_deck(
            'Test Deck',
            [('01001a', 1), ('01002a', 3)]
        )
        
        assert deck.name == 'Test Deck'
        assert len(deck.cards) == 2
    
    def test_get_deck_with_cards(self, test_db):
        """Test getting deck with all card entities"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        # Create cards
        card_repo.save_all([
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Iron Man'),
        ])
        
        # Create deck
        deck = Deck(
            id=None,
            name='Test Deck',
            cards=(
                DeckCard(code='01001a', quantity=1),
                DeckCard(code='01002a', quantity=2),
            )
        )
        saved_deck = deck_repo.save(deck)
        
        class MockGateway:
            pass
        
        class MockStorage:
            def image_exists(self, code):
                return False
        
        card_interactor = CardInteractor(card_repo, MockGateway(), MockStorage())
        deck_interactor = DeckInteractor(deck_repo, card_interactor, MockGateway())
        
        result = deck_interactor.get_deck_with_cards(saved_deck.id)
        assert result is not None
        
        deck, cards = result
        assert deck.name == 'Test Deck'
        # cards list contains 2 unique cards, not 3 total cards
        assert len(cards) == 2


class TestGameInteractor:
    """Test GameInteractor"""
    
    def test_create_game(self, test_db):
        """Test creating a game"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        game_repo = MongoGameRepository(test_db)
        
        # Create cards and deck
        card_repo.save_all([
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Iron Man'),
        ])
        
        deck = Deck(
            id=None,
            name='Test Deck',
            cards=(
                DeckCard(code='01001a', quantity=1),
                DeckCard(code='01002a', quantity=2),
            )
        )
        saved_deck = deck_repo.save(deck)
        
        class MockGateway:
            pass
        
        class MockStorage:
            def image_exists(self, code):
                return False
        
        card_interactor = CardInteractor(card_repo, MockGateway(), MockStorage())
        deck_interactor = DeckInteractor(deck_repo, card_interactor, MockGateway())
        game_interactor = GameInteractor(game_repo, deck_interactor)
        
        game = game_interactor.create_game(
            'Test Game',
            [saved_deck.id],
            ['Alice']
        )
        
        assert game.name == 'Test Game'
        assert len(game.state.players) == 1
        assert game.state.players[0].player_name == 'Alice'
    
    def test_draw_card(self, test_db):
        """Test drawing a card in a game"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        game_repo = MongoGameRepository(test_db)
        
        # Setup
        card_repo.save(Card(code='01001a', name='Spider-Man'))
        deck = Deck(
            id=None,
            name='Test Deck',
            cards=(DeckCard(code='01001a', quantity=3),)
        )
        saved_deck = deck_repo.save(deck)
        
        class MockGateway:
            pass
        
        class MockStorage:
            def image_exists(self, code):
                return False
        
        card_interactor = CardInteractor(card_repo, MockGateway(), MockStorage())
        deck_interactor = DeckInteractor(deck_repo, card_interactor, MockGateway())
        game_interactor = GameInteractor(game_repo, deck_interactor)
        
        # Create game
        game = game_interactor.create_game('Test Game', [saved_deck.id], ['Alice'])
        
        # Get initial state
        alice_before = game.state.get_player('Alice')
        deck_size_before = len(alice_before.deck)
        hand_size_before = len(alice_before.hand)
        
        # Draw card using the game interactor method
        updated_game = game_interactor.draw_card(game.id, 'Alice')
        
        assert updated_game is not None
        alice_after = updated_game.state.get_player('Alice')
        assert len(alice_after.hand) == hand_size_before + 1
        assert len(alice_after.deck) == deck_size_before - 1
    
    def test_play_card_to_table(self, test_db):
        """Test playing a card to the table"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        game_repo = MongoGameRepository(test_db)
        
        # Setup
        card_repo.save(Card(code='01001a', name='Spider-Man'))
        deck = Deck(
            id=None,
            name='Test Deck',
            cards=(DeckCard(code='01001a', quantity=3),)
        )
        saved_deck = deck_repo.save(deck)
        
        class MockGateway:
            pass
        
        class MockStorage:
            def image_exists(self, code):
                return False
        
        card_interactor = CardInteractor(card_repo, MockGateway(), MockStorage())
        deck_interactor = DeckInteractor(deck_repo, card_interactor, MockGateway())
        game_interactor = GameInteractor(game_repo, deck_interactor)
        
        # Create game
        game = game_interactor.create_game('Test Game', [saved_deck.id], ['Alice'])
        
        # Draw a card first using the interactor
        game_with_card = game_interactor.draw_card(game.id, 'Alice')
        
        # Get the card that was drawn
        alice = game_with_card.state.get_player('Alice')
        card_to_play = alice.hand[0]
        
        # Play card to table
        updated_game = game_interactor.play_card_to_table(
            game_with_card.id,
            'Alice',
            card_to_play,
            Position(x=100, y=200)
        )
        
        assert updated_game is not None
        assert len(updated_game.state.play_area) == 1
        assert updated_game.state.play_area[0].position.x == 100
        
        # Verify card was removed from hand
        alice_after = updated_game.state.get_player('Alice')
        assert len(alice_after.hand) == 0