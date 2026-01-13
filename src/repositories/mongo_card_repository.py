from typing import Optional, List
from pymongo.database import Database
from pymongo import UpdateOne
from datetime import datetime, UTC
from src.boundaries.repository import CardRepository
from src.entities import Card


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
        return self._to_entity(doc) if doc else None
    
    def find_by_codes(self, codes: List[str]) -> List[Card]:
        """Find multiple cards by their codes"""
        docs = self.collection.find({'code': {'$in': codes}})
        return [self._to_entity(doc) for doc in docs]
    
    def save(self, card: Card) -> Card:
        """Save a card and return the saved entity"""
        doc = self._to_document(card)
        doc['updated_at'] = datetime.now(UTC)
        
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
            doc = self._to_document(card)
            doc['updated_at'] = datetime.now(UTC)
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
        return [self._to_entity(doc) for doc in docs]
    
    def _to_entity(self, doc: dict) -> Card:
        """Convert MongoDB document to Card entity"""
        return Card(
            code=doc['code'],
            name=doc['name'],
            text=doc.get('text'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )
    
    def _to_document(self, card: Card) -> dict:
        """Convert Card entity to MongoDB document"""
        doc = {
            'code': card.code,
            'name': card.name,
            'created_at': card.created_at or datetime.now(UTC)
        }
        
        if card.text:
            doc['text'] = card.text
        
        return doc