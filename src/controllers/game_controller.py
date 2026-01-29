"""
Game Controller - REST API endpoints for game operations.

Endpoints:
- GET /api/games - Get all games
- GET /api/games/<id> - Get game by ID
- POST /api/games/<id>/draw - Draw card
- POST /api/games/<id>/shuffle - Shuffle discard
- POST /api/games/<id>/play - Play card
- POST /api/games/<id>/move - Move card
- POST /api/games/<id>/rotate - Toggle rotation
- POST /api/games/<id>/counter - Add counter
- DELETE /api/games/<id> - Delete game
"""

from flask import jsonify, request
from src.controllers import game_bp
from src.middleware import audit_endpoint
from src.entities import Position
import logging

logger = logging.getLogger(__name__)

# Global interactors
_list_games_interactor = None
_get_game_interactor = None
_draw_card_interactor = None
_shuffle_discard_interactor = None
_play_card_interactor = None
_move_card_interactor = None
_toggle_exhaustion_interactor = None
_add_counter_interactor = None
_delete_game_interactor = None


def init_game_controller(
    list_games_interactor,
    get_game_interactor,
    draw_card_interactor,
    shuffle_discard_interactor,
    play_card_interactor,
    move_card_interactor,
    toggle_exhaustion_interactor,
    add_counter_interactor,
    delete_game_interactor
):
    """Initialize controller with interactors."""
    global (
        _list_games_interactor,
        _get_game_interactor,
        _draw_card_interactor,
        _shuffle_discard_interactor,
        _play_card_interactor,
        _move_card_interactor,
        _toggle_exhaustion_interactor,
        _add_counter_interactor,
        _delete_game_interactor,
    )
    _list_games_interactor = list_games_interactor
    _get_game_interactor = get_game_interactor
    _draw_card_interactor = draw_card_interactor
    _shuffle_discard_interactor = shuffle_discard_interactor
    _play_card_interactor = play_card_interactor
    _move_card_interactor = move_card_interactor
    _toggle_exhaustion_interactor = toggle_exhaustion_interactor
    _add_counter_interactor = add_counter_interactor
    _delete_game_interactor = delete_game_interactor


@game_bp.route('', methods=['GET'])
@audit_endpoint('list_games')
def list_games():
    """Get all games."""
    try:
        logger.info("Fetching all games")
        games = _list_games_interactor.execute()
        
        return jsonify({
            'games': [
                {
                    'id': str(game.id),
                    'name': game.name,
                    'phase': game.phase.value,
                    'host': game.host,
                }
                for game in games
            ],
            'count': len(games)
        })
        
    except Exception as e:
        logger.error(f"Error listing games: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>', methods=['GET'])
@audit_endpoint('get_game')
def get_game(game_id: str):
    """Get a game by ID."""
    try:
        logger.info(f"Fetching game: {game_id}")
        game = _get_game_interactor.execute(game_id)
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({
            'id': str(game.id),
            'name': game.name,
            'phase': game.phase.value,
            'host': game.host,
        })
        
    except Exception as e:
        logger.error(f"Error fetching game: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/draw', methods=['POST'])
@audit_endpoint('draw_card')
def draw_card(game_id: str):
    """Draw a card."""
    data = request.get_json()
    
    if not data or 'player_name' not in data:
        return jsonify({'error': 'player_name required'}), 400
    
    try:
        logger.info(f"Drawing card for {data['player_name']}")
        game = _draw_card_interactor.execute(game_id, data['player_name'])
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error drawing card: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/shuffle', methods=['POST'])
@audit_endpoint('shuffle_discard')
def shuffle_discard(game_id: str):
    """Shuffle discard into deck."""
    data = request.get_json()
    
    if not data or 'player_name' not in data:
        return jsonify({'error': 'player_name required'}), 400
    
    try:
        logger.info(f"Shuffling discard for {data['player_name']}")
        game = _shuffle_discard_interactor.execute(game_id, data['player_name'])
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error shuffling discard: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/play', methods=['POST'])
@audit_endpoint('play_card')
def play_card(game_id: str):
    """Play a card to the table."""
    data = request.get_json()
    
    required = ['player_name', 'card_code', 'position']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'{", ".join(required)} required'}), 400
    
    try:
        logger.info(f"Playing card {data['card_code']}")
        position = Position(**data['position'])
        game = _play_card_interactor.execute(
            game_id, data['player_name'], data['card_code'], position
        )
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error playing card: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/move', methods=['POST'])
@audit_endpoint('move_card')
def move_card(game_id: str):
    """Move a card on the table."""
    data = request.get_json()
    
    required = ['card_code', 'position']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'{", ".join(required)} required'}), 400
    
    try:
        logger.info(f"Moving card {data['card_code']}")
        position = Position(**data['position'])
        game = _move_card_interactor.execute(game_id, data['card_code'], position)
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error moving card: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/rotate', methods=['POST'])
@audit_endpoint('toggle_exhaustion')
def toggle_exhaustion(game_id: str):
    """Toggle card exhaustion."""
    data = request.get_json()
    
    if not data or 'card_code' not in data:
        return jsonify({'error': 'card_code required'}), 400
    
    try:
        logger.info(f"Toggling exhaustion for {data['card_code']}")
        game = _toggle_exhaustion_interactor.execute(game_id, data['card_code'])
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error toggling exhaustion: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>/counter', methods=['POST'])
@audit_endpoint('add_counter')
def add_counter(game_id: str):
    """Add a counter to a card."""
    data = request.get_json()
    
    required = ['card_code', 'counter_type']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'{", ".join(required)} required'}), 400
    
    try:
        logger.info(f"Adding counter to {data['card_code']}")
        amount = data.get('amount', 1)
        game = _add_counter_interactor.execute(
            game_id, data['card_code'], data['counter_type'], amount
        )
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error adding counter: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@game_bp.route('/<game_id>', methods=['DELETE'])
@audit_endpoint('delete_game')
def delete_game(game_id: str):
    """Delete a game."""
    try:
        logger.info(f"Deleting game: {game_id}")
        success = _delete_game_interactor.execute(game_id)
        
        if not success:
            return jsonify({'error': 'Game not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting game: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
