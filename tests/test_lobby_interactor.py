"""Tests for Lobby Interactor - Business logic for game lobby operations"""

import pytest
from datetime import datetime
from src.interactors import LobbyInteractor
from src.repositories import MongoGameRepository, MongoDeckRepository
from src.entities import (
    Game, GamePhase, Player, Deck, DeckCard, Card
)
from src.repositories import MongoCardRepository


class TestLobbyInteractor:
    """Test LobbyInteractor business logic"""
    
    @pytest.fixture
    def lobby_interactor(self, test_db):
        """Create lobby interactor with test database"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        return LobbyInteractor(game_repo, deck_repo)
    
    @pytest.fixture
    def sample_deck(self, test_db):
        """Create a sample deck for testing"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        # Create some cards
        card_repo.save_all([
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Iron Man'),
            Card(code='01003a', name='Web-Swing'),
        ])
        
        # Create a deck
        deck = Deck(
            id=None,
            name='Spider-Man Justice',
            cards=(
                DeckCard(code='01001a', quantity=1),
                DeckCard(code='01002a', quantity=2),
                DeckCard(code='01003a', quantity=3),
            )
        )
        return deck_repo.save(deck)
    
    @pytest.fixture
    def encounter_deck(self, test_db):
        """Create a sample encounter deck"""
        card_repo = MongoCardRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        # Create encounter cards
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
    
    def test_create_lobby(self, lobby_interactor):
        """Test creating a new lobby"""
        game = lobby_interactor.create_lobby('My Game', 'Alice')
        
        assert game.id is not None
        assert game.name == 'My Game'
        assert game.status == GamePhase.LOBBY
        assert game.host == 'Alice'
        assert len(game.players) == 1
        assert game.players[0].username == 'Alice'
        assert game.players[0].is_host is True
        assert game.players[0].is_ready is False
        assert game.players[0].deck_id is None
        assert game.created_at is not None
    
    def test_create_lobby_empty_name(self, lobby_interactor):
        """Test that creating lobby with empty name fails"""
        with pytest.raises(ValueError):
            lobby_interactor.create_lobby('', 'Alice')
    
    def test_create_lobby_empty_host(self, lobby_interactor):
        """Test that creating lobby with empty host fails"""
        with pytest.raises(ValueError):
            lobby_interactor.create_lobby('My Game', '')
    
    # ========================================================================
    # LIST LOBBIES TESTS
    # ========================================================================
    
    def test_list_lobbies_empty(self, lobby_interactor):
        """Test listing lobbies when none exist"""
        lobbies = lobby_interactor.list_lobbies()
        assert len(lobbies) == 0
    
    def test_list_lobbies_multiple(self, lobby_interactor):
        """Test listing multiple lobbies"""
        lobby_interactor.create_lobby('Game 1', 'Alice')
        lobby_interactor.create_lobby('Game 2', 'Bob')
        lobby_interactor.create_lobby('Game 3', 'Carol')
        
        lobbies = lobby_interactor.list_lobbies()
        assert len(lobbies) == 3
        
        names = [g.name for g in lobbies]
        assert 'Game 1' in names
        assert 'Game 2' in names
        assert 'Game 3' in names
    
    def test_list_lobbies_excludes_in_progress(self, lobby_interactor, sample_deck, encounter_deck):
        """Test that list_lobbies excludes games that are IN_PROGRESS"""
        # Create two lobbies
        lobby1 = lobby_interactor.create_lobby('Lobby 1', 'Alice')
        lobby2 = lobby_interactor.create_lobby('Lobby 2', 'Bob')
        
        # Start one of them
        lobby_interactor.choose_deck(lobby1.id, 'Alice', sample_deck.id)
        lobby_interactor.set_encounter_deck(lobby1.id, 'Alice', encounter_deck.id)
        lobby_interactor.toggle_ready(lobby1.id, 'Alice')
        lobby_interactor.start_game(lobby1.id, 'Alice')
        
        # List lobbies should only return the one still in LOBBY status
        lobbies = lobby_interactor.list_lobbies()
        assert len(lobbies) == 1
        assert lobbies[0].name == 'Lobby 2'
    
    # ========================================================================
    # GET LOBBY TESTS
    # ========================================================================
    
    def test_get_lobby_exists(self, lobby_interactor):
        """Test getting a lobby that exists"""
        created = lobby_interactor.create_lobby('My Game', 'Alice')
        
        retrieved = lobby_interactor.get_lobby(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == 'My Game'
    
    def test_get_lobby_not_found(self, lobby_interactor):
        """Test getting a lobby that doesn't exist"""
        result = lobby_interactor.get_lobby('nonexistent_id')
        assert result is None
    
    # ========================================================================
    # JOIN LOBBY TESTS
    # ========================================================================
    
    def test_join_lobby(self, lobby_interactor):
        """Test joining a lobby"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        updated = lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        assert len(updated.lobby_players) == 2
        assert updated.lobby_players[0].username == 'Alice'
        assert updated.lobby_players[1].username == 'Bob'
        assert updated.lobby_players[1].is_host is False
    
    def test_join_lobby_multiple_players(self, lobby_interactor):
        """Test multiple players joining"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        lobby_interactor.join_lobby(lobby.id, 'Carol')
        updated = lobby_interactor.join_lobby(lobby.id, 'Dave')
        
        assert len(updated.lobby_players) == 4
        usernames = [p.username for p in updated.lobby_players]
        assert 'Alice' in usernames
        assert 'Bob' in usernames
        assert 'Carol' in usernames
        assert 'Dave' in usernames
    
    def test_join_lobby_duplicate_player(self, lobby_interactor):
        """Test that joining twice with same username fails"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        with pytest.raises(ValueError, match='already in lobby'):
            lobby_interactor.join_lobby(lobby.id, 'Bob')
    
    def test_join_lobby_not_found(self, lobby_interactor):
        """Test joining a non-existent lobby"""
        with pytest.raises(ValueError, match='not found'):
            lobby_interactor.join_lobby('nonexistent', 'Bob')
    
    # ========================================================================
    # LEAVE LOBBY TESTS
    # ========================================================================
    
    def test_leave_lobby(self, lobby_interactor):
        """Test leaving a lobby"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        updated = lobby_interactor.leave_lobby(lobby.id, 'Bob')
        
        assert updated is not None
        assert len(updated.lobby_players) == 1
        assert updated.lobby_players[0].username == 'Alice'
    
    def test_leave_lobby_host_deletes_lobby(self, lobby_interactor):
        """Test that when host leaves, lobby is deleted"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        result = lobby_interactor.leave_lobby(lobby.id, 'Alice')
        
        assert result is None
        
        # Verify lobby no longer exists
        retrieved = lobby_interactor.get_lobby(lobby.id)
        assert retrieved is None
    
    def test_leave_lobby_last_player_deletes(self, lobby_interactor):
        """Test that when last player leaves, lobby is deleted"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        result = lobby_interactor.leave_lobby(lobby.id, 'Alice')
        
        assert result is None
        retrieved = lobby_interactor.get_lobby(lobby.id)
        assert retrieved is None
    
    # ========================================================================
    # CHOOSE DECK TESTS
    # ========================================================================
    
    def test_choose_deck(self, lobby_interactor, sample_deck):
        """Test choosing a deck"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        updated = lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        
        alice = updated.get_lobby_player('Alice')
        assert alice.deck_id == sample_deck.id
    
    def test_choose_deck_player_not_in_lobby(self, lobby_interactor, sample_deck):
        """Test choosing deck for player not in lobby"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        with pytest.raises(ValueError, match='not in lobby'):
            lobby_interactor.choose_deck(lobby.id, 'Bob', sample_deck.id)
    
    def test_choose_deck_deck_not_found(self, lobby_interactor):
        """Test choosing a deck that doesn't exist"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        with pytest.raises(ValueError, match='not found'):
            lobby_interactor.choose_deck(lobby.id, 'Alice', 'nonexistent_deck')
    
    def test_choose_deck_change_deck(self, lobby_interactor, sample_deck, test_db):
        """Test changing to a different deck"""
        # Create second deck
        deck_repo = MongoDeckRepository(test_db)
        deck2 = Deck(
            id=None,
            name='Iron Man Deck',
            cards=(DeckCard(code='01002a', quantity=3),)
        )
        deck2 = deck_repo.save(deck2)
        
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        # Choose first deck
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        
        # Change to second deck
        updated = lobby_interactor.choose_deck(lobby.id, 'Alice', deck2.id)
        
        alice = updated.get_lobby_player('Alice')
        assert alice.deck_id == deck2.id
    
    # ========================================================================
    # SET ENCOUNTER DECK TESTS
    # ========================================================================
    
    def test_set_encounter_deck(self, lobby_interactor, encounter_deck):
        """Test setting encounter deck"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        updated = lobby_interactor.set_encounter_deck(lobby.id, 'Alice', encounter_deck.id)
        
        assert updated.encounter_deck_id == encounter_deck.id
    
    def test_set_encounter_deck_non_host(self, lobby_interactor, encounter_deck):
        """Test that only host can set encounter deck"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        with pytest.raises(ValueError, match='Only host'):
            lobby_interactor.set_encounter_deck(lobby.id, 'Bob', encounter_deck.id)
    
    def test_set_encounter_deck_not_found(self, lobby_interactor):
        """Test setting encounter deck that doesn't exist"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        with pytest.raises(ValueError, match='not found'):
            lobby_interactor.set_encounter_deck(lobby.id, 'Alice', 'nonexistent')
    
    # ========================================================================
    # TOGGLE READY TESTS
    # ========================================================================
    
    def test_toggle_ready_without_deck_fails(self, lobby_interactor):
        """Test that player cannot ready without choosing deck"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        with pytest.raises(ValueError, match='Choose a deck'):
            lobby_interactor.toggle_ready(lobby.id, 'Alice')
    
    def test_toggle_ready_with_deck(self, lobby_interactor, sample_deck):
        """Test toggling ready after choosing deck"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        
        updated = lobby_interactor.toggle_ready(lobby.id, 'Alice')
        
        alice = updated.get_lobby_player('Alice')
        assert alice.is_ready is True
    
    def test_toggle_ready_twice(self, lobby_interactor, sample_deck):
        """Test toggling ready status on and off"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        
        # Ready up
        updated = lobby_interactor.toggle_ready(lobby.id, 'Alice')
        alice = updated.get_lobby_player('Alice')
        assert alice.is_ready is True
        
        # Un-ready
        updated = lobby_interactor.toggle_ready(updated.id, 'Alice')
        alice = updated.get_lobby_player('Alice')
        assert alice.is_ready is False
    
    # ========================================================================
    # START GAME TESTS
    # ========================================================================
    
    def test_start_game_success(self, lobby_interactor, sample_deck, encounter_deck):
        """Test successfully starting a game"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        lobby_interactor.set_encounter_deck(lobby.id, 'Alice', encounter_deck.id)
        lobby_interactor.toggle_ready(lobby.id, 'Alice')
        
        started = lobby_interactor.start_game(lobby.id, 'Alice')
        
        assert started.status == GamePhase.IN_PROGRESS
        assert started.state is not None
        assert len(started.state.players) == 1
        assert started.state.players[0].player_name == 'Alice'
        assert len(started.state.players[0].deck) > 0
        assert len(started.deck_ids) == 1
        assert started.deck_ids[0] == sample_deck.id
    
    def test_start_game_multiplayer(self, lobby_interactor, sample_deck, encounter_deck, test_db):
        """Test starting game with multiple players"""
        # Create second deck
        deck_repo = MongoDeckRepository(test_db)
        deck2 = Deck(
            id=None,
            name='Bob Deck',
            cards=(DeckCard(code='01002a', quantity=5),)
        )
        deck2 = deck_repo.save(deck2)
        
        # Setup lobby
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        lobby_interactor.choose_deck(lobby.id, 'Bob', deck2.id)
        lobby_interactor.set_encounter_deck(lobby.id, 'Alice', encounter_deck.id)
        
        lobby_interactor.toggle_ready(lobby.id, 'Alice')
        lobby_interactor.toggle_ready(lobby.id, 'Bob')
        
        started = lobby_interactor.start_game(lobby.id, 'Alice')
        
        assert started.status == GamePhase.IN_PROGRESS
        assert len(started.state.players) == 2
        
        player_names = [p.player_name for p in started.state.players]
        assert 'Alice' in player_names
        assert 'Bob' in player_names
        
        assert len(started.deck_ids) == 2
    
    def test_start_game_non_host(self, lobby_interactor, sample_deck, encounter_deck):
        """Test that only host can start game"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        lobby_interactor.set_encounter_deck(lobby.id, 'Alice', encounter_deck.id)
        lobby_interactor.toggle_ready(lobby.id, 'Alice')
        
        with pytest.raises(ValueError, match='Only host'):
            lobby_interactor.start_game(lobby.id, 'Bob')
    
    def test_start_game_no_encounter_deck(self, lobby_interactor, sample_deck):
        """Test that game cannot start without encounter deck"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        lobby_interactor.toggle_ready(lobby.id, 'Alice')
        
        with pytest.raises(ValueError, match='no encounter deck'):
            lobby_interactor.start_game(lobby.id, 'Alice')
    
    def test_start_game_player_not_ready(self, lobby_interactor, sample_deck, encounter_deck):
        """Test that game cannot start if players not ready"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        lobby_interactor.choose_deck(lobby.id, 'Bob', sample_deck.id)
        lobby_interactor.set_encounter_deck(lobby.id, 'Alice', encounter_deck.id)
        
        lobby_interactor.toggle_ready(lobby.id, 'Alice')
        # Bob not ready
        
        with pytest.raises(ValueError, match='not all players ready'):
            lobby_interactor.start_game(lobby.id, 'Alice')
    
    def test_start_game_decks_shuffled(self, lobby_interactor, sample_deck, encounter_deck):
        """Test that decks are shuffled when game starts"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.choose_deck(lobby.id, 'Alice', sample_deck.id)
        lobby_interactor.set_encounter_deck(lobby.id, 'Alice', encounter_deck.id)
        lobby_interactor.toggle_ready(lobby.id, 'Alice')
        
        started = lobby_interactor.start_game(lobby.id, 'Alice')
        
        # Verify deck has expected number of cards (not testing exact order since shuffled)
        alice = started.state.players[0]
        expected_count = sample_deck.total_cards()
        assert len(alice.deck) == expected_count
    
    # ========================================================================
    # DELETE LOBBY TESTS
    # ========================================================================
    
    def test_delete_lobby_by_host(self, lobby_interactor):
        """Test deleting lobby by host"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        
        success = lobby_interactor.delete_lobby(lobby.id, 'Alice')
        
        assert success is True
        assert lobby_interactor.get_lobby(lobby.id) is None
    
    def test_delete_lobby_by_non_host(self, lobby_interactor):
        """Test that non-host cannot delete lobby"""
        lobby = lobby_interactor.create_lobby('My Game', 'Alice')
        lobby_interactor.join_lobby(lobby.id, 'Bob')
        
        with pytest.raises(ValueError, match='Only host'):
            lobby_interactor.delete_lobby(lobby.id, 'Bob')
    
    def test_delete_lobby_not_found(self, lobby_interactor):
        """Test deleting non-existent lobby"""
        success = lobby_interactor.delete_lobby('nonexistent', 'Alice')
        assert success is False
