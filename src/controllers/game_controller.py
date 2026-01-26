"""
Game Controller - REST API endpoints for game operations.

Endpoints:
- GET /api/games - Get all games
- GET /api/games/recent - Get recent games
- GET /api/games/<id> - Get game by ID
- POST /api/games - Create new game
- DELETE /api/games/<id> - Delete game
- POST /api/games/<id>/draw - Draw card for player
- POST /api/games/<id>/shuffle - Shuffle discard into deck
- POST /api/games/<id>/play - Play card to table
- POST /api/games/<id>/move - Move card on table
- POST /api/games/<id>/rotate - Toggle card rotation
- POST /api/games/<id>/counter - Add counter to card
"""

import uuid
from flask import jsonify, request
from src.controllers import game_bp
from src.middleware import audit_endpoint
from src.interactors import GameInteractor
from src.entities import Position
import logging

from src.repositories.serializers import GameSerializer

logger = logging.getLogger(__name__)

_game_interactor: GameInteractor = None


def init_game_controller(game_interactor: GameInteractor):
    """Initialize controller with interactor"""
    global _game_interactor
    _game_interactor = game_interactor


@game_bp.route('', methods=['GET'])
@audit_endpoint('list_games')
def list_games():
    """Get all games"""
    try:
        logger.info("Fetching all games")
        
        games = _game_interactor.get_all_games()
        
        return jsonify({
            'games': [
                {
                    'id': game.id,
                    'name': game.name,
                    'players': [p.name for p in game.players],
                    'created_at': game.created_at.isoformat() if game.created_at else None
                }
                for game in games
            ],
            'count': len(games)
        })
        
    except Exception as e:
        logger.error(f"Error listing games: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/recent', methods=['GET'])
@audit_endpoint('list_recent_games')
def list_recent_games():
    """Get recent games"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        logger.info(f"Fetching {limit} recent games")
        
        games = _game_interactor.get_recent_games(limit)
        
        return jsonify({
            'games': [
                {
                    'id': game.id,
                    'name': game.name,
                    'players': [p.name for p in game.players],
                    'created_at': game.created_at.isoformat() if game.created_at else None
                }
                for game in games
            ],
            'count': len(games)
        })
        
    except Exception as e:
        logger.error(f"Error fetching recent games: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>', methods=['GET'])
@audit_endpoint('get_game')
def get_game(game_id: str):
    """Get full game state"""
    try:
        uuid_id = uuid.UUID(game_id)
        logger.info(f"Fetching game: {game_id}")
        
        game = _game_interactor.get_game(uuid_id)
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify(GameSerializer.to_doc(game))
        
    except Exception as e:
        logger.error(f"Error fetching game {game_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('', methods=['POST'])
@audit_endpoint('create_game')
def create_game():
    """Create a new game"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'deck_ids' not in data or 'player_names' not in data:
        return jsonify({'error': 'name, deck_ids, and player_names are required'}), 400
    
    try:
        logger.info(f"Creating game: {data['name']}")
        
        game = _game_interactor.create_game(
            data['name'],
            data['deck_ids'],
            data['player_names']
        )
        
        logger.info(f"Created game: {game.id}")
        
        return jsonify({
            'success': True,
            'game': {
                'id': game.id,
                'name': game.name,
                'players': [p.name for p in game.players]
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating game: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>', methods=['DELETE'])
@audit_endpoint('delete_game')
def delete_game(game_id: str):
    """Delete a game"""
    try:
        logger.info(f"Deleting game: {game_id}")
        
        success = _game_interactor.delete_game(game_id)
        
        if not success:
            return jsonify({'error': 'Game not found'}), 404
        
        logger.info(f"Deleted game: {game_id}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting game {game_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/draw', methods=['POST'])
@audit_endpoint('draw_card')
def draw_card(game_id: str):
    """Draw a card for a player"""
    data = request.get_json()
    
    if not data or 'player_name' not in data:
        return jsonify({'error': 'player_name is required'}), 400
    
    try:
        logger.info(f"Drawing card for {data['player_name']} in game {game_id}")
        
        game = _game_interactor.draw_card(game_id, data['player_name'])
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error drawing card: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/shuffle', methods=['POST'])
@audit_endpoint('shuffle_deck')
def shuffle_deck(game_id: str):
    """Shuffle discard pile into deck"""
    data = request.get_json()
    
    if not data or 'player_name' not in data:
        return jsonify({'error': 'player_name is required'}), 400
    
    try:
        logger.info(f"Shuffling deck for {data['player_name']} in game {game_id}")
        
        game = _game_interactor.shuffle_discard_into_deck(game_id, data['player_name'])
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error shuffling deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/play', methods=['POST'])
@audit_endpoint('play_card')
def play_card(game_id: str):
    """Play a card from hand to table"""
    data = request.get_json()
    
    required = ['player_name', 'card_code', 'x', 'y']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {", ".join(required)}'}), 400
    
    try:
        logger.info(f"Playing card {data['card_code']} for {data['player_name']}")
        
        position = Position(x=data['x'], y=data['y'])
        
        game = _game_interactor.play_card_to_table(
            game_id,
            data['player_name'],
            data['card_code'],
            position
        )
        
        if not game:
            return jsonify({'error': 'Game not found or card not in hand'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error playing card: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/move', methods=['POST'])
@audit_endpoint('move_card')
def move_card(game_id: str):
    """Move a card on the table"""
    data = request.get_json()
    
    required = ['card_code', 'x', 'y']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {", ".join(required)}'}), 400
    
    try:
        logger.debug(f"Moving card {data['card_code']} to ({data['x']}, {data['y']})")
        
        position = Position(x=data['x'], y=data['y'])
        
        game = _game_interactor.move_card_on_table(game_id, data['card_code'], position)
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error moving card: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/rotate', methods=['POST'])
@audit_endpoint('rotate_card')
def rotate_card(game_id: str):
    """Toggle card rotation (exhaust/ready)"""
    data = request.get_json()
    
    if not data or 'card_code' not in data:
        return jsonify({'error': 'card_code is required'}), 400
    
    try:
        logger.debug(f"Rotating card {data['card_code']}")
        
        game = _game_interactor.toggle_card_rotation(game_id, data['card_code'])
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error rotating card: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/counter', methods=['POST'])
@audit_endpoint('add_counter')
def add_counter(game_id: str):
    """Add counters to a card"""
    data = request.get_json()
    
    required = ['card_code', 'counter_type', 'amount']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {", ".join(required)}'}), 400
    
    try:
        logger.debug(f"Adding {data['amount']} {data['counter_type']} to {data['card_code']}")
        
        game = _game_interactor.add_counter_to_card(
            game_id,
            data['card_code'],
            data['counter_type'],
            data['amount']
        )
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error adding counter: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500