"""
Controller Tests - Test API endpoints and HTTP handling.

These tests verify:
- Correct HTTP status codes
- Proper response formats
- Input validation
- Error handling
- Integration with interactors
"""

from typing import Optional
import uuid
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from src.controllers import card_bp, deck_bp, game_bp
import datetime
import src.controllers.card_controller as card_controller
import src.controllers.deck_controller as deck_controller
import src.controllers.game_controller as game_controller
from src.entities import Card, Deck, DeckCard, Game, GamePhase, Player, PlayZone, Position, CardInPlay


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Register blueprints
    app.register_blueprint(card_bp)
    app.register_blueprint(deck_bp)
    app.register_blueprint(game_bp)
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_card_interactor():
    """Create mock card interactor"""
    mock = Mock()
    mock.get_card = Mock()
    mock.search_cards = Mock()
    mock.import_card_from_marvelcdb = Mock()
    mock.import_cards_bulk = Mock()
    mock.get_card_image_path = Mock()
    return mock


@pytest.fixture
def mock_deck_interactor():
    """Create mock deck interactor"""
    mock = Mock()
    mock.get_all_decks = Mock()
    mock.get_deck = Mock()
    mock.create_deck = Mock()
    mock.update_deck = Mock()
    mock.delete_deck = Mock()
    mock.get_deck_with_cards = Mock()
    mock.import_deck_from_marvelcdb = Mock()
    return mock


@pytest.fixture
def mock_game_interactor():
    """Create mock game interactor"""
    mock = Mock()
    mock.get_all_games = Mock()
    mock.get_recent_games = Mock()
    mock.get_game = Mock()
    mock.create_game = Mock()
    mock.delete_game = Mock()
    mock.draw_card = Mock()
    mock.shuffle_discard = Mock()
    mock.play_card = Mock()
    return mock


