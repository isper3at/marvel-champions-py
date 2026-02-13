"""
Lobby Controller - REST API endpoints for lobby operations.

Endpoints:
- POST /api/lobby - Create new lobby
- GET /api/lobby - List all lobbies
- GET /api/lobby/<id> - Get lobby details
- POST /api/lobby/<id>/join - Join lobby
- POST /api/lobby/<id>/leave - Leave lobby
- PUT /api/lobby/<id>/deck - Choose deck
- POST /api/lobby/<id>/ready - Toggle ready
- POST /api/lobby/<id>/start - Start game
- DELETE /api/lobby/<id> - Delete lobby
"""

from flask import jsonify, request
from src.controllers import lobby_bp
from src.middleware import audit_endpoint
import logging

logger = logging.getLogger(__name__)

# Global interactors
_create_lobby_interactor = None
_join_lobby_interactor = None
_leave_lobby_interactor = None
_get_lobby_interactor = None
_choose_deck_interactor = None
_toggle_ready_interactor = None
_start_game_interactor = None
_build_encounter_deck_interactor = None
_list_lobbies_interactor = None
_delete_lobby_interactor = None
_save_encounter_deck_interactor = None
_list_saved_encounter_decks_interactor = None
_load_saved_encounter_deck_interactor = None

def init_lobby_controller(
    create_lobby_interactor,
    join_lobby_interactor,
    leave_lobby_interactor,
    get_lobby_interactor,
    choose_deck_interactor,
    toggle_ready_interactor,
    start_game_interactor,
    build_encounter_deck_interactor,
    list_lobbies_interactor,
    delete_lobby_interactor,
    save_encounter_deck_interactor,
    list_saved_encounter_decks_interactor,
    load_saved_encounter_deck_interactor 
):
    """Initialize controller with interactors."""
    global _create_lobby_interactor
    global _join_lobby_interactor
    global _leave_lobby_interactor
    global _get_lobby_interactor
    global _choose_deck_interactor
    global _toggle_ready_interactor
    global _start_game_interactor
    global _build_encounter_deck_interactor
    global _list_lobbies_interactor
    global _delete_lobby_interactor
    global _save_encounter_deck_interactor  
    global _list_saved_encounter_decks_interactor
    global _load_saved_encounter_deck_interactor 
    
    _create_lobby_interactor = create_lobby_interactor
    _join_lobby_interactor = join_lobby_interactor
    _leave_lobby_interactor = leave_lobby_interactor
    _get_lobby_interactor = get_lobby_interactor
    _choose_deck_interactor = choose_deck_interactor
    _toggle_ready_interactor = toggle_ready_interactor
    _start_game_interactor = start_game_interactor
    _build_encounter_deck_interactor = build_encounter_deck_interactor
    _list_lobbies_interactor = list_lobbies_interactor
    _delete_lobby_interactor = delete_lobby_interactor
    _save_encounter_deck_interactor = save_encounter_deck_interactor
    _list_saved_encounter_decks_interactor = list_saved_encounter_decks_interactor
    _load_saved_encounter_deck_interactor = load_saved_encounter_deck_interactor 


