from typing import Optional, List
from pymongo.database import Database
from src.boundaries.game_repository import DeckRepository
from src.entities import Deck, DeckCard
import datetime

from src.entities.encounter_deck import EncounterDeck

from .serializers import DeckSerializer, EncounterDeckSerializer

class MongoDeckRepository(DeckRepository):
    """MongoDB implementation of DeckRepository"""
    
    def __init__(self, db: Database):
        if 'decks' not in db.list_collection_names():
            db.create_collection('decks', capped=False)
        self.collection = db['decks']
        self.collection.create_index('deck_id')
        self.collection.create_index('name')
    
    def find_by_id(self, deck_id: str) -> Optional[Deck]:
        """Find a deck by its ID"""
        try:
            doc = self.collection.find_one({'deck_id': deck_id})
            return DeckSerializer.to_entity(doc) if doc else None
        except Exception:
            return None
    
    def find_by_marvelcdb_id(self, marvelcdb_id: str) -> Optional[Deck]:
        """Find a deck by its MarvelCDB ID"""
        doc = self.collection.find_one({'source_url': {'$regex': f'/decklist/{marvelcdb_id}$'}})
        return DeckSerializer.to_entity(doc) if doc else None
    
    def save(self, deck: Deck) -> Optional[Deck]:
        """Save a deck and return the saved entity"""
        doc = DeckSerializer.to_doc(deck)
        doc['updated_at'] = datetime.datetime.now(datetime.UTC)
        
        self.collection.update_one(
            {'deck_id': deck.id},
            {'$set': doc},
            True
        )
        return self.find_by_id(deck.id)
    
    def save_encounter_deck(self, deck: EncounterDeck) -> EncounterDeck:
        """Save an encounter deck and return the saved entity"""
        doc = EncounterDeckSerializer.to_doc(deck)
        doc['updated_at'] = datetime.datetime.now(datetime.UTC)
        
        self.collection.update_one(
            {'deck_id': deck.id},
            {'$set': doc},
            True
        )
        return self.find_encounter_deck_by_id(deck.id)
    
    def find_encounter_deck_by_id(self, deck_id: str) -> EncounterDeck:
        """Find an encounter deck by its ID"""
        try:
            doc = self.collection.find_one({'deck_id': deck_id})
            return EncounterDeckSerializer.to_entity(doc) if doc else None
        except Exception:
            return None
    
    def delete(self, deck_id: str) -> bool:
        """Delete a deck by ID"""
        try:
            result = self.collection.delete_one({'deck_id': deck_id})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def find_all(self) -> List[Deck]:
        """Find all decks"""
        docs = self.collection.find().sort('updated_at', -1)
        return [DeckSerializer.to_entity(doc) for doc in docs]