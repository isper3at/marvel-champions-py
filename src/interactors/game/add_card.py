from src.gateways.marvelcdb_client import MarvelCDBClient
from src.boundaries.game_repository import GameRepository
from src.boundaries.card_repository import CardRepository
from src.interactors.marvelcdb.get_card import GetCardInteractor
from src.entities import Card, Game
from typing import Optional
from uuid import UUID

class AddCard:
    """
    Adds a new card based on card code to a deck.
    This is intended to be used in game when a card from outside the current game needs to be added.
    """

    add_card: GetCardInteractor
    game_repository: GameRepository
    card_repository: CardRepository

    def __init__(self, game_repository: GameRepository, card_repository: CardRepository, add_card: GetCardInteractor):
        self.game_repository = game_repository
        self.card_repository = card_repository
        self.add_card = add_card
        pass

    def add_to_deck(self, game_id: UUID, deck_id: str, card_code: str) -> bool:
        """
        Add a card by its code.

        Args:
            card_code: The unique code of the card to add.

        Returns:
            True if the card was added successfully, False otherwise.
        """

        card: Optional[Card] = self.card_repository.find_by_code(card_code)
        if card is None:
            #get card from marvelcdb and add it to card repository
            card = self.add_card.get(card_code, True)

        game: Optional[Game] = self.game_repository.find_by_id(game_id)

        if game is None or card is None:
            return False
        
        if game.encounter_deck is not None and deck_id == game.encounter_deck.id:
            new_encounter_deck = game.encounter_deck.cardsadd
            new_game = game.update_encounter_deck(new_encounter_deck)
            saved_game = self.game_repository.save(new_game)
            return saved_game is not None
        for p in game.players:
            if p.deck.id == deck_id:
                new_deck = p.deck.add_card(card)
                new_players = tuple(p if p.deck.id != deck_id else p.update_deck(new_deck) for p in game.players)
                new_game = game.update_players(new_players)
                saved_game = self.game_repository.save(new_game)
                return saved_game is not None
        return saved_card is not None
    
    def add_to_game(self, game_id: str, card_code: str) -> bool:
        """
        Add a card by its code to the game's play zone.

        Args:
            card_code: The unique code of the card to add.

        Returns:
            True if the card was added successfully, False otherwise.
        """
        # Check if the card already exists in the repository
        if self.card_repository.exists(card_code):
            return True

        # Fetch card data from MarvelCDB
        card_data = self.marvelcdb_client.fetch_card_by_code(card_code)
        if card_data is None:
            return False

        # Create Card entity
        card = Card.from_dict(card_data)

        # Save the new card to the repository
        saved_card = self.card_repository.save(card)
        return saved_card is not None
    
    def add_to_encounter_deck(self, game_id: str, card_code: str) -> bool:
        """
        Add a card by its code to the encounter deck.

        Args:
            card_code: The unique code of the card to add.

        Returns:
            True if the card was added successfully, False otherwise.
        """
        # Check if the card already exists in the repository
        if self.card_repository.exists(card_code):
            return True

        # Fetch card data from MarvelCDB
        card_data = self.marvelcdb_client.fetch_card_by_code(card_code)
        if card_data is None:
            return False

        # Create Card entity
        card = Card.from_dict(card_data)

        # Save the new card to the repository
        saved_card = self.card_repository.save(card)
        return saved_card is not None