"""Tests for repository implementations"""

import pytest
from src.repositories import MongoCardRepository, MongoDeckRepository, MongoGameRepository
from src.entities import Card, Deck, DeckCard, Game, GameState, Position, CardInPlay, PlayZone


class TestMongoCardRepository:
    """Test MongoCardRepository"""
    
    def test_save_and_find_card(self, test_db):
        """Test saving and finding a card"""
        repo = MongoCardRepository(test_db)
        
        card = Card(code='01001a', name='Spider-Man', text='Hero')
        saved = repo.save(card)
        
        assert saved.code == '01001a'
        assert saved.name == 'Spider-Man'
        
        found = repo.find_by_code('01001a')
        assert found is not None
        assert found.code == '01001a'
    
    def test_find_nonexistent_card(self, test_db):
        """Test finding card that doesn't exist"""
        repo = MongoCardRepository(test_db)
        found = repo.find_by_code('nonexistent')
        assert found is None
    
    def test_save_multiple_cards(self, test_db):
        """Test bulk save"""
        repo = MongoCardRepository(test_db)
        
        cards = [
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Iron Man'),
            Card(code='01003a', name='Captain Marvel'),
        ]
        
        saved = repo.save_all(cards)
        assert len(saved) == 3
    
    def test_find_by_codes(self, test_db):
        """Test finding multiple cards"""
        repo = MongoCardRepository(test_db)
        
        repo.save_all([
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Iron Man'),
        ])
        
        found = repo.find_by_codes(['01001a', '01002a'])
        assert len(found) == 2
    
    def test_card_exists(self, test_db):
        """Test checking card existence"""
        repo = MongoCardRepository(test_db)
        
        repo.save(Card(code='01001a', name='Spider-Man'))
        
        assert repo.exists('01001a') is True
        assert repo.exists('nonexistent') is False
    
    def test_search_by_name(self, test_db):
        """Test searching cards by name"""
        repo = MongoCardRepository(test_db)
        
        repo.save_all([
            Card(code='01001a', name='Spider-Man'),
            Card(code='01002a', name='Spider-Woman'),
            Card(code='01003a', name='Iron Man'),
        ])
        
        results = repo.search_by_name('spider')
        assert len(results) == 2
        
        results = repo.search_by_name('iron')
        assert len(results) == 1


class TestMongoDeckRepository:
    """Test MongoDeckRepository"""
    
    def test_save_and_find_deck(self, test_db):
        """Test saving and finding a deck"""
        repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name='Justice Spider-Man',
            cards=(
                DeckCard(code='01001a', quantity=1),
                DeckCard(code='01002a', quantity=3),
            )
        )
        
        saved = repo.save(deck)
        
        assert saved.id is not None
        assert saved.name == 'Justice Spider-Man'
        
        found = repo.find_by_id(saved.id)
        assert found is not None
        assert len(found.cards) == 2
    
    def test_update_deck(self, test_db):
        """Test updating an existing deck"""
        repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name='Original Name',
            cards=(DeckCard(code='01001a', quantity=1),)
        )
        
        saved = repo.save(deck)
        deck_id = saved.id
        
        # Update
        updated = Deck(
            id=deck_id,
            name='Updated Name',
            cards=saved.cards
        )
        
        saved_updated = repo.save(updated)
        assert saved_updated.name == 'Updated Name'
        assert saved_updated.id == deck_id
    
    def test_delete_deck(self, test_db):
        """Test deleting a deck"""
        repo = MongoDeckRepository(test_db)
        
        deck = Deck(
            id=None,
            name='Test Deck',
            cards=(DeckCard(code='01001a', quantity=1),)
        )
        
        saved = repo.save(deck)
        deck_id = saved.id
        
        deleted = repo.delete(deck_id)
        assert deleted is True
        
        found = repo.find_by_id(deck_id)
        assert found is None
    
    def test_find_all_decks(self, test_db):
        """Test finding all decks"""
        repo = MongoDeckRepository(test_db)
        
        repo.save(Deck(id=None, name='Deck 1', cards=()))
        repo.save(Deck(id=None, name='Deck 2', cards=()))
        
        all_decks = repo.find_all()
        assert len(all_decks) >= 2


class TestMongoGameRepository:
    """Test MongoGameRepository"""
    
    def test_save_and_find_game(self, test_db):
        """Test saving and finding a game"""
        repo = MongoGameRepository(test_db)
        
        game = Game(
            id=None,
            name='Test Game',
            deck_ids=('deck1',),
            state=GameState(
                players=(
                    PlayZone(
                        player_name='Alice',
                        deck=('01001a', '01002a'),
                        hand=(),
                        discard=()
                    ),
                ),
                play_area=()
            )
        )
        
        saved = repo.save(game)
        assert saved.id is not None
        
        found = repo.find_by_id(saved.id)
        assert found is not None
        assert found.name == 'Test Game'
        assert len(found.state.players) == 1
    
    def test_save_game_with_cards_in_play(self, test_db):
        """Test saving game with cards on table"""
        repo = MongoGameRepository(test_db)
        
        game = Game(
            id=None,
            name='Game with Cards',
            deck_ids=('deck1',),
            state=GameState(
                players=(
                    PlayZone(player_name='Alice', deck=(), hand=(), discard=()),
                ),
                play_area=(
                    CardInPlay(
                        code='01001a',
                        position=Position(x=100, y=200),
                        rotated=True,
                        counters={'damage': 3}
                    ),
                )
            )
        )
        
        saved = repo.save(game)
        found = repo.find_by_id(saved.id)
        
        assert len(found.state.play_area) == 1
        card = found.state.play_area[0]
        assert card.code == '01001a'
        assert card.position.x == 100
        assert card.rotated is True
        assert card.counters['damage'] == 3
    
    def test_save_multiplayer_game(self, test_db):
        """Test saving multiplayer game"""
        repo = MongoGameRepository(test_db)
        
        game = Game(
            id=None,
            name='2 Player Game',
            deck_ids=('deck1', 'deck2'),
            state=GameState(
                players=(
                    PlayZone(player_name='Alice', deck=('01001a',), hand=(), discard=()),
                    PlayZone(player_name='Bob', deck=('01010a',), hand=(), discard=()),
                ),
                play_area=()
            )
        )
        
        saved = repo.save(game)
        found = repo.find_by_id(saved.id)
        
        assert len(found.state.players) == 2
        assert found.state.players[0].player_name == 'Alice'
        assert found.state.players[1].player_name == 'Bob'
    
    def test_find_recent_games(self, test_db):
        """Test finding recent games"""
        repo = MongoGameRepository(test_db)
        
        for i in range(5):
            game = Game(
                id=None,
                name=f'Game {i}',
                deck_ids=('deck1',),
                state=GameState(
                    players=(PlayZone(player_name='Alice', deck=(), hand=(), discard=()),),
                    play_area=()
                )
            )
            repo.save(game)
        
        recent = repo.find_recent(limit=3)
        assert len(recent) == 3