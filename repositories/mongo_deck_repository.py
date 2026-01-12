from typing import Optional, List
from pymongo.database import Database
from datetime import datetime
from bson.objectid import ObjectId
from boundaries.repository import DeckRepository
from entities import Deck, DeckCard


class MongoDeckRepository(DeckRepository):
    """MongoDB implementation of DeckRepository"""
    
    def __init__(self, db: Database):
        self.collection = db['decks']
        self.collection.create_index('updated_at')
        self.collection.create_index('name')
    
    def find_by_id(self, deck_id: str) -> Optional[Deck]:
        """Find a deck by its ID"""
        try:
            doc = self.collection.find_one({'_id': ObjectId(deck_id)})
            return self._to_entity(doc) if doc else None
        except Exception:
            return None
    
    def save(self, deck: Deck) -> Deck:
        """Save a deck and return the saved entity"""
        doc = self._to_document(deck)
        doc['updated_at'] = datetime.utcnow()
        
        if deck.id:
            # Update existing deck
            self.collection.update_one(
                {'_id': ObjectId(deck.id)},
                {'$set': doc}
            )
            return self.find_by_id(deck.id)
        else:
            # Insert new deck
            result = self.collection.insert_one(doc)
            return self.find_by_id(str(result.inserted_id))
    
    def delete(self, deck_id: str) -> bool:
        """Delete a deck by ID"""
        try:
            result = self.collection.delete_one({'_id': ObjectId(deck_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def find_all(self) -> List[Deck]:
        """Find all decks"""
        docs = self.collection.find().sort('updated_at', -1)
        return [self._to_entity(doc) for doc in docs]
    
    def _to_entity(self, doc: dict) -> Deck:
        """Convert MongoDB document to Deck entity"""
        cards = tuple(
            DeckCard(code=c['code'], quantity=c['quantity'])
            for c in doc['cards']
        )
        
        return Deck(
            id=str(doc['_id']),
            name=doc['name'],
            cards=cards,
            source_url=doc.get('source_url'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )
    
    def _to_document(self, deck: Deck) -> dict:
        """Convert Deck entity to MongoDB document"""
        doc = {
            'name': deck.name,
            'cards': [
                {'code': c.code, 'quantity': c.quantity}
                for c in deck.cards
            ],
            'created_at': deck.created_at or datetime.utcnow()
        }
        
        if deck.source_url:
            doc['source_url'] = deck.source_url
        
        if deck.id:
            doc['_id'] = ObjectId(deck.id)
        
        return doc