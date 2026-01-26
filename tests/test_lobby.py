"""
Tests for lobby functionality.

Tests the full lobby lifecycle:
1. Create lobby
2. Players join
3. Choose decks
4. Ready up
5. Start game
"""

import pytest
from src.entities import Game, GamePhase, Player, Deck, DeckCard
from src.entities.card import Card
from src.entities.encounter_deck import EncounterDeck
from src.interactors import LobbyInteractor
from src.repositories import MongoGameRepository, MongoDeckRepository


class TestLobbyLifecycle:
    """Test complete lobby lifecycle"""
    
    def test_create_lobby(self, test_db, test_marvel_client):
        """Test creating a new lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        assert lobby.id is not None
        assert lobby.name == "Test Game"
        assert lobby.phase == GamePhase.LOBBY
        assert lobby.host == "Alice"
        assert len(lobby.players) == 1
        assert lobby.players[0].name == "Alice"
        assert lobby.players[0].is_host is True
        assert lobby.players[0].is_ready is False

    def test_join_lobby(self, test_db, test_marvel_client):
        """Test player joining lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        updated = interactor.join_lobby(lobby.id, "Bob")
        
        assert len(updated.players) == 2
        assert updated.players[1] is not None
        assert updated.players[1].name == "Bob"
        assert updated.players[1].is_host is False

    def test_join_lobby_duplicate(self, test_db, test_marvel_client):
        """Test player joining same lobby twice"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        with pytest.raises(ValueError, match="already in lobby"):
            interactor.join_lobby(lobby.id, "Alice")
    
    def test_leave_lobby(self, test_db, test_marvel_client):
        """Test player leaving lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        updated = interactor.leave_lobby(lobby.id, "Bob")
        
        assert updated is not None
        assert len(updated.players) == 1
    
    def test_leave_lobby_host_deletes(self, test_db, test_marvel_client):
        """Test that host leaving deletes lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        result = interactor.leave_lobby(lobby.id, "Alice")
        
        assert result is None  # Lobby deleted
    
    def test_choose_deck(self, test_db, test_marvel_client):
        """Test player choosing deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        # Create a deck first
        deck = Deck(
            id='test-deck-1',
            name="Test Deck",
            cards=(Card(code="01001a", name="Card 1", text="..."),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        updated = interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        
        player = updated.players[0]
        assert player.deck == saved_deck
    
    def test_choose_deck_not_host(self, test_db, test_marvel_client):
        """Test non-host can choose deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id='test-deck-2',
            name="Test Deck",
            cards=(Card(code="01001a", name="Card 1", text="..."),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        updated = interactor.choose_deck(lobby.id, "Bob", saved_deck.id)
        
        player = updated.players[1]
        assert player.deck == saved_deck
    
    def test_choose_deck_nonexistent(self, test_db, test_marvel_client):
        """Test choosing non-existent deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        with pytest.raises(ValueError, match="Deck not found"):
            interactor.choose_deck(lobby.id, "Alice", "nonexistent")
    
    def test_set_encounter_deck_host_only(self, test_db, test_marvel_client):
        """Test only host can set encounter deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id='test-deck-3',
            name="Encounter Deck",
            cards=(Card(code="enc001", name="Encounter Card", text="..."),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        game_lobby = interactor.create_lobby("Test Game", "Alice")
        game_lobby = interactor.join_lobby(game_lobby.id, "Bob")
        
        encounter_deck = EncounterDeck(
            id=saved_deck.id,
            name=saved_deck.name,
            cards=[],
            villian_cards=[],
            main_scheme_cards=[],
            scenario_cards=[],
            source_url="http://example.com"
            )
        
        # Host can set
        updated = interactor.set_encounter_deck(game_lobby.id, encounter_deck)
        assert updated.encounter_deck.id == updated.encounter_deck.id
    
    def test_toggle_ready(self, test_db, test_marvel_client):
        """Test toggling ready status"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id='test-deck-4',
            name="Test Deck",
            cards=(Card(code="01001a", name="Card 1", text="..."),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        
        # Toggle ready
        updated = interactor.toggle_ready(lobby.id, "Alice")
        assert updated.players[0].is_ready is True
        
        # Toggle back
        updated = interactor.toggle_ready(updated.id, "Alice")
        assert updated.players[0].is_ready is False
    
    def test_toggle_ready_without_deck(self, test_db, test_marvel_client):
        """Test cannot ready without deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        with pytest.raises(ValueError, match="Choose a deck"):
            interactor.toggle_ready(lobby.id, "Alice")
    
    def test_start_game_not_host(self, test_db, test_marvel_client):
        """Test non-host cannot start game"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id='test-deck-8',
            name="Test Deck",
            cards=(Card(code="01001a", name="Card 1", text="..."),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        interactor.choose_deck(lobby.id, "Bob", saved_deck.id)
        interactor.toggle_ready(lobby.id, "Alice")
        interactor.toggle_ready(lobby.id, "Bob")
        
        with pytest.raises(ValueError, match="Only host"):
            interactor.start_game(lobby.id, "Bob")
    
    def test_start_game_not_all_ready(self, test_db, test_marvel_client):
        """Test cannot start when not all ready"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id='test-deck-9',
            name="Test Deck",
            cards=(Card(code="01001a", name="Card 1", text="..."),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        interactor.choose_deck(lobby.id, "Bob", saved_deck.id)
        
        # Only Alice ready
        interactor.toggle_ready(lobby.id, "Alice")
        
        with pytest.raises(ValueError, match="not all players ready"):
            interactor.start_game(lobby.id, "Alice")
    
    def test_start_game_no_encounter_deck(self, test_db, test_marvel_client):
        """Test cannot start without encounter deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id='test-deck-10',
            name="Test Deck",
            cards=(Card(code="01001a", name="Card 1", text="..."),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        interactor.toggle_ready(lobby.id, "Alice")
        
        with pytest.raises(ValueError, match="no encounter deck"):
            interactor.start_game(lobby.id, "Alice")
    
    def test_list_lobbies(self, test_db, test_marvel_client):
        """Test listing active lobbies"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        # Create several lobbies
        lobby1 = interactor.create_lobby("Game 1", "Alice")
        lobby2 = interactor.create_lobby("Game 2", "Bob")
        
        lobbies = interactor.list_lobbies()
        
        assert len(lobbies) >= 2
        lobby_ids = [l.id for l in lobbies]
        assert lobby1.id in lobby_ids
        assert lobby2.id in lobby_ids
    
    def test_get_lobby(self, test_db, test_marvel_client):
        """Test getting specific lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        retrieved = interactor.get_lobby(lobby.id)
        
        assert retrieved is not None
        assert retrieved.id == lobby.id
        assert retrieved.name == "Test Game"

    def test_delete_lobby(self, test_db, test_marvel_client):
        """Test deleting lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        print(f"Lobby id: {lobby.id}")

        success = interactor.delete_lobby(lobby.id, "Alice")
        
        
        assert success is True
        assert interactor.get_lobby(lobby.id) is None

    def test_delete_lobby_not_host(self, test_db, test_marvel_client):
        """Test non-host cannot delete lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo, test_marvel_client)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        with pytest.raises(ValueError, match="Only host"):
            interactor.delete_lobby(lobby.id, "Bob")