"""Interactor to build an encounter deck."""
from typing import List
from src.entities import EncounterDeck
from src.boundaries.repository import DeckRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from src.interactors.marvelcdb.get_encounter_module import GetEncounterModule


class BuildEncounterDeckInteractor:
    """Build an encounter deck from multiple modules."""
    
    def __init__(
        self,
        deck_repo: DeckRepository,
        marvelcdb_gateway: MarvelCDBGateway
    ):
        self.deck_repo = deck_repo
        self.marvelcdb = marvelcdb_gateway
    
    def execute(self, module_names: List[str]) -> EncounterDeck:
        """
        Build encounter deck by combining modules.
        
        Args:
            module_names: List of encounter module names
            
        Returns:
            Combined EncounterDeck
        """
        interactor = GetEncounterModule(self.deck_repo, self.marvelcdb)
        encounter_deck = None
        
        for module_name in module_names:
            module = interactor.get(module_name, update=True)
            if not module:
                continue
            
            if not encounter_deck:
                encounter_deck = module
            else:
                encounter_deck = encounter_deck.join_encounter_deck(module)
        
        return encounter_deck
