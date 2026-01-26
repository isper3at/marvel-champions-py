from dataclasses import dataclass
from src.entities import CardInPlay, Card, Position, FlipState
import pytest

class TestCardInPlay:
    def test_card_in_play_rotation(self):
        """Test card rotation (exhaust/ready)"""
        card = CardInPlay(
            card=Card(code='01001a', name='Test Card'),
            position=Position(x=100, y=200),
            counters={'damage': 3}
        )
        
        assert card.position.rotation == 0
        
        card = card.rotate(new_rotation=90)
        
        assert card.position.rotation == 90
        
    def test_card_in_play_flip(self):
        """Test card flip (face up/face down)"""
        card = CardInPlay(
            card=Card(code='01001a', name='Test Card'),
            position=Position(x=100, y=200, flip_state=FlipState.FACE_UP),
            counters={'damage': 3}
        )
        
        assert card.position.flip_state == FlipState.FACE_UP
        
        card = card.flip()
        
        assert card.position.flip_state == FlipState.FACE_DOWN
        
        