"""Tests for repository implementations"""

import pytest
import uuid
from src.entities.deck_in_play import DeckInPlay
from src.entities.encounter_deck import EncounterDeck
from src.entities.encounter_deck_in_play import EncounterDeckInPlay
from src.repositories import MongoCardRepository, MongoDeckRepository, MongoGameRepository
from src.entities import Card, Deck, DeckCard, Game, GamePhase, CardInPlay, Position, Player, PlayZone


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
            id='deck123',
            name='Justice Spider-Man',
            cards=[
                Card(code='01001a', name='Spider-Man', text="1"),
                Card(code='01002a', name='Iron Man', text="3"),
            ]
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
            id='deck123',
            name='Original Name',
            cards=[Card(code='01001a', name='Spider-Man', text="1")]
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
            id='deck123',
            name='Test Deck',
            cards=[Card(code='01001a', name='Spider-Man', text="1")]
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
        
        repo.save(Deck(id='deck1', name='Deck 1', cards=[]))
        repo.save(Deck(id='deck2', name='Deck 2', cards=[]))
        
        all_decks = repo.find_all()
        assert len(all_decks) >= 2


class TestMongoGameRepository:
    """Test MongoGameRepository"""
    
    def test_save_and_find_game(self, test_db):
        """Test saving and finding a game"""
        repo = MongoGameRepository(test_db)
        
        player = Player(name='Alice', is_host=True)
        
        game = Game(
            name='Test Game',
            host='Alice',
            phase=GamePhase.LOBBY,
            players=(player,),
            play_zone=None
        )
        
        assert game.id is not None
        
        saved = repo.save(game)
        assert saved.id is not None
        
        found = repo.find_by_id(saved.id)
        assert found is not None
        assert found.name == 'Test Game'
        assert len(found.players) == 1
    
    def test_save_game_in_progress(self, test_db):
        """Test saving game in progress with cards in play"""
        repo = MongoGameRepository(test_db)
        
        player = Player(name='Alice', is_host=True)
        zone = PlayZone()
        
        card = Card(code='01001a', name='Spider-Man')
        position = Position(x=100, y=200)
        card_in_play = CardInPlay(card=card, position=position)
        encounter_deck_in_play = EncounterDeckInPlay(
            encounterDeck=EncounterDeck(id='encounter1', name='Encounter Deck', cards=[]),
            draw_position=Position(x=0, y=0),
            discard_position=Position(x=0, y=0),
            draw_pile=(),
            discard_pile=()
        )
        alice_deck_in_play = DeckInPlay(
            deck=Deck(id='deck123', name='Alice Deck', cards=[]),
            draw_position=Position(x=50, y=50),
            discard_position=Position(x=60, y=60),
            draw_pile=(),
            discard_pile=(),
            hand=()
        )
        zone = zone.set_encounter_deck(encounter_deck_in_play)
        zone = zone.add_deck(alice_deck_in_play)
        zone = zone.add_card(card_in_play)
        
        game = Game(
            name='Game with Cards',
            host='Alice',
            phase=GamePhase.IN_PROGRESS,
            players=(player,),
            play_zone=zone
        )
        
        saved = repo.save(game)
        
        assert len(saved.play_zone.cards_in_play) == 1
        card = saved.play_zone.cards_in_play[0]
        assert card.code == '01001a'
    
    def test_save_multiplayer_game(self, test_db):
        """Test saving multiplayer game"""
        repo = MongoGameRepository(test_db)
        
        alice = Player(name='Alice', is_host=True)
        bob = Player(name='Bob', is_host=False)
        
        game = Game(
            name='2 Player Game',
            host='Alice',
            phase=GamePhase.LOBBY,
            players=(alice, bob),
            play_zone=None
        )
        
        saved = repo.save(game)
        found = repo.find_by_id(saved.id)
        
        assert len(found.players) == 2
        assert found.players[0].name == 'Alice'
        assert found.players[1].name == 'Bob'
    
    def test_find_recent_games(self, test_db):
        """Test finding recent games"""
        repo = MongoGameRepository(test_db)
        
        for i in range(5):
            player = Player(name=f'Player {i}')
            game = Game(
                name=f'Game {i}',
                host=f'Player {i}',
                phase=GamePhase.LOBBY,
                players=(player,),
                play_zone=None
            )
            repo.save(game)
        
        recent = repo.find_recent(limit=3)
        assert len(recent) == 3