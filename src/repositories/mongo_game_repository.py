"""
MongoDB implementation of GameRepository
"""
from typing import Optional, List
import uuid
from pymongo.database import Database
from src.boundaries.repository import GameRepository
from src.entities import Game
import datetime

from .serializers import GameSerializer


class MongoGameRepository(GameRepository):
    """MongoDB implementation of GameRepository"""
    
    def __init__(self, db: Database):
        if 'games' not in db.list_collection_names():
            db.create_collection('games', capped=False)
        self.collection = db['games']
        self.collection.create_index('updated_at')
        self.collection.create_index('name')
    
    def find_by_id(self, game_id: uuid.UUID) -> Optional[Game]:
        """Find a game by its ID"""
        try:
            doc = self.collection.find_one({'_id': game_id})
            return GameSerializer.to_entity(doc) if doc else None
        except Exception:
            return None
    
    def save(self, game: Game) -> Game:
        """Save a game and return the saved entity"""
        doc = GameSerializer.to_doc(game)
        doc['updated_at'] = datetime.datetime.now(datetime.UTC)
        self.collection.update_one(
            {'_id': game.id},
            {'$set': doc},
            True
        )
        return self.find_by_id(game.id)
     
    def delete(self, game_id: uuid.UUID) -> bool:
        """Delete a game by ID"""
        try:
            result = self.collection.delete_one({'_id': game_id})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def find_all(self) -> List[Game]:
        """Find all games"""
        docs = self.collection.find().sort('updated_at', -1)
        return [GameSerializer.to_entity(doc) for doc in docs]
    
    def find_recent(self, limit: int = 10) -> List[Game]:
        """Find recent games"""
        docs = self.collection.find().sort('updated_at', -1).limit(limit)
        return [GameSerializer.to_entity(doc) for doc in docs]