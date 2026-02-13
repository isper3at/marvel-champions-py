"""
Interactor to list all saved encounter deck configurations.
Uses the existing DeckRepository to find EncounterDecks with saved_names.
"""

from typing import List, Dict, Any
from src.boundaries.deck_repository import DeckRepository
from src.entities.encounter_deck import EncounterDeck


class ListSavedEncounterDecksInteractor:
    """List all saved encounter deck configurations."""
    
    def __init__(self, deck_repo: DeckRepository):
        self.deck_repo = deck_repo
    
    def execute(self) -> List[Dict[str, Any]]:
        """
        List all saved encounter deck configurations.
        
        Returns:
            List of dicts containing:
            - id: Encounter deck ID
            - name: Primary deck name
            - saved_names: List of all names/aliases
            - created_at: ISO timestamp
            - updated_at: ISO timestamp
        """
        # Get all encounter decks from repository
        all_decks = self.deck_repo.find_all()
        
        # Filter to only EncounterDecks with saved_names
        saved_decks = [
            deck for deck in all_decks
            if isinstance(deck, EncounterDeck) and deck.saved_names
        ]
        
        # Sort by most recently updated first
        saved_decks.sort(
            key=lambda d: d.updated_at if d.updated_at else d.created_at,
            reverse=True
        )
        
        return [
            {
                'id': deck.id,
                'name': deck.name,
                'saved_names': list(deck.saved_names),
                'created_at': deck.created_at.isoformat() if deck.created_at else None,
                'updated_at': deck.updated_at.isoformat() if deck.updated_at else None
            }
            for deck in saved_decks
        ]