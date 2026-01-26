"""
Additional unit tests for improved coverage of interactors.

These tests focus on business logic coverage and edge cases.
"""

import pytest
from unittest.mock import Mock, patch
from src.entities import Card, Deck, DeckCard, Game
from src.entities.deck import DeckList
from src.interactors import CardInteractor, DeckInteractor, GameInteractor


class TestCardInteractorAdvanced:
    """Advanced unit tests for CardInteractor"""
    
    @pytest.fixture
    def card_interactor(self):
        """Create card interactor with mocks"""
        mock_repo = Mock()
        mock_gateway = Mock()
        mock_storage = Mock()
        return CardInteractor(mock_repo, mock_gateway, mock_storage)
    
    def test_import_card_from_marvelcdb_new(self, card_interactor):
        """Test importing a new card from MarvelCDB"""
        card_interactor.card_repo.find_by_code = Mock(return_value=None)
        card_interactor.marvelcdb.get_card_info = Mock(return_value={
            'code': 'test_card',
            'name': 'Test Card',
            'text': 'Test text'
        })
        card_interactor.image_storage.image_exists = Mock(return_value=False)
        
        created_card = Card(code='test_card', name='Test Card', text='Test text')
        card_interactor.card_repo.save = Mock(return_value=created_card)
        
        with patch.object(card_interactor, '_download_card_image'):
            result = card_interactor.import_card_from_marvelcdb('test_card')
        
        assert result is not None
        assert result.code == 'test_card'
        card_interactor.card_repo.save.assert_called_once()
    
    def test_import_card_already_exists(self, card_interactor):
        """Test importing a card that already exists"""
        existing_card = Card(code='test_card', name='Test Card')
        card_interactor.card_repo.find_by_code = Mock(return_value=existing_card)
        card_interactor.image_storage.image_exists = Mock(return_value=True)
        
        result = card_interactor.import_card_from_marvelcdb('test_card')
        
        assert result == existing_card
        card_interactor.card_repo.save.assert_not_called()
    
    def test_search_cards_by_name(self, card_interactor):
        """Test searching cards by name"""
        cards = (
            Card(code='card1', name='Iron Man'),
            Card(code='card2', name='Iron Patriot')
        )
        card_interactor.card_repo.search_by_name = Mock(return_value=cards)
        
        result = card_interactor.search_cards('Iron')
        
        assert len(result) == 2
        card_interactor.card_repo.search_by_name.assert_called_once_with('Iron')
    
    def test_get_card_not_found(self, card_interactor):
        """Test getting a card that doesn't exist"""
        card_interactor.card_repo.find_by_code = Mock(return_value=None)
        
        result = card_interactor.get_card('nonexistent')
        
        assert result is None
    
    def test_get_card_found(self, card_interactor):
        """Test getting a card that exists"""
        card = Card(code='test', name='Test Card')
        card_interactor.card_repo.find_by_code = Mock(return_value=card)
        
        result = card_interactor.get_card('test')
        
        assert result == card
    
    def test_get_multiple_cards(self, card_interactor):
        """Test getting multiple cards"""
        cards = (
            Card(code='card1', name='Card 1'),
            Card(code='card2', name='Card 2')
        )
        card_interactor.card_repo.find_by_codes = Mock(return_value=cards)
        
        result = card_interactor.get_cards(['card1', 'card2'])
        
        assert len(result) == 2


