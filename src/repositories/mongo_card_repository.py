from typing import Optional, List
from pymongo.database import Database
from pymongo import UpdateOne
from src.boundaries import CardRepository
from src.entities import Card
import datetime

from .serializers import CardSerializer

class MongoCardRepository(CardRepository):
    """MongoDB implementation of CardRepository"""
    
    def __init__(self, db: Database):
        if 'cards' not in db.list_collection_names():
            db.create_collection('cards', capped=False)
        self.collection = db['cards']
        self.collection.create_index('code', unique=True)
        self.collection.create_index('name')
    
    def find_all(self, limit = 100, offset = 0):
        return super().find_all(limit, offset)
    
    def find_by_code(self, code: str) -> Optional[Card]:
        """Find a card by its unique code"""
        doc = self.collection.find_one({'code': code})
        return CardSerializer.to_entity(doc) if doc else None
    
    def find_by_codes(self, codes: List[str]) -> List[Card]:
        """Find multiple cards by their codes"""
        docs = self.collection.find({'code': {'$in': codes}})
        return [CardSerializer.to_entity(doc) for doc in docs]
    
    def save(self, card: Card) -> Optional[Card]:
        """Save a card and return the saved entity"""
        doc = CardSerializer.to_doc(card)
        doc['updated_at'] = datetime.datetime.now(datetime.UTC)
        
        self.collection.update_one(
            {'code': card.code},
            {'$set': doc},
            upsert=True
        )

        return self.find_by_code(card.code)
    
    def save_all(self, cards: List[Card]) -> List[Card]:
        """Save multiple cards"""
        if not cards:
            return []
        
        operations = []
        for card in cards:
            doc = CardSerializer.to_doc(card)
            doc['updated_at'] = datetime.datetime.now(datetime.UTC)
            operations.append(
                UpdateOne(
                    filter={'code': card.code},
                    update={'$set': doc},
                    upsert=True)
            )
        
        if operations:
            self.collection.bulk_write(operations)
        
        return self.find_by_codes([card.code for card in cards])
    
    def exists(self, code: str) -> bool:
        """Check if a card exists"""
        return self.collection.count_documents({'code': code}) > 0
    
    def search_by_name(self, name: str) -> List[Card]:
        """Search cards by name (partial match)"""
        docs = self.collection.find({
            'name': {'$regex': name, '$options': 'i'}
        }).limit(50)
        return [CardSerializer.to_entity(doc) for doc in docs]