from dataclasses import dataclass
from typing import Tuple, Optional
import random
from .deck import Deck
from .position import Position


@dataclass(frozen=True)
class DeckInPlay:
    """
    TODO doc
    """
    deck: Deck  # The deck being played
    draw_position: Position  # Position of the draw pile on the play field
    discard_position: Position  # Position of the discard pile on the play field
    draw_pile: Tuple[str, ...]  # Tuple of card codes in draw pile
    discard_pile: Tuple[str, ...]  # Tuple of card codes in discard pile
    hand: Tuple[str, ...]  # Tuple of card codes in hand
    
    @classmethod
    def from_deck(cls, deck: Deck, shuffle: bool = True) -> 'DeckInPlay':
        draw_pile = tuple(deck.get_card_codes())
        if shuffle:
            draw_pile = random.shuffle(list(draw_pile))
            
        return cls(
            deck=deck,
            draw_pile=draw_pile,
            discard_pile=(),
            hand=()
        )

    def draw_card(self, count: int = 1) -> tuple['DeckInPlay', Optional[str]]:
        """
        Draw a card from the draw pile into hand
        
        Args:
            count: Number of cards to draw (default 1)
        
        Returns:
            Tuple of (new DeckInPlay state, drawn card code or None if draw pile empty
        """
        if count <= 0:
            return self, None
        if not self.draw_pile:
            return self, None
        
        drawn = self.draw_pile[:count]
        new_draw_pile = self.draw_pile[count:]
        new_hand = self.hand + drawn
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=new_draw_pile,
            discard_pile=self.discard_pile,
            hand=new_hand
        ), drawn[0] if drawn else None
        
    def discard_from_hand(self, card_code: str) -> 'DeckInPlay':
        """
        Discard a card from hand to discard pile
        
        Args:
            card_code: Card code to discard
        Returns:
            New DeckInPlay state with card discarded
        """
        if card_code not in self.hand:
            return self  # No change if card not in hand
        
        hand_list = list(self.hand)
        hand_list.remove(card_code)
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=self.draw_pile,
            discard_pile=self.discard_pile + (card_code,),
            hand=tuple(hand_list)
        )
        
    def discard_from_play(self, card_code: str) -> 'DeckInPlay':
        """
        Discard a card from play area to discard pile
        
        Args:
            card_code: Card code to discard
        Returns:
            New DeckInPlay state with card discarded
        """       
        return DeckInPlay(
            deck=self.deck,
            draw_pile=self.draw_pile,
            discard_pile=self.discard_pile + (card_code,),
            hand=self.hand
        )
        
    def play_from_hand(self, card_code: str) -> 'DeckInPlay':
        """
        Play a card from hand (removing it from hand)
        
        Args:
            card_code: Card code to play
        Returns:
            New DeckInPlay state with card removed from hand
        """
        if card_code not in self.hand:
            return self  # No change if card not in hand
        
        hand_list = list(self.hand)
        hand_list.remove(card_code)
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=self.draw_pile,
            discard_pile=self.discard_pile,
            hand=tuple(hand_list)
        )
        
    def shuffle(self) -> 'DeckInPlay':
        """
        Shuffle the draw pile
        
        Returns:
            New DeckInPlay state with shuffled draw pile
        """
        shuffled_draw = list(self.draw_pile)
        random.shuffle(shuffled_draw)
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=tuple(shuffled_draw),
            discard_pile=self.discard_pile,
            hand=self.hand
        )
        
    def shuffle_discard_into_draw(self) -> 'DeckInPlay':
        """
        Shuffle discard pile back into draw pile
        
        Returns:
            New DeckInPlay state with discard shuffled into draw pile
        """
        combined = list(self.draw_pile) + list(self.discard_pile)
        random.shuffle(combined)
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=tuple(combined),
            discard_pile=(),
            hand=self.hand
        )
        
    def add_card_to_hand(self, card_code: str) -> 'DeckInPlay':
        """
        Add a specific card code to hand (e.g., for effects that add cards)
        
        Args:
            card_code: Card code to add to hand
            
        Returns:
            New DeckInPlay state with card added to hand
        """
        return DeckInPlay(
            deck=self.deck,
            draw_pile=self.draw_pile,
            discard_pile=self.discard_pile,
            hand=self.hand + (card_code,)
        )
        
    def add_card_to_discard(self, card_code: str) -> 'DeckInPlay':
        """
        Add a specific card code to discard pile (e.g., for effects that add cards)
        
        Args:
            card_code: Card code to add to discard pile
            
        Returns:
            New DeckInPlay state with card added to discard pile
        """
        return DeckInPlay(
            deck=self.deck,
            draw_pile=self.draw_pile,
            discard_pile=self.discard_pile + (card_code,),
            hand=self.hand
        )
        
    def add_card_to_deck(self, card_code: str) -> 'DeckInPlay':
        """
        Add a specific card code to the deck (e.g., for effects that add cards)
        
        Args:
            card_code: Card code to add to deck
            
        Returns:
            New DeckInPlay state with card added to deck's card list
        """
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=self.draw_pile + (card_code,),
            discard_pile=self.discard_pile,
            hand=self.hand
        )
        
    def move_draw_pile(self, new_position: Position) -> 'DeckInPlay':
        """
        Move the draw pile to a new position on the play field
        
        Args:
            new_position: New Position for the draw pile
            
        Returns:
            New DeckInPlay state with updated draw pile position
        """
        return DeckInPlay(
            deck=self.deck,
            draw_position=new_position,
            discard_position=self.discard_position,
            draw_pile=self.draw_pile,
            discard_pile=self.discard_pile,
            hand=self.hand
        )
        
    def move_discard_pile(self, new_position: Position) -> 'DeckInPlay':
        """
        Move the discard pile to a new position on the play field

        Args:
            new_position: New Position for the discard pile

        Returns:
            New DeckInPlay state with updated discard pile position
        """
        return DeckInPlay(
            deck=self.deck,
            draw_position=self.draw_position,
            discard_position=new_position,
            draw_pile=self.draw_pile,
            discard_pile=self.discard_pile,
            hand=self.hand
        )   