class TestDeckInteractorAdvanced:
    """Advanced unit tests for DeckInteractor"""
    
    @pytest.fixture
    def deck_interactor(self):
        """Create deck interactor with mocks"""
        mock_deck_repo = Mock()
        mock_card_interactor = Mock(spec=CardInteractor)
        mock_gateway = Mock()
        
        return DeckInteractor(mock_deck_repo, mock_card_interactor, mock_gateway)
    
    def test_import_deck_from_marvelcdb(self, deck_interactor):
        """Test importing a deck from MarvelCDB"""
        deck_list = DeckList(
            id='deck123',
            name='Imported',
            cards=(
                DeckCard(code='card1', name='Card 1', quantity=2),
                DeckCard(code='card2', name='Card 2', quantity=1)
            )
        )

        deck_interactor.marvelcdb.get_deck_cards = Mock(return_value=deck_list)
        
        created_deck = deck_interactor.marvelcdb.get_cards_from_deck_list(deck_list)
        deck_interactor.deck_repo.save = Mock(return_value=created_deck)
        
        result = deck_interactor.import_deck_from_marvelcdb('deck123')
        
        assert result is not None
        deck_interactor.deck_repo.save.assert_called_once()
    
    def test_import_deck_no_cards(self, deck_interactor):
        """Test importing a deck with no cards raises error"""
        deck_interactor.marvelcdb.get_deck = Mock(return_value=[])
        
        with pytest.raises(ValueError):
            deck_interactor.import_deck_from_marvelcdb('deck123')

class TestGameInteractorAdvanced:
    """Advanced unit tests for GameInteractor"""
    
    @pytest.fixture
    def game_interactor(self):
        """Create game interactor with mocks"""
        mock_repo = Mock()
        mock_deck_interactor = Mock(spec=DeckInteractor)
        
        interactor = GameInteractor(mock_repo, mock_deck_interactor)
        return interactor
    
    def test_create_game_mismatched_players_decks(self, game_interactor):
        """Test creating a game with mismatched players and decks raises error"""
        deck_ids = ['deck1']
        player_names = ['Player 1', 'Player 2']
        
        with pytest.raises(ValueError):
            game_interactor.create_game('Test Game', deck_ids, player_names)
    
    def test_create_game_deck_not_found(self, game_interactor):
        """Test creating a game when deck not found raises error"""
        game_interactor.deck_interactor.get_deck_with_cards = Mock(return_value=None)
        
        with pytest.raises(ValueError):
            game_interactor.create_game('Test Game', ['deck1'], ['Player 1'])
    
    def test_get_game_not_found(self, game_interactor):
        """Test getting a game that doesn't exist"""
        game_interactor.game_repo.find_by_id = Mock(return_value=None)
        
        result = game_interactor.get_game('nonexistent')
        
        assert result is None
        game_interactor.game_repo.find_by_id.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_deck_zones(self):
        """Test creating empty play zone"""
        from src.entities import PlayZone, Position
        zone = PlayZone()
        
        assert len(zone.decks_in_play) == 0
        assert len(zone.cards_in_play) == 0
    
    def test_card_with_zero_cost(self):
        """Test card creation"""
        card = Card(code='card_free', name='Free Card')
        assert card.code == 'card_free'
    
    def test_deck_with_cards(self):
        """Test creating a deck with cards"""
        cards = [
            DeckCard(code='card1', name='Card 1', quantity=2),
            DeckCard(code='card2', name='Card 2', quantity=1)
        ]
        deck = Deck(id='test', name='Test', cards=cards)
        
        assert len(deck.cards) == 2
    
    def test_game_creation(self):
        """Test creating a game"""
        from src.entities import GamePhase, Player
        player = Player(name='Player 1')
        game = Game(
            name='Test Game',
            host='Player 1',
            phase=GamePhase.LOBBY,
            players=(player,),
            play_zone=None
        )
        
        assert game.name == 'Test Game'
        assert len(game.players) == 1


class TestMockingPatterns:
    """Test mocking patterns and patterns for complex scenarios"""
    
    def test_card_interactor_with_gateway_mock(self):
        """Test mocking external gateway calls"""
        mock_repo = Mock()
        mock_gateway = Mock()
        mock_storage = Mock()
        
        interactor = CardInteractor(mock_repo, mock_gateway, mock_storage)
        
        # Setup mocks
        mock_gateway.get_card_info = Mock(return_value={'code': 'test', 'name': 'Test'})
        mock_repo.find_by_code = Mock(return_value=None)
        mock_repo.save = Mock(return_value=Card(code='test', name='Test'))
        mock_storage.image_exists = Mock(return_value=False)
        
        with patch.object(interactor, '_download_card_image'):
            result = interactor.import_card_from_marvelcdb('test')
        
        assert result is not None
        mock_gateway.get_card_info.assert_called_once_with('test')