class TestCardController:
    """Test card API endpoints"""
    
    def test_get_card_success(self, app, client, mock_card_interactor):
        """Test getting a card successfully"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            card = Card(code='test_card', name='Test Card', text='Test text')
            mock_card_interactor.get_card.return_value = card
            
            response = client.get('/api/cards/test_card')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['code'] == 'test_card'
            assert data['name'] == 'Test Card'
            mock_card_interactor.get_card.assert_called_once_with('test_card')
    
    def test_get_card_not_found(self, app, client, mock_card_interactor):
        """Test getting a card that doesn't exist"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            mock_card_interactor.get_card.return_value = None
            
            response = client.get('/api/cards/nonexistent')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
            assert data['error'] == 'Card not found'
    
    def test_search_cards_success(self, app, client, mock_card_interactor):
        """Test searching for cards"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            cards = (
                Card(code='card1', name='Iron Man'),
                Card(code='card2', name='Iron Patriot')
            )
            mock_card_interactor.search_cards.return_value = cards
            
            response = client.get('/api/cards/search?q=Iron')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['count'] == 2
            assert len(data['results']) == 2
            assert data['results'][0]['name'] == 'Iron Man'
    
    def test_search_cards_missing_query(self, app, client, mock_card_interactor):
        """Test search without query parameter"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            response = client.get('/api/cards/search')
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_search_cards_empty_results(self, app, client, mock_card_interactor):
        """Test search with no results"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            mock_card_interactor.search_cards.return_value = ()
            
            response = client.get('/api/cards/search?q=xyz')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['count'] == 0
            assert len(data['results']) == 0
    
    def test_import_card_success(self, app, client, mock_card_interactor):
        """Test importing a card from MarvelCDB"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            card = Card(code='01001', name='Black Widow', text='Fight action')
            mock_card_interactor.import_card_from_marvelcdb.return_value = card
            
            response = client.post(
                '/api/cards/import',
                json={'code': '01001'},
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['card']['code'] == '01001'
            assert data['card']['name'] == 'Black Widow'
    
    def test_import_card_missing_code(self, app, client, mock_card_interactor):
        """Test importing card without code"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            response = client.post(
                '/api/cards/import',
                json={},
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_import_card_error(self, app, client, mock_card_interactor):
        """Test import card error handling"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            mock_card_interactor.import_card_from_marvelcdb.side_effect = ValueError('Invalid code')
            
            response = client.post(
                '/api/cards/import',
                json={'code': 'invalid'},
                content_type='application/json'
            )
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
    
    def test_import_cards_bulk_success(self, app, client, mock_card_interactor):
        """Test bulk importing cards"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            cards = (
                Card(code='card1', name='Card 1'),
                Card(code='card2', name='Card 2'),
                Card(code='card3', name='Card 3')
            )
            mock_card_interactor.import_cards_bulk.return_value = cards
            
            response = client.post(
                '/api/cards/import/bulk',
                json={'codes': ['card1', 'card2', 'card3']},
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['imported'] == 3
            assert len(data['cards']) == 3
    
    def test_import_cards_bulk_missing_codes(self, app, client, mock_card_interactor):
        """Test bulk import without codes"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            response = client.post(
                '/api/cards/import/bulk',
                json={},
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_import_cards_bulk_invalid_type(self, app, client, mock_card_interactor):
        """Test bulk import with non-array codes"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            response = client.post(
                '/api/cards/import/bulk',
                json={'codes': 'not_an_array'},
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_get_card_image_not_found(self, app, client, mock_card_interactor):
        """Test getting image for non-existent card"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            mock_card_interactor.get_card_image_path.return_value = None
            
            response = client.get('/api/cards/nonexistent/image')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data


class TestDeckController:
    """Test deck API endpoints"""
    
    def test_list_decks_success(self, app, client, mock_deck_interactor):
        """Test listing all decks"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            decks = (
                Deck(id='deck1', name='Iron Deck', cards=[]),
                Deck(id='deck2', name='Captain Deck', cards=[])
            )
            mock_deck_interactor.get_all_decks.return_value = decks
            
            response = client.get('/api/decks')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['count'] == 2
            assert len(data['decks']) == 2
            assert data['decks'][0]['name'] == 'Iron Deck'
    
    def test_list_decks_empty(self, app, client, mock_deck_interactor):
        """Test listing decks when none exist"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            mock_deck_interactor.get_all_decks.return_value = ()
            
            response = client.get('/api/decks')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['count'] == 0
            assert len(data['decks']) == 0
    
    def test_get_deck_success(self, app, client, mock_deck_interactor):
        """Test getting a single deck"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            cards = [
                DeckCard(code='card1', name='test', quantity=2),
                DeckCard(code='card2', name='test2', quantity=1)
            ]
            deck = Deck(id='deck1', name='Test Deck', cards=cards)
            mock_deck_interactor.get_deck.return_value = deck
            
            response = client.get('/api/decks/deck1')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['id'] == 'deck1'
            assert data['name'] == 'Test Deck'
            assert data['card_count'] == 3
            assert len(data['cards']) == 2
    
    def test_get_deck_not_found(self, app, client, mock_deck_interactor):
        """Test getting a non-existent deck"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            mock_deck_interactor.get_deck.return_value = None
            
            response = client.get('/api/decks/nonexistent')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_create_deck_success(self, app, client, mock_deck_interactor):
        """Test creating a deck"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            created_deck = Deck(id='new_deck', name='My Deck', cards=[])
            mock_deck_interactor.create_deck.return_value = created_deck
            
            response = client.post(
                '/api/decks',
                json={'name': 'My Deck', 'cards': [{'code': 'card1', 'quantity': 2}]},
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['deck']['name'] == 'My Deck'
    
    def test_create_deck_missing_name(self, app, client, mock_deck_interactor):
        """Test creating deck without name"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            response = client.post(
                '/api/decks',
                json={'cards': []},
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_create_deck_missing_cards(self, app, client, mock_deck_interactor):
        """Test creating deck without cards"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            response = client.post(
                '/api/decks',
                json={'name': 'My Deck'},
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_delete_deck_success(self, app, client, mock_deck_interactor):
        """Test deleting a deck"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            mock_deck_interactor.delete_deck.return_value = True
            
            response = client.delete('/api/decks/deck1')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_delete_deck_not_found(self, app, client, mock_deck_interactor):
        """Test deleting non-existent deck"""
        with app.app_context():
            deck_controller.init_deck_controller(mock_deck_interactor)
            
            mock_deck_interactor.delete_deck.return_value = False
            
            response = client.delete('/api/decks/nonexistent')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data


class TestGameController:
    """Test game API endpoints"""
    
    def test_list_games_success(self, app, client, mock_game_interactor):
        """Test listing all games"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            games = (
                Game(
                    id=uuid.uuid4(),
                    name='Game 1',
                    host='host_player1',
                    phase=GamePhase.LOBBY,
                    players=(),
                    play_zone=None,
                    created_at=datetime.datetime.now(datetime.UTC)
                ),
                Game(
                    id=uuid.uuid4(),
                    name='Game 2',
                    host='host_player2',
                    phase=GamePhase.LOBBY,
                    players=(),
                    play_zone=None,
                    created_at=datetime.datetime.now(datetime.UTC)
                ),
            )
            mock_game_interactor.get_all_games.return_value = games
            
            response = client.get('/api/games')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['count'] == 2
            assert len(data['games']) == 2
    
    def test_get_recent_games_success(self, app, client, mock_game_interactor):
        """Test getting recent games"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            games = (
                Game(
                    id=uuid.uuid4(),
                    name='Recent Game',
                    host='player1',
                    phase=GamePhase.IN_PROGRESS,
                    players=(),
                    play_zone=None,
                    created_at=datetime.datetime.now(datetime.UTC)
                ),
            )
            mock_game_interactor.get_recent_games.return_value = games
            
            response = client.get('/api/games/recent')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['count'] == 1
    
    def test_get_game_success(self, app, client, mock_game_interactor):
        """Test getting a single game"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            game_id = uuid.uuid4()
            game = Game(
                id=game_id,
                name='Test Game',
                host='test_host',
                phase=GamePhase.LOBBY,
                players=(),
                play_zone=None,
                created_at=datetime.datetime.now(datetime.UTC)
            )
            mock_game_interactor.get_game.return_value = game
            
            response = client.get(f'/api/games/{game_id}')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['name'] == 'Test Game'
    
    def test_get_game_not_found(self, app, client, mock_game_interactor):
        """Test getting non-existent game"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            mock_game_interactor.get_game.return_value = None
            
            response = client.get('/api/games/nonexistent')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
    
    def test_create_game_success(self, app, client, mock_game_interactor):
        """Test creating a game"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            game = Game(
                id=uuid.uuid4(),
                name='New Game',
                host='player1',
                phase=GamePhase.LOBBY,
                players=(),
                play_zone=None,
                created_at=datetime.datetime.now(datetime.UTC)
            )
            mock_game_interactor.create_game.return_value = game
            
            response = client.post(
                '/api/games',
                json={
                    'name': 'New Game',
                    'deck_ids': ['deck1'],
                    'player_names': ['Player 1']
                },
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['game']['name'] == 'New Game'
    
    def test_create_game_missing_name(self, app, client, mock_game_interactor):
        """Test creating game without name"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            response = client.post(
                '/api/games',
                json={'deck_ids': ['deck1'], 'player_names': ['Player 1']},
                content_type='application/json'
            )
            
            assert response.status_code == 400
    
    def test_delete_game_success(self, app, client, mock_game_interactor):
        """Test deleting a game"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            mock_game_interactor.delete_game.return_value = True
            
            response = client.delete('/api/games/game1')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_draw_card_success(self, app, client, mock_game_interactor):
        """Test drawing a card in game"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            game = Game(
                id=uuid.uuid4(),
                name='Test Game',
                host='player1',
                phase=GamePhase.IN_PROGRESS,
                players=(),
                play_zone=None,
                created_at=datetime.datetime.now(datetime.UTC)
            )
            mock_game_interactor.draw_card.return_value = game
            
            response = client.post(
                '/api/games/game1/draw',
                json={'player_name': 'Player 1'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_draw_card_missing_player(self, app, client, mock_game_interactor):
        """Test draw without player name"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            response = client.post(
                '/api/games/game1/draw',
                json={},
                content_type='application/json'
            )
            
            assert response.status_code == 400
    
    def test_play_card_success(self, app, client, mock_game_interactor):
        """Test playing a card"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            game = Game(
                id=uuid.uuid4(),
                name='Test Game',
                host='player1',
                phase=GamePhase.IN_PROGRESS,
                players=(),
                play_zone=None,
                created_at=datetime.datetime.now(datetime.UTC)
            )
            mock_game_interactor.play_card_to_table.return_value = game
            
            response = client.post(
                '/api/games/game1/play',
                json={
                    'player_name': 'Player 1',
                    'card_code': 'card1',
                    'x': 10,
                    'y': 20
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_play_card_missing_fields(self, app, client, mock_game_interactor):
        """Test play card with missing required fields"""
        with app.app_context():
            game_controller.init_game_controller(mock_game_interactor)
            
            response = client.post(
                '/api/games/game1/play',
                json={'player_name': 'Player 1'},  # Missing card_code, x, y
                content_type='application/json'
            )
            
            assert response.status_code == 400


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_interactor_exception_handling(self, app, client, mock_card_interactor):
        """Test handling exceptions from interactor"""
        with app.app_context():
            card_controller.init_card_controller(mock_card_interactor)
            
            mock_card_interactor.search_cards.side_effect = RuntimeError('Database error')
            
            response = client.get('/api/cards/search?q=test')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data