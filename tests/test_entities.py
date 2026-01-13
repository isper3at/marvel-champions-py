"""Tests for domain entities"""

import pytest
from datetime import datetime
from src.entities import Card, Deck, DeckCard, Game, GameState, PlayerZones, CardInPlay, Position


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
            id=None,
            name='Justice Spider-Man',
            cards=(
                DeckCard(code='01001a', quantity=1),
                DeckCard(code='01002a', quantity=3),
            )
        )
        assert deck.name == 'Justice Spider-Man'
        assert len(deck.cards) == 2
    
    def test_total_cards(self):
        """Test calculating total cards in deck"""
        deck = Deck(
            id=None,
            name='Test Deck',
            cards=(
                DeckCard(code='01001a', quantity=1),
                DeckCard(code='01002a', quantity=3),
                DeckCard(code='01003a', quantity=2),
            )
        )
        assert deck.total_cards() == 6
    
    def test_get_card_codes(self):
        """Test getting expanded card codes"""
        deck = Deck(
            id=None,
            name='Test Deck',
            cards=(
                DeckCard(code='01001a', quantity=2),
                DeckCard(code='01002a', quantity=1),
            )
        )
        codes = deck.get_card_codes()
        assert len(codes) == 3
        assert codes.count('01001a') == 2
        assert codes.count('01002a') == 1
    
    def test_deck_card_validation_min_quantity(self):
        """Test deck card quantity validation"""
        with pytest.raises(ValueError):
            DeckCard(code='01001a', quantity=0)


class TestGame:
    """Test Game entity"""
    
    def test_create_game_single_player(self):
        """Test creating single player game"""
        state = GameState(
            players=(
                PlayerZones(
                    player_name='Alice',
                    deck=('01001a', '01002a', '01003a'),
                    hand=(),
                    discard=()
                ),
            ),
            play_area=()
        )
        
        game = Game(
            id=None,
            name='Solo Game',
            deck_ids=('deck_123',),
            state=state
        )
        
        assert game.name == 'Solo Game'
        assert len(game.state.players) == 1
        assert game.state.players[0].player_name == 'Alice'
    
    def test_create_game_multiplayer(self):
        """Test creating multiplayer game"""
        state = GameState(
            players=(
                PlayerZones(player_name='Alice', deck=('01001a',), hand=(), discard=()),
                PlayerZones(player_name='Bob', deck=('01010a',), hand=(), discard=()),
            ),
            play_area=()
        )
        
        game = Game(
            id=None,
            name='2 Player Game',
            deck_ids=('deck_alice', 'deck_bob'),
            state=state
        )
        
        assert len(game.state.players) == 2
    
    def test_draw_card(self):
        """Test drawing a card"""
        player = PlayerZones(
            player_name='Alice',
            deck=('01001a', '01002a', '01003a'),
            hand=(),
            discard=()
        )
        
        updated_player, drawn = player.draw_card()
        
        assert drawn == '01001a'
        assert len(updated_player.deck) == 2
        assert len(updated_player.hand) == 1
        assert updated_player.hand[0] == '01001a'
    
    def test_shuffle_discard_into_deck(self):
        """Test shuffling discard pile into deck"""
        player = PlayerZones(
            player_name='Alice',
            deck=('01001a',),
            hand=(),
            discard=('01002a', '01003a', '01004a')
        )
        
        shuffled = player.shuffle_discard_into_deck()
        
        assert len(shuffled.deck) == 4
        assert len(shuffled.discard) == 0
        assert '01001a' in shuffled.deck
        assert '01002a' in shuffled.deck
    
    def test_card_in_play_rotation(self):
        """Test card rotation (exhaust/ready)"""
        card = CardInPlay(
            code='01001a',
            position=Position(x=100, y=200),
            rotated=False
        )
        
        exhausted = card.with_rotated(True)
        assert exhausted.rotated is True
        assert card.rotated is False  # Original unchanged
    
    def test_card_in_play_counters(self):
        """Test adding counters to cards"""
        card = CardInPlay(
            code='01001a',
            position=Position(x=100, y=200)
        )
        
        with_damage = card.add_counter('damage', 3)
        assert with_damage.counters['damage'] == 3
        
        more_damage = with_damage.add_counter('damage', 2)
        assert more_damage.counters['damage'] == 5