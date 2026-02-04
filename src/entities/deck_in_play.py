from dataclasses import dataclass
from typing import Tuple, Optional
import random
from .deck import Deck
from .position import Position
from .card_in_play import CardInPlay

@dataclass(frozen=True)
class DeckInPlay:
    deck: Deck  # The deck being played
    deck_position: Position  # Position of the draw pile on the play field
    draw_pile: list[CardInPlay]  # Cards currently in play from this deck
    
    @staticmethod
    def from_deck(deck: Deck, pos: Position, shuffle: bool = True) -> 'DeckInPlay':
        play_cards = list[CardInPlay]()
        for c in deck.cards:
            play_cards.append(CardInPlay.from_card(card=c, position=pos.flip()))

        if shuffle:
            random.shuffle(play_cards)
            
        return DeckInPlay(
            deck=deck,
            draw_pile=play_cards,
            deck_position=pos)

    def draw_card(self, count: int = 1) -> tuple['DeckInPlay', Optional[CardInPlay]]:
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
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=new_draw_pile,
            deck_position=self.deck_position
        ), drawn[0] if drawn else None
        
    def shuffle(self) -> 'DeckInPlay':
        """
        Shuffle the draw pile
        
        Returns:
            New DeckInPlay state with shuffled draw pile
        """
        random.shuffle(self.draw_pile)
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=self.draw_pile,
            deck_position=self.deck_position
        )
        
    def shuffle_cards_into_draw(self, cards:list[CardInPlay]) -> 'DeckInPlay':
        """
        Shuffle discard pile back into draw pile
        
        Returns:
            New DeckInPlay state with discard shuffled into draw pile
        """
        combined = self.draw_pile + cards
        random.shuffle(combined)
        
        return DeckInPlay(
            deck=self.deck,
            draw_pile=combined,
            deck_position=self.deck_position
        )
        
    def get_and_remove_card(self, card_id: str, shuffle: bool = False) -> tuple['DeckInPlay', Optional[CardInPlay]]:
        """
        Add a specific card code to hand (e.g., for effects that add cards)
        
        Args:
            card_code: Card code to add to hand
            
        Returns:
            New DeckInPlay state with card added to hand
        """

        card_to_remove = None
        new_draw_pile = []
        for card in self.draw_pile:
            if card.card_id == card_id and card_to_remove is None:
                card_to_remove = card
            else:
                new_draw_pile.append(card)


        new_deck_in_play = DeckInPlay(
            deck=self.deck,
            draw_pile=new_draw_pile,
            deck_position=self.deck_position
        )
        if shuffle:
            new_deck_in_play = new_deck_in_play.shuffle()

        return new_deck_in_play, card_to_remove
        
    def add_card_to_deck(self, card_to_add: CardInPlay, shuffle:bool = False) -> 'DeckInPlay':
        """
        Add a specific card code to the deck (e.g., for effects that add cards)
        
        Args:
            card_to_add: The CardInPlay to add to the deck.
            shuffle: whether or not to shuffle the deck after adding. (default = False)
            
        Returns:
            New DeckInPlay state with card added to deck's card list
        """
        
        new_draw_pile = self.draw_pile + [card_to_add]

        if shuffle:
            random.shuffle(new_draw_pile)

        return DeckInPlay(
            deck=self.deck,
            draw_pile=new_draw_pile,
            deck_position=self.deck_position
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
            draw_pile=self.draw_pile,
            deck_position=new_position,
        )