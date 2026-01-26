"""Tests for domain entities"""

import pytest
import datetime
from src.entities import Card, Deck, DeckCard, Game, GamePhase, CardInPlay, Position, Player, PlayZone


class TestCard:
    """Test Card entity"""
    
    def test_create_card_minimal(self):
        """Test creating card with minimal fields"""
        card = Card(code='01001a', name='Spider-Man')
        assert card.code == '01001a'
        assert card.name == 'Spider-Man'
        assert card.text is None
    
    def test_create_card_with_text(self):
        """Test creating card with text"""
        card = Card(
            code='01001a',
            name='Spider-Man',
            text='Friendly neighborhood hero'
        )
        assert card.text == 'Friendly neighborhood hero'
    
    def test_card_immutability(self):
        """Test that cards are immutable"""
        card = Card(code='01001a', name='Spider-Man')
        with pytest.raises(Exception):  # FrozenInstanceError
            card.name = 'Iron Man'
    
    def test_card_validation_empty_code(self):
        """Test validation fails on empty code"""
        with pytest.raises(ValueError):
            Card(code='', name='Spider-Man')
    
    def test_card_validation_empty_name(self):
        """Test validation fails on empty name"""
        with pytest.raises(ValueError):
            Card(code='01001a', name='')


class TestDeck:
    """Test Deck entity"""
    
    def test_create_deck(self):
        """Test creating a deck"""
        deck = Deck(
            id='deck123',
            name='Justice Spider-Man',
            cards=[
                DeckCard(code='01001a', name='1', quantity=1),
                DeckCard(code='01002a', name='2', quantity=3),
            ]
        )
        assert deck.name == 'Justice Spider-Man'
        assert len(deck.cards) == 2
    
    def test_total_cards(self):
        """Test calculating total cards in deck"""
        deck = Deck(
            id='deck123',
            name='Test Deck',
            cards=[
                DeckCard(code='01001a', name='1', quantity=1),
                DeckCard(code='01002a', name='2', quantity=3),
                DeckCard(code='01003a', name='3', quantity=2),
            ]
        )
        assert deck.total_cards() == 6
    
    def test_get_card_codes(self):
        """Test getting expanded card codes"""
        deck = Deck(
            id='deck123',
            name='Test Deck',
            cards=[
                DeckCard(code='01001a', name='1', quantity=2),
                DeckCard(code='01002a', name='2', quantity=1),
            ]
        )
        codes = deck.get_card_codes()
        assert len(codes) == 3
        assert codes.count('01001a') == 2
        assert codes.count('01002a') == 1
    
    def test_deck_card_validation_min_quantity(self):
        """Test deck card quantity validation"""
        with pytest.raises(ValueError):
            DeckCard(code='01001a', name='test', quantity=0)


class TestGame:
    """Test Game entity"""
    
    def test_create_game_lobby(self):
        """Test creating a game in lobby phase"""
        game = Game(
            name='Test Game',
            host='Alice',
            phase=GamePhase.LOBBY,
            players=(),
            play_zone=None
        )
        
        assert game.name == 'Test Game'
        assert game.host == 'Alice'
        assert game.phase == GamePhase.LOBBY
        assert len(game.players) == 0
    
    def test_add_player_to_lobby(self):
        """Test adding a player to game lobby"""
        game = Game(
            name='Test Game',
            host='Alice',
            phase=GamePhase.LOBBY,
            players=(),
            play_zone=None
        )
        
        player = Player(name='Alice', is_host=True)
        updated_game = game.add_player(player)
        
        assert len(updated_game.players) == 1
        assert updated_game.players[0].name == 'Alice'
    
    def test_player_ready_toggle(self):
        """Test toggling player ready state"""
        player = Player(
            name='Alice',
            is_host=True,
            is_ready=False,
            deck=None
        )
        
        ready_player = player.toggle_ready()
        assert ready_player.is_ready is True
        assert player.is_ready is False  # Original unchanged


class TestCardInPlay:
    """Test CardInPlay entity"""
    
    def test_create_card_in_play(self):
        """Test creating card in play"""
        card = Card(code='01001a', name='Spider-Man')
        position = Position(x=100, y=200)
        
        card_in_play = CardInPlay(
            card=card,
            position=position
        )
        
        assert card_in_play.code == '01001a'
        assert card_in_play.name == 'Spider-Man'
        assert card_in_play.position.x == 100
    
    def test_card_in_play_rotation(self):
        """Test card rotation"""
        card = Card(code='01001a', name='Spider-Man')
        position = Position(x=100, y=200)
        
        card_in_play = CardInPlay(card=card, position=position)
        rotated = card_in_play.rotate(90)
        
        assert rotated.position.rotation == 90
        assert card_in_play.position.rotation == 0  # Original unchanged
    
    def test_card_in_play_add_counter(self):
        """Test adding counters to card"""
        card = Card(code='01001a', name='Spider-Man')
        position = Position(x=100, y=200)
        
        card_in_play = CardInPlay(card=card, position=position)
        with_damage = card_in_play.add_counter('damage', 3)
        
        assert with_damage.counters.get('damage') == 3
        
        more_damage = with_damage.add_counter('damage', 2)
        assert more_damage.counters.get('damage') == 5


class TestPlayZone:
    """Test PlayZone entity"""
    
    def test_create_play_zone(self):
        """Test creating an empty play zone"""
        zone = PlayZone()
        
        assert len(zone.decks_in_play) == 0
        assert len(zone.cards_in_play) == 0
        assert len(zone.dials) == 0
    
    def test_add_card_to_play_zone(self):
        """Test adding card to play zone"""
        zone = PlayZone()
        
        card = Card(code='01001a', name='Spider-Man')
        position = Position(x=100, y=200)
        card_in_play = CardInPlay(card=card, position=position)
        
        updated_zone = zone.add_card(card_in_play)
        
        assert len(updated_zone.cards_in_play) == 1
        assert len(zone.cards_in_play) == 0  # Original unchanged
    
    def test_get_card_from_play_zone(self):
        """Test getting card from play zone"""
        zone = PlayZone()
        
        card = Card(code='01001a', name='Spider-Man')
        position = Position(x=100, y=200)
        card_in_play = CardInPlay(card=card, position=position)
        
        zone = zone.add_card(card_in_play)
        found = zone.get_card('01001a')
        
        assert found is not None
        assert found.code == '01001a'