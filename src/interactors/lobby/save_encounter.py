"""
Interactor to save an encounter deck configuration with a name.
Uses the existing DeckRepository to store EncounterDeck entities.
"""

from typing import Tuple, List
from src.boundaries.deck_repository import DeckRepository
from src.entities.encounter_deck import EncounterDeck
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway


class SaveEncounterDeckInteractor:
    """
    Save an encounter deck configuration with a name.
    
    This interactor builds an EncounterDeck from module names and saves it
    with a custom name. If an encounter deck with the same modules already
    exists, it adds the new name as an alias.
    """
    
    def __init__(
        self,
        deck_repo: DeckRepository,
        marvelcdb_gateway: MarvelCDBGateway
    ):
        self.deck_repo = deck_repo
        self.marvelcdb = marvelcdb_gateway
    
    def execute(self, module_names: List[str], save_name: str) -> EncounterDeck:
        """
        Build and save an encounter deck configuration.
        
        Args:
            module_names: List of module names to build the deck from
            save_name: Name to save this configuration under
            
        Returns:
            Saved EncounterDeck with the name added to saved_names
            
        Raises:
            ValueError: If module_names is empty or save_name is empty
        """
        if not module_names:
            raise ValueError("Cannot save encounter deck with no modules")
        
        if not save_name or not save_name.strip():
            raise ValueError("Cannot save encounter deck with empty name")
        
        save_name = save_name.strip()
        
        # Build the encounter deck from modules
        encounter_deck = None
        for module_name in module_names:
            if not encounter_deck:
                encounter_deck = self.marvelcdb.get_module(module_name)
            else:
                encounter_deck = encounter_deck.join_encounter_deck(
                    self.marvelcdb.get_module(module_name)
                )
        
        # Generate a stable ID based on sorted module names
        # This ensures the same module combination always gets the same ID
        module_hash = hash(tuple(sorted(module_names)))
        deck_id = f"encounter_{abs(module_hash)}"
        
        # Store module names in source_url for later retrieval
        source_url = f"modules:{','.join(module_names)}"
        
        # Check if this configuration already exists
        existing = self.deck_repo.find_by_id(deck_id)
        
        if existing and isinstance(existing, EncounterDeck):
            # Add the name as an alias
            updated = existing.add_saved_name(save_name)
            return self.deck_repo.save(updated)
        else:
            # Create new encounter deck with the save name
            saved_deck = EncounterDeck(
                id=deck_id,
                name=encounter_deck.name,
                cards=encounter_deck.cards,
                villian_cards=encounter_deck.villian_cards,
                main_scheme_cards=encounter_deck.main_scheme_cards,
                scenario_cards=encounter_deck.scenario_cards,
                source_url=source_url,  # Store module names here
                created_at=encounter_deck.created_at,
                updated_at=encounter_deck.updated_at,
                saved_names=(save_name,)
            )
            return self.deck_repo.save(saved_deck)