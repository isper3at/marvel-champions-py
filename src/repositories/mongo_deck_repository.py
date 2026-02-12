from typing import Optional, List
from pymongo.database import Database
from src.boundaries import DeckRepository
from src.entities import DeckList, DeckCard
import datetime

from src.entities.deck import DeckList

from .serializers import DeckListSerializer

class MongoDeckRepository(DeckRepository):
    """MongoDB implementation of DeckRepository"""
    
    def __init__(self, db: Database):
        if 'decks' not in db.list_collection_names():
            db.create_collection('decks', capped=False)
        self.decks_collection = db['decks']
        self.decks_collection.create_index('deck_id')
        self.decks_collection.create_index('name')

    def find_by_id(self, deck_id: str) -> Optional[DeckList]:
        """Find a deck by its ID"""
        try:
            doc = self.decks_collection.find_one({'deck_id': deck_id})
            return DeckListSerializer.to_entity(doc) if doc else None
        except Exception:
            return None
    
    def save(self, deck_list: DeckList) -> Optional[DeckList]:
        """Save a deck list and return the saved entity"""
        doc = DeckListSerializer.to_doc(deck_list)
        doc['updated_at'] = datetime.datetime.now(datetime.UTC)
        
        self.decks_collection.update_one(
            {'deck_id': deck_list.id},
            {'$set': doc},
            True
        )
        return self.find_by_id(deck_list.id)

    def delete(self, deck_id: str) -> bool:
        """Delete a deck by ID"""
        try:
            result = self.decks_collection.delete_one({'deck_id': deck_id})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def find_all(self) -> List[DeckList]:
        """Find all decks"""
        docs = self.decks_collection.find().sort('updated_at', -1)
        return [DeckListSerializer.to_entity(doc) for doc in docs]
    
    def find_all_modules(self) -> List[DeckList]:
        """Find all encounter modules"""
        docs = self.decks_collection.find({'is_module': True}).sort('name', -1)
        return [DeckListSerializer.to_entity(doc) for doc in docs]
    
    def find_all_player_decks(self) -> List[DeckList]:
        """Find all player decks"""
        docs = self.decks_collection.find({'is_module': False}).sort('name', -1)
        return [DeckListSerializer.to_entity(doc) for doc in docs]