@lobby_bp.route('', methods=['POST'])
@audit_endpoint('create_lobby')
def create_lobby():
    """Create a new game lobby."""
    data = request.get_json()
    
    if not data or 'name' not in data or 'username' not in data:
        return jsonify({'error': 'name and username are required'}), 400
    
    try:
        logger.info(f"Creating lobby: {data['name']} (host: {data['username']})")
        game = _create_lobby_interactor.execute(data['name'], data['username'])
        
        return jsonify({
            'success': True,
            'lobby': {
                'id': str(game.id),
                'name': game.name,
                'phase': game.phase.value,
                'host': game.host,
                'players': [{'name': p.name, 'is_ready': p.is_ready} for p in game.players],
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('', methods=['GET'])
@audit_endpoint('list_lobbies')
def list_lobbies():
    """Get all lobbies."""
    try:
        logger.info("Fetching all lobbies")
        lobbies = _list_lobbies_interactor.execute()
        
        return jsonify({
            'lobbies': [
                {
                    'id': str(g.id),
                    'name': g.name,
                    'host': g.host,
                    'players': len(g.players),
                    'phase': g.phase.value
                }
                for g in lobbies
            ],
            'count': len(lobbies)
        })
        
    except Exception as e:
        logger.error(f"Error listing lobbies: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@lobby_bp.route('/<lobby_id>', methods=['GET'])
@audit_endpoint('get_lobby')
def get_lobby(lobby_id):
    """Get lobby details."""
    try:
        logger.info(f"Fetching lobby {lobby_id}")
        game = _get_lobby_interactor.execute(lobby_id)
        
        if not game:
            return jsonify({'error': 'Lobby not found'}), 404
        
        return jsonify({
            'id': str(game.id),
            'name': game.name,
            'host': game.host,
            'phase': game.phase.value,
            'players': [{'name': p.name, 'is_ready': p.is_ready} for p in game.players],
        })
        
    except Exception as e:
        logger.error(f"Error fetching lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@lobby_bp.route('/<lobby_id>/join', methods=['POST'])
@audit_endpoint('join_lobby')
def join_lobby(lobby_id):
    """Join a lobby."""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username required'}), 400
    
    try:
        logger.info(f"Player {data['username']} joining lobby {lobby_id}")
        game = _join_lobby_interactor.execute(lobby_id, data['username'])
        
        return jsonify({
            'success': True,
            'lobby': {
                'id': str(game.id),
                'players': [{'name': p.name, 'is_ready': p.is_ready} for p in game.players],
            }
        })
        
    except ValueError as e:
        logger.warning(f"Error joining lobby: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error joining lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/leave', methods=['POST'])
@audit_endpoint('leave_lobby')
def leave_lobby(lobby_id):
    """Leave a lobby."""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username required'}), 400
    
    try:
        logger.info(f"Player {data['username']} leaving lobby {lobby_id}")
        game = _leave_lobby_interactor.execute(lobby_id, data['username'])
        
        if not game:
            return jsonify({'success': True, 'message': 'Lobby deleted'})
        
        return jsonify({
            'success': True,
            'lobby': {
                'id': str(game.id),
                'players': [{'name': p.name} for p in game.players],
            }
        })
        
    except Exception as e:
        logger.error(f"Error leaving lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/deck', methods=['PUT'])
@audit_endpoint('choose_deck')
def choose_deck(lobby_id):
    """Choose a deck for the player."""
    data = request.get_json()
    
    if not data or 'username' not in data or 'deck_id' not in data:
        return jsonify({'error': 'username and deck_id required'}), 400
    
    try:
        logger.info(f"Player {data['username']} choosing deck {data['deck_id']}")
        game = _choose_deck_interactor.execute(
            lobby_id, data['username'], data['deck_id']
        )
        
        return jsonify({'success': True})
        
    except ValueError as e:
        logger.warning(f"Error choosing deck: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error choosing deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/ready', methods=['POST'])
@audit_endpoint('toggle_ready')
def toggle_ready(lobby_id):
    """Toggle player's ready status."""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username required'}), 400
    
    try:
        logger.info(f"Player {data['username']} toggling ready status")
        game = _toggle_ready_interactor.execute(lobby_id, data['username'])
        
        return jsonify({
            'success': True,
            'players': [
                {'name': p.name, 'is_ready': p.is_ready}
                for p in game.players
            ]
        })
        
    except ValueError as e:
        logger.warning(f"Error toggling ready: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error toggling ready: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/start', methods=['POST'])
@audit_endpoint('start_game')
def start_game(lobby_id):
    """Start the game."""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username required'}), 400
    
    try:
        logger.info(f"Host {data['username']} starting game {lobby_id}")
        game = _start_game_interactor.execute(lobby_id, data['username'])
        
        return jsonify({
            'success': True,
            'game': {
                'id': str(game.id),
                'phase': game.phase.value
            }
        })
        
    except ValueError as e:
        logger.warning(f"Error starting game: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error starting game: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>', methods=['DELETE'])
@audit_endpoint('delete_lobby')
def delete_lobby(lobby_id):
    """Delete a lobby (host only)."""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username required'}), 400
    
    try:
        logger.info(f"Deleting lobby {lobby_id}")
        success = _delete_lobby_interactor.execute(lobby_id, data['username'])
        
        if not success:
            return jsonify({'error': 'Lobby not found'}), 404
        
        return jsonify({'success': True})
        
    except ValueError as e:
        logger.warning(f"Error deleting lobby: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error deleting lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@lobby_bp.route('/encounter/save', methods=['POST'])
@audit_endpoint('save_encounter_deck')
def save_encounter_deck():
    """
    Save an encounter deck configuration with a name.
    
    Request body:
    {
        "module_names": ["Rhino", "Kree Fanatic"],
        "name": "Rhino + Kree"
    }
    
    Returns:
    {
        "success": true,
        "encounter_deck": {
            "id": "encounter_12345",
            "name": "Rhino",
            "saved_names": ["Rhino + Kree"],
            "created_at": "2026-02-12T10:30:00Z",
            "updated_at": "2026-02-12T10:30:00Z"
        }
    }
    """
    data = request.get_json()
    
    if not data or 'module_names' not in data or 'name' not in data:
        return jsonify({'error': 'module_names and name are required'}), 400
    
    module_names = data['module_names']
    name = data['name']
    
    if not isinstance(module_names, list) or not module_names:
        return jsonify({'error': 'module_names must be a non-empty list'}), 400
    
    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': 'name must be a non-empty string'}), 400
    
    try:
        logger.info(f"Saving encounter deck '{name}' with modules: {module_names}")
        encounter_deck = _save_encounter_deck_interactor.execute(
            module_names=module_names,
            save_name=name
        )
        
        return jsonify({
            'success': True,
            'encounter_deck': {
                'id': encounter_deck.id,
                'name': encounter_deck.name,
                'saved_names': list(encounter_deck.saved_names),
                'created_at': encounter_deck.created_at.isoformat() if encounter_deck.created_at else None,
                'updated_at': encounter_deck.updated_at.isoformat() if encounter_deck.updated_at else None
            }
        })
        
    except ValueError as e:
        logger.warning(f"Error saving encounter deck: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error saving encounter deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/encounter/saved', methods=['GET'])
@audit_endpoint('list_saved_encounter_decks')
def list_saved_encounter_decks():
    """
    List all saved encounter deck configurations.
    
    Returns:
    {
        "saved_decks": [
            {
                "id": "encounter_12345",
                "name": "Rhino",
                "saved_names": ["Rhino + Kree", "Standard"],
                "created_at": "2026-02-12T10:30:00Z",
                "updated_at": "2026-02-12T10:30:00Z"
            },
            ...
        ],
        "count": 5
    }
    """
    try:
        logger.info("Fetching all saved encounter decks")
        saved_decks = _list_saved_encounter_decks_interactor.execute()
        
        return jsonify({
            'saved_decks': saved_decks,
            'count': len(saved_decks)
        })
        
    except Exception as e:
        logger.error(f"Error listing saved encounter decks: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/encounter/load/<n>', methods=['GET'])
@audit_endpoint('load_saved_encounter_deck')
def load_saved_encounter_deck(name: str):
    """
    Load a saved encounter deck configuration by name and return the module names.
    
    Args:
        name: Name/alias of the saved configuration
    
    Returns:
    {
        "success": true,
        "modules": ["Rhino", "Kree Fanatic"]
    }
    
    Or:
    {
        "error": "Not found"
    } (404)
    """
    try:
        logger.info(f"Loading saved encounter deck '{name}'")
        modules = _load_saved_encounter_deck_interactor.execute(name)
        
        if modules is None:
            return jsonify({'error': 'Not found'}), 404
        
        return jsonify({
            'success': True,
            'modules': modules
        })
        
    except Exception as e:
        logger.error(f"Error loading saved encounter deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500