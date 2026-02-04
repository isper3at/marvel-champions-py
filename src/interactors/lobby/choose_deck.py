"""Interactor to choose a deck for a player."""
from typing import Optional
import uuid
from src.entities import Game, Deck
from src.boundaries.game_repository import GameRepository, DeckRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway


class ChooseDeckInteractor:
    """Choose a deck for a player in the lobby."""
    
    def __init__(
        self,
        game_repo: GameRepository,
        deck_repo: DeckRepository,
        marvelcdb_gateway: MarvelCDBGateway
    ):
        self.game_repo = game_repo
        self.deck_repo = deck_repo
        self.marvelcdb = marvelcdb_gateway
    
    def execute(self, game_id: str, username: str, deck_id: str) -> Game:
        """
        Choose a deck for a player.
        
        Args:
            game_id: Lobby ID
            username: Player username
            deck_id: Deck to use
            
        Returns:
            Updated Game
            
        Raises:
            ValueError: If lobby or deck not found
        """
        try:
            game_uuid = uuid.UUID(game_id)
        except ValueError:
            raise ValueError("Invalid game ID")
        
        game = self.game_repo.find_by_id(game_uuid)
        if not game:
            raise ValueError("Lobby not found")
        
        # Verify deck exists
        deck = self.deck_repo.find_by_id(deck_id)
        if not deck:
            raise ValueError("Deck not found")
        
        # Find player and update with deck
        player = next((p for p in game.players if p.name == username), None)
        if not player:
            raise ValueError("Player not in lobby")
        
        updated_player = player.play_deck(deck)
        updated_game = game.update_player(updated_player)
        
        return self.game_repo.save(updated_game)
