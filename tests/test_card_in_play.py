from dataclasses import dataclass
from src.entities import CardInPlay, Card, Position
import pytest

class TestCardInPlay:
    def test_card_in_play_rotation(self):
        """Test card rotation (exhaust/ready)"""
        card = CardInPlay(
            card=Card(code='01001a', name='Test Card'),
            position=Position(x=100, y=200)
            counters={'damage': 3}
        )
        
        rotated = card.with_rotated(True)
        assert rotated.exhausted is True
        assert rotated.rotated is True