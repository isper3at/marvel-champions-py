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
from src.interactors import LobbyInteractor
from src.repositories import MongoGameRepository, MongoDeckRepository


class TestLobbyLifecycle:
    """Test complete lobby lifecycle"""
    
    def test_create_lobby(self, test_db):
        """Test creating a new lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        assert lobby.id is not None
        assert lobby.name == "Test Game"
        assert lobby.status == GamePhase.LOBBY
        assert lobby.host == "Alice"
        assert len(lobby.players) == 1
        assert lobby.players[0].username == "Alice"
        assert lobby.players[0].is_host is True
        assert lobby.players[0].is_ready is False
    
    def test_join_lobby(self, test_db):
        """Test player joining lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        updated = interactor.join_lobby(lobby.id, "Bob")
        
        assert len(updated.lobby_players) == 2
        assert updated.get_lobby_player("Bob") is not None
        assert updated.get_lobby_player("Bob").is_host is False
    
    def test_join_lobby_duplicate(self, test_db):
        """Test player joining same lobby twice"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        with pytest.raises(ValueError, match="already in lobby"):
            interactor.join_lobby(lobby.id, "Alice")
    
    def test_leave_lobby(self, test_db):
        """Test player leaving lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        updated = interactor.leave_lobby(lobby.id, "Bob")
        
        assert updated is not None
        assert len(updated.lobby_players) == 1
        assert updated.get_lobby_player("Bob") is None
    
    def test_leave_lobby_host_deletes(self, test_db):
        """Test that host leaving deletes lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        result = interactor.leave_lobby(lobby.id, "Alice")
        
        assert result is None  # Lobby deleted
    
    def test_choose_deck(self, test_db):
        """Test player choosing deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        # Create a deck first
        deck = Deck(
            id=None,
            name="Test Deck",
            cards=(DeckCard(code="01001a", quantity=1),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        updated = interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        
        player = updated.get_lobby_player("Alice")
        assert player.deck_id == saved_deck.id
    
    def test_choose_deck_not_host(self, test_db):
        """Test non-host can choose deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name="Test Deck",
            cards=(DeckCard(code="01001a", quantity=1),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        updated = interactor.choose_deck(lobby.id, "Bob", saved_deck.id)
        
        player = updated.get_lobby_player("Bob")
        assert player.deck_id == saved_deck.id
    
    def test_choose_deck_nonexistent(self, test_db):
        """Test choosing non-existent deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        with pytest.raises(ValueError, match="Deck not found"):
            interactor.choose_deck(lobby.id, "Alice", "nonexistent")
    
    def test_set_encounter_deck_host_only(self, test_db):
        """Test only host can set encounter deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name="Encounter Deck",
            cards=(DeckCard(code="enc001", quantity=1),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        # Host can set
        updated = interactor.set_encounter_deck(lobby.id, "Alice", saved_deck.id)
        assert updated.encounter_deck_id == saved_deck.id
        
        # Non-host cannot set
        with pytest.raises(ValueError, match="Only host"):
            interactor.set_encounter_deck(lobby.id, "Bob", saved_deck.id)
    
    def test_toggle_ready(self, test_db):
        """Test toggling ready status"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name="Test Deck",
            cards=(DeckCard(code="01001a", quantity=1),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        
        # Toggle ready
        updated = interactor.toggle_ready(lobby.id, "Alice")
        assert updated.get_lobby_player("Alice").is_ready is True
        
        # Toggle back
        updated = interactor.toggle_ready(updated.id, "Alice")
        assert updated.get_lobby_player("Alice").is_ready is False
    
    def test_toggle_ready_without_deck(self, test_db):
        """Test cannot ready without deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        with pytest.raises(ValueError, match="Choose a deck"):
            interactor.toggle_ready(lobby.id, "Alice")
    
    def test_start_game_success(self, test_db):
        """Test starting game when all ready"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        # Create decks
        deck1 = Deck(
            id=None,
            name="Alice Deck",
            cards=(
                DeckCard(code="01001a", quantity=3),
                DeckCard(code="01002a", quantity=2),
            )
        )
        deck2 = Deck(
            id=None,
            name="Bob Deck",
            cards=(DeckCard(code="01010a", quantity=5),)
        )
        encounter_deck = Deck(
            id=None,
            name="Encounter",
            cards=(DeckCard(code="enc001", quantity=10),)
        )
        
        saved_deck1 = deck_repo.save(deck1)
        saved_deck2 = deck_repo.save(deck2)
        saved_encounter = deck_repo.save(encounter_deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        # Create lobby
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        # Choose decks
        interactor.choose_deck(lobby.id, "Alice", saved_deck1.id)
        interactor.choose_deck(lobby.id, "Bob", saved_deck2.id)
        interactor.set_encounter_deck(lobby.id, "Alice", saved_encounter.id)
        
        # Ready up
        interactor.toggle_ready(lobby.id, "Alice")
        lobby = interactor.toggle_ready(lobby.id, "Bob")
        
        # Start game
        game = interactor.start_game(lobby.id, "Alice")
        
        assert game.status == GamePhase.IN_PROGRESS
        assert game.state is not None
        assert len(game.state.players) == 2
        
        # Check Alice's deck
        alice = game.state.get_player("Alice")
        assert alice is not None
        assert len(alice.deck) == 5  # 3 + 2 cards
        assert len(alice.hand) == 0
        
        # Check Bob's deck
        bob = game.state.get_player("Bob")
        assert bob is not None
        assert len(bob.deck) == 5
    
    def test_start_game_not_host(self, test_db):
        """Test non-host cannot start game"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name="Test Deck",
            cards=(DeckCard(code="01001a", quantity=1),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        interactor.choose_deck(lobby.id, "Bob", saved_deck.id)
        interactor.toggle_ready(lobby.id, "Alice")
        interactor.toggle_ready(lobby.id, "Bob")
        
        with pytest.raises(ValueError, match="Only host"):
            interactor.start_game(lobby.id, "Bob")
    
    def test_start_game_not_all_ready(self, test_db):
        """Test cannot start when not all ready"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name="Test Deck",
            cards=(DeckCard(code="01001a", quantity=1),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        interactor.choose_deck(lobby.id, "Bob", saved_deck.id)
        
        # Only Alice ready
        interactor.toggle_ready(lobby.id, "Alice")
        
        with pytest.raises(ValueError, match="not all players ready"):
            interactor.start_game(lobby.id, "Alice")
    
    def test_start_game_no_encounter_deck(self, test_db):
        """Test cannot start without encounter deck"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name="Test Deck",
            cards=(DeckCard(code="01001a", quantity=1),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        interactor.toggle_ready(lobby.id, "Alice")
        
        with pytest.raises(ValueError, match="no encounter deck"):
            interactor.start_game(lobby.id, "Alice")
    
    def test_list_lobbies(self, test_db):
        """Test listing active lobbies"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        # Create several lobbies
        lobby1 = interactor.create_lobby("Game 1", "Alice")
        lobby2 = interactor.create_lobby("Game 2", "Bob")
        
        lobbies = interactor.list_lobbies()
        
        assert len(lobbies) >= 2
        lobby_ids = [l.id for l in lobbies]
        assert lobby1.id in lobby_ids
        assert lobby2.id in lobby_ids
    
    def test_get_lobby(self, test_db):
        """Test getting specific lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        retrieved = interactor.get_lobby(lobby.id)
        
        assert retrieved is not None
        assert retrieved.id == lobby.id
        assert retrieved.name == "Test Game"
    
    def test_delete_lobby(self, test_db):
        """Test deleting lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        success = interactor.delete_lobby(lobby.id, "Alice")
        
        assert success is True
        assert interactor.get_lobby(lobby.id) is None
    
    def test_delete_lobby_not_host(self, test_db):
        """Test non-host cannot delete lobby"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        interactor.join_lobby(lobby.id, "Bob")
        
        with pytest.raises(ValueError, match="Only host"):
            interactor.delete_lobby(lobby.id, "Bob")


class TestLobbyEntityMethods:
    """Test LobbyPlayer and Game entity methods"""
    
    def test_player_with_deck(self):
        """Test Player.with_deck()"""
        player = Player(username="Alice", is_host=True)
        
        with_deck = player.with_deck("deck123")
        
        assert with_deck.deck_id == "deck123"
        assert with_deck.username == "Alice"
        assert with_deck.is_host is True
        assert player.deck_id is None  # Original unchanged
    
    def test_player_toggle_ready(self):
        """Test Player.toggle_ready()"""
        player = Player(
            username="Alice",
            deck_id="deck123",
            is_ready=False
        )
        
        ready = player.toggle_ready()
        assert ready.is_ready is True
        
        not_ready = ready.toggle_ready()
        assert not_ready.is_ready is False
    
    def test_player_is_ready_to_start(self):
        """Test Player.is_ready_to_start()"""
        player = Player(username="Alice")
        assert player.is_ready_to_start() is False
        
        with_deck = player.with_deck("deck123")
        assert with_deck.is_ready_to_start() is False
        
        ready = with_deck.toggle_ready()
        assert ready.is_ready_to_start() is True
    
    def test_game_can_start(self, test_db):
        """Test Game.can_start()"""
        game_repo = MongoGameRepository(test_db)
        deck_repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name="Test Deck",
            cards=(DeckCard(code="01001a", quantity=1),)
        )
        saved_deck = deck_repo.save(deck)
        
        interactor = LobbyInteractor(game_repo, deck_repo)
        
        lobby = interactor.create_lobby("Test Game", "Alice")
        
        # Cannot start - no deck, not ready, no encounter
        assert lobby.can_start() is False
        
        # Choose deck
        lobby = interactor.choose_deck(lobby.id, "Alice", saved_deck.id)
        assert lobby.can_start() is False
        
        # Ready up
        lobby = interactor.toggle_ready(lobby.id, "Alice")
        assert lobby.can_start() is False
        
        # Set encounter
        lobby = interactor.set_encounter_deck(lobby.id, "Alice", saved_deck.id)
        assert lobby.can_start() is True
