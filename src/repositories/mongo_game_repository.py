from typing import Optional, List
from pymongo.database import Database
from datetime import datetime
from bson.objectid import ObjectId
from src.boundaries.repository import GameRepository
from src.entities import Game, GameState, PlayerZones, CardInPlay, Position


class MongoGameRepository(GameRepository):
    """MongoDB implementation of GameRepository"""
    
    def __init__(self, db: Database):
        if 'games' not in db.list_collection_names():
            db.create_collection('games', capped=False)
        self.collection = db['games']
        self.collection.create_index('updated_at')
        self.collection.create_index('name')
    
    def find_by_id(self, game_id: str) -> Optional[Game]:
        """Find a game by its ID"""
        try:
            doc = self.collection.find_one({'_id': ObjectId(game_id)})
            return self._to_entity(doc) if doc else None
        except Exception:
            return None
    
    def save(self, game: Game) -> bool:
        """Save a game and return whether or not it succeeded"""
        doc = self._to_document(game)
        doc['updated_at'] = datetime.utcnow()
        
        if game.id:
            # Update existing game
            self.collection.update_one(
                {'_id': ObjectId(game.id)},
                {'$set': doc}
            )
            return True
        else:
            # Insert new game
            result = self.collection.insert_one(doc)
            return True if result.inserted_id else False
    
    def delete(self, game_id: str) -> bool:
        """Delete a game by ID"""
        try:
            result = self.collection.delete_one({'_id': ObjectId(game_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def find_all(self) -> List[Game]:
        """Find all games"""
        docs = self.collection.find().sort('updated_at', -1)
        return [self._to_entity(doc) for doc in docs]
    
    def find_recent(self, limit: int = 10) -> List[Game]:
        """Find recent games"""
        docs = self.collection.find().sort('updated_at', -1).limit(limit)
        return [self._to_entity(doc) for doc in docs]
    
    def _to_entity(self, doc: dict) -> Game:
        """Convert MongoDB document to Game entity"""
        state_doc = doc['state']
        
        # Convert players
        players = tuple(
            PlayerZones(
                player_name=p['player_name'],
                deck=tuple(p.get('deck', [])),
                hand=tuple(p.get('hand', [])),
                discard=tuple(p.get('discard', [])),
                removed=tuple(p.get('removed', []))
            )
            for p in state_doc.get('players', [])
        )
        
        # Convert play area
        play_area = tuple(
            CardInPlay(
                code=c['code'],
                position=Position(
                    x=c['position']['x'],
                    y=c['position']['y'],
                    rotation=c.get('rotation', 0),
                    flip_state=c.get('flip_state', False)
                ),
                counters=c.get('counters', {})
            )
            for c in state_doc.get('play_area', [])
        )
        
        # Build GameState
        state = GameState(
            players=players,
            play_area=play_area
        )
        
        # Build Game
        return Game(
            id=str(doc['_id']),
            name=doc['name'],
            deck_ids=tuple(doc.get('deck_ids', [])),
            state=state,
            status=doc['status'],
            host=doc['host'],
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )
    
    def _to_document(self, game: Game) -> dict:
        """Convert Game entity to MongoDB document"""
    
        doc = {
            'name': game.name,
            'status': game.status.value,
            'host': game.host,
            'created_at': game.created_at or datetime.utcnow()
        }
        
        # Lobby fields (when status = LOBBY)
        if game.lobby_players:
            doc['lobby_players'] = [
                {
                    'username': p.username,
                    'deck_id': p.deck_id,
                    'is_ready': p.is_ready,
                    'is_host': p.is_host
                }
                for p in game.lobby_players
            ]
        
        if game.encounter_deck_id:
            doc['encounter_deck_id'] = game.encounter_deck_id
        
        # Game fields (when status = IN_PROGRESS)
        if game.deck_ids:
            doc['deck_ids'] = list(game.deck_ids)
        
        if game.state:
            # Convert players
            doc['state'] = {
                'players': [
                    {
                        'player_name': p.player_name,
                        'deck': list(p.deck),
                        'hand': list(p.hand),
                        'discard': list(p.discard),
                        'removed': list(p.removed)
                    }
                    for p in game.state.players
                ],
                'play_area': [
                    {
                        'code': c.code,
                        'position': {'x': c.position.x, 'y': c.position.y},
                        'exhausted': c.exhausted,
                        'flipped': c.flipped,
                        'counters': dict(c.counters)
                    }
                    for c in game.state.play_area
                ]
            }
        
        if game.id:
            doc['_id'] = ObjectId(game.id)
        
        return doc