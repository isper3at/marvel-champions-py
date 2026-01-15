"""Tests for Lobby Controller - REST API endpoints"""

import pytest
import json
from src.entities import Card, Deck, DeckCard
from src.repositories import MongoCardRepository, MongoDeckRepository


class TestLobbyController:
    """Test Lobby Controller REST endpoints"""
    
    @pytest.fixture
    def sample_deck(self, test_db):
        """Create a sample deck for testing"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        # Create cards
        card_repo.save_all([
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Web-Swing'),
        ])
        
        # Create deck
        deck = Deck(
            id=None,
            name='Spider-Man Deck',
            cards=(
                DeckCard(code='01001a', quantity=1),
                DeckCard(code='01002a', quantity=3),
            )
        )
        return deck_repo.save(deck)
    
    @pytest.fixture
    def encounter_deck(self, test_db):
        """Create encounter deck"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        card_repo.save_all([
            Card(code='enc_001', name='Rhino'),
            Card(code='enc_002', name='Charge'),
        ])
        
        deck = Deck(
            id=None,
            name='Rhino Encounter',
            cards=(
                DeckCard(code='enc_001', quantity=1),
                DeckCard(code='enc_002', quantity=5),
            )
        )
        return deck_repo.save(deck)
    
    # ========================================================================
    # CREATE LOBBY TESTS
    # ========================================================================
    
    def test_create_lobby_success(self, client):
        """Test POST /api/lobby - create lobby"""
        response = client.post(
            '/api/lobby',
            data=json.dumps({
                'name': 'Test Game',
                'username': 'Alice'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['lobby']['name'] == 'Test Game'
        assert data['lobby']['host'] == 'Alice'
        assert data['lobby']['status'] == 'lobby'
        assert len(data['lobby']['players']) == 1
        assert data['lobby']['players'][0]['username'] == 'Alice'
        assert data['lobby']['players'][0]['is_host'] is True
    
    def test_create_lobby_missing_name(self, client):
        """Test creating lobby without name fails"""
        response = client.post(
            '/api/lobby',
            data=json.dumps({'username': 'Alice'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_lobby_missing_username(self, client):
        """Test creating lobby without username fails"""
        response = client.post(
            '/api/lobby',
            data=json.dumps({'name': 'Test Game'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    # ========================================================================
    # LIST LOBBIES TESTS
    # ========================================================================
    
    def test_list_lobbies_empty(self, client):
        """Test GET /api/lobby - list empty lobbies"""
        response = client.get('/api/lobby')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['lobbies'] == []
        assert data['count'] == 0
    
    def test_list_lobbies_multiple(self, client):
        """Test listing multiple lobbies"""
        # Create lobbies
        client.post('/api/lobby', data=json.dumps({
            'name': 'Game 1', 'username': 'Alice'
        }), content_type='application/json')
        
        client.post('/api/lobby', data=json.dumps({
            'name': 'Game 2', 'username': 'Bob'
        }), content_type='application/json')
        
        # List lobbies
        response = client.get('/api/lobby')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['count'] == 2
        names = [lobby['name'] for lobby in data['lobbies']]
        assert 'Game 1' in names
        assert 'Game 2' in names
    
    # ========================================================================
    # GET LOBBY TESTS
    # ========================================================================
    
    def test_get_lobby_success(self, client):
        """Test GET /api/lobby/<id> - get lobby details"""
        # Create lobby
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        # Get lobby
        response = client.get(f'/api/lobby/{lobby_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['name'] == 'Test Game'
        assert data['host'] == 'Alice'
        assert data['all_ready'] is False
        assert data['can_start'] is False
    
    def test_get_lobby_not_found(self, client):
        """Test getting non-existent lobby"""
        response = client.get('/api/lobby/nonexistent_id')
        
        assert response.status_code == 404
    
    # ========================================================================
    # JOIN LOBBY TESTS
    # ========================================================================
    
    def test_join_lobby_success(self, client):
        """Test POST /api/lobby/<id>/join - join lobby"""
        # Create lobby
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        # Join lobby
        response = client.post(
            f'/api/lobby/{lobby_id}/join',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert len(data['lobby']['players']) == 2
        usernames = [p['username'] for p in data['lobby']['players']]
        assert 'Alice' in usernames
        assert 'Bob' in usernames
    
    def test_join_lobby_duplicate(self, client):
        """Test joining lobby twice with same username"""
        # Create and join
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        client.post(
            f'/api/lobby/{lobby_id}/join',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        # Try to join again
        response = client.post(
            f'/api/lobby/{lobby_id}/join',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    # ========================================================================
    # LEAVE LOBBY TESTS
    # ========================================================================
    
    def test_leave_lobby_success(self, client):
        """Test POST /api/lobby/<id>/leave - leave lobby"""
        # Create and join
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        client.post(
            f'/api/lobby/{lobby_id}/join',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        # Leave lobby
        response = client.post(
            f'/api/lobby/{lobby_id}/leave',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['lobby_deleted'] is False
    
    def test_leave_lobby_host_deletes(self, client):
        """Test that host leaving deletes lobby"""
        # Create lobby
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        # Host leaves
        response = client.post(
            f'/api/lobby/{lobby_id}/leave',
            data=json.dumps({'username': 'Alice'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['lobby_deleted'] is True
        
        # Verify lobby is gone
        get_response = client.get(f'/api/lobby/{lobby_id}')
        assert get_response.status_code == 404
    
    # ========================================================================
    # CHOOSE DECK TESTS
    # ========================================================================
    
    def test_choose_deck_success(self, client, sample_deck):
        """Test PUT /api/lobby/<id>/deck - choose deck"""
        # Create lobby
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        # Choose deck
        response = client.put(
            f'/api/lobby/{lobby_id}/deck',
            data=json.dumps({
                'username': 'Alice',
                'deck_id': sample_deck.id
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['player']['deck_id'] == sample_deck.id
    
    def test_choose_deck_not_found(self, client):
        """Test choosing non-existent deck"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        response = client.put(
            f'/api/lobby/{lobby_id}/deck',
            data=json.dumps({
                'username': 'Alice',
                'deck_id': 'nonexistent'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    # ========================================================================
    # SET ENCOUNTER DECK TESTS
    # ========================================================================
    
    def test_set_encounter_deck_success(self, client, encounter_deck):
        """Test PUT /api/lobby/<id>/encounter - set encounter deck"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        response = client.put(
            f'/api/lobby/{lobby_id}/encounter',
            data=json.dumps({
                'username': 'Alice',
                'encounter_deck_id': encounter_deck.id
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['encounter_deck_id'] == encounter_deck.id
    
    def test_set_encounter_deck_non_host(self, client, encounter_deck):
        """Test that non-host cannot set encounter deck"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        # Join as Bob
        client.post(
            f'/api/lobby/{lobby_id}/join',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        # Bob tries to set encounter deck
        response = client.put(
            f'/api/lobby/{lobby_id}/encounter',
            data=json.dumps({
                'username': 'Bob',
                'encounter_deck_id': encounter_deck.id
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 403
    
    # ========================================================================
    # TOGGLE READY TESTS
    # ========================================================================
    
    def test_toggle_ready_success(self, client, sample_deck):
        """Test POST /api/lobby/<id>/ready - toggle ready"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        # Choose deck first
        client.put(
            f'/api/lobby/{lobby_id}/deck',
            data=json.dumps({
                'username': 'Alice',
                'deck_id': sample_deck.id
            }),
            content_type='application/json'
        )
        
        # Toggle ready
        response = client.post(
            f'/api/lobby/{lobby_id}/ready',
            data=json.dumps({'username': 'Alice'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['player']['is_ready'] is True
    
    def test_toggle_ready_without_deck(self, client):
        """Test that cannot ready without deck"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        response = client.post(
            f'/api/lobby/{lobby_id}/ready',
            data=json.dumps({'username': 'Alice'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    # ========================================================================
    # START GAME TESTS
    # ========================================================================
    
    def test_start_game_success(self, client, sample_deck, encounter_deck):
        """Test POST /api/lobby/<id>/start - start game"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        # Setup: choose deck, encounter, ready
        client.put(
            f'/api/lobby/{lobby_id}/deck',
            data=json.dumps({
                'username': 'Alice',
                'deck_id': sample_deck.id
            }),
            content_type='application/json'
        )
        
        client.put(
            f'/api/lobby/{lobby_id}/encounter',
            data=json.dumps({
                'username': 'Alice',
                'encounter_deck_id': encounter_deck.id
            }),
            content_type='application/json'
        )
        
        client.post(
            f'/api/lobby/{lobby_id}/ready',
            data=json.dumps({'username': 'Alice'}),
            content_type='application/json'
        )
        
        # Start game
        response = client.post(
            f'/api/lobby/{lobby_id}/start',
            data=json.dumps({'username': 'Alice'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['status'] == 'in_progress'
        assert 'Alice' in data['players']
    
    def test_start_game_non_host(self, client, sample_deck, encounter_deck):
        """Test that non-host cannot start game"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        # Join as Bob
        client.post(
            f'/api/lobby/{lobby_id}/join',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        # Setup lobby (as host)
        client.put(
            f'/api/lobby/{lobby_id}/deck',
            data=json.dumps({
                'username': 'Alice',
                'deck_id': sample_deck.id
            }),
            content_type='application/json'
        )
        
        client.put(
            f'/api/lobby/{lobby_id}/encounter',
            data=json.dumps({
                'username': 'Alice',
                'encounter_deck_id': encounter_deck.id
            }),
            content_type='application/json'
        )
        
        client.post(
            f'/api/lobby/{lobby_id}/ready',
            data=json.dumps({'username': 'Alice'}),
            content_type='application/json'
        )
        
        # Bob tries to start
        response = client.post(
            f'/api/lobby/{lobby_id}/start',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        assert response.status_code == 403
    
    # ========================================================================
    # DELETE LOBBY TESTS
    # ========================================================================
    
    def test_delete_lobby_success(self, client):
        """Test DELETE /api/lobby/<id> - delete lobby"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        response = client.delete(
            f'/api/lobby/{lobby_id}',
            data=json.dumps({'username': 'Alice'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify deleted
        get_response = client.get(f'/api/lobby/{lobby_id}')
        assert get_response.status_code == 404
    
    def test_delete_lobby_non_host(self, client):
        """Test that non-host cannot delete lobby"""
        create_response = client.post('/api/lobby', data=json.dumps({
            'name': 'Test Game', 'username': 'Alice'
        }), content_type='application/json')
        
        lobby_id = json.loads(create_response.data)['lobby']['id']
        
        client.post(
            f'/api/lobby/{lobby_id}/join',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        response = client.delete(
            f'/api/lobby/{lobby_id}',
            data=json.dumps({'username': 'Bob'}),
            content_type='application/json'
        )
        
        assert response.status_code == 403
