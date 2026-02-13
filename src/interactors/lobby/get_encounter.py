"""
Interactor to load a saved encounter deck by name and return module names.
Uses the existing DeckRepository to find EncounterDecks.
"""

from typing import Optional, List
from src.boundaries.deck_repository import DeckRepository
from src.entities.encounter_deck import EncounterDeck


class LoadSavedEncounterDeckInteractor:
    """Load a saved encounter deck configuration by name and return module names."""
    
    def __init__(self, deck_repo: DeckRepository):
        self.deck_repo = deck_repo
    
    def execute(self, name: str) -> Optional[List[str]]:
        """
        Load a saved encounter deck configuration by name and extract module names.
        
        Args:
            name: Name/alias of the saved configuration
            
        Returns:
            List of module names if found, None otherwise
        """
        if not name or not name.strip():
            return None
        
        name = name.strip()
        
        # Get all encounter decks
        all_decks = self.deck_repo.find_all()
        
        # Find the deck with this name in saved_names
        for deck in all_decks:
            if isinstance(deck, EncounterDeck) and name in deck.saved_names:
                # Extract module names from source_url
                if deck.source_url and deck.source_url.startswith("modules:"):
                    modules_str = deck.source_url.replace("modules:", "")
                    return modules_str.split(",")
                return None
        
        return None