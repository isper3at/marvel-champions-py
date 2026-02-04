from src.boundaries.game_repository import DeckRepository
from src.boundaries.marvelcdb_gateway import MarvelCDBGateway
from typing import Optional
from src.entities import DeckList, EncounterDeck

class GetEncounterModule:
    """
    Interactor to get encounter modules from MarvelCDB.
    """
    deck_repo: DeckRepository
    marvelcdb_client: MarvelCDBGateway

    def __init__(self, deck_repo: DeckRepository, marvelcdb_client: MarvelCDBGateway):
        """Initialize the interactor with required repositories and clients."""
        self.deck_repo = deck_repo
        self.marvelcdb_client = marvelcdb_client

    def get(self, module_name:str, update: bool) -> Optional[EncounterDeck]:
        """
        Retrieve an encounter module by its name.

        Args:
            module_name: Name of the encounter module
            update: Whether to fetch the latest data from MarvelCDB

        Returns:
            EncounterModule entity or None if not found
        """

        found_module: Optional[EncounterDeck] = None
        found_module = self.deck_repo.find_encounter_module_by_id(module_name)

        if update or found_module is None:
            found_module = self.marvelcdb_client.get_module(module_name)
            if found_module is not None:
                self.deck_repo.save_encounter_module(found_module)

        return found_module 