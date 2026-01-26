"""
Lobby Controller - REST API endpoints for lobby operations.

Endpoints:
- POST /api/lobby - Create new lobby
- GET /api/lobby - List all lobbies
- GET /api/lobby/<id> - Get lobby details
- POST /api/lobby/<id>/join - Join lobby
- POST /api/lobby/<id>/leave - Leave lobby
- PUT /api/lobby/<id>/deck - Choose deck
- PUT /api/lobby/<id>/encounter - Set encounter deck
- POST /api/lobby/<id>/ready - Toggle ready
- POST /api/lobby/<id>/start - Start game
- DELETE /api/lobby/<id> - Delete lobby
"""

from flask import Blueprint, jsonify, request
from src.middleware import audit_endpoint
from src.interactors import LobbyInteractor
from src.entities import GameStatus
import logging

logger = logging.getLogger(__name__)

# Create blueprint
lobby_bp = Blueprint('lobby', __name__, url_prefix='/api/lobby')

_lobby_interactor: LobbyInteractor = None


def init_lobby_controller(lobby_interactor: LobbyInteractor):
    """Initialize controller with interactor"""
    global _lobby_interactor
    _lobby_interactor = lobby_interactor


@lobby_bp.route('', methods=['POST'])
@audit_endpoint('create_lobby')
def create_lobby():
    """Create a new game lobby"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'username' not in data:
        return jsonify({'error': 'name and username are required'}), 400
    
    try:
        logger.info(f"Creating lobby: {data['name']} (host: {data['username']})")
        
        game = _lobby_interactor.create_lobby(data['name'], data['username'])
        
        logger.info(f"Lobby created: {game.id}")
        
        return jsonify({
            'success': True,
            'lobby': {
                'id': game.id,
                'name': game.name,
                'status': game.phase.value,
                'host': game.host,
                'players': [
                    {
                        'username': p.username,
                        'deck_id': p.deck_id,
                        'is_ready': p.is_ready,
                        'is_host': p.is_host
                    }
                    for p in game.lobby_players
                ],
                'encounter_deck_id': game.encounter_deck_id
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('', methods=['GET'])
@audit_endpoint('list_lobbies')
def list_lobbies():
    """List all active lobbies"""
    try:
        logger.info("Listing lobbies")
        
        lobbies = _lobby_interactor.list_lobbies()
        
        return jsonify({
            'lobbies': [
                {
                    'id': game.id,
                    'name': game.name,
                    'host': game.host,
                    'player_count': len(game.lobby_players),
                    'players': [p.username for p in game.lobby_players],
                    'has_encounter': game.encounter_deck_id is not None,
                    'all_ready': game.all_players_ready()
                }
                for game in lobbies
            ],
            'count': len(lobbies)
        })
        
    except Exception as e:
        logger.error(f"Error listing lobbies: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>', methods=['GET'])
@audit_endpoint('get_lobby')
def get_lobby(lobby_id: str):
    """Get lobby details"""
    try:
        logger.info(f"Getting lobby: {lobby_id}")
        
        game = _lobby_interactor.get_lobby(lobby_id)
        
        if not game:
            return jsonify({'error': 'Lobby not found'}), 404
        
        return jsonify({
            'id': game.id,
            'name': game.name,
            'status': game.phase.value,
            'host': game.host,
            'players': [
                {
                    'username': p.username,
                    'deck_id': p.deck_id,
                    'is_ready': p.is_ready,
                    'is_host': p.is_host
                }
                for p in game.lobby_players
            ],
            'encounter_deck_id': game.encounter_deck_id,
            'all_ready': game.all_players_ready(),
            'can_start': game.can_start()
        })
        
    except Exception as e:
        logger.error(f"Error getting lobby {lobby_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/join', methods=['POST'])
@audit_endpoint('join_lobby')
def join_lobby(lobby_id: str):
    """Join a lobby"""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username is required'}), 400
    
    try:
        logger.info(f"Player {data['username']} joining lobby {lobby_id}")
        
        game = _lobby_interactor.join_lobby(lobby_id, data['username'])
        
        logger.info(f"Player joined: {data['username']}")
        
        return jsonify({
            'success': True,
            'lobby': {
                'id': game.id,
                'players': [
                    {
                        'username': p.username,
                        'deck_id': p.deck_id,
                        'is_ready': p.is_ready,
                        'is_host': p.is_host
                    }
                    for p in game.lobby_players
                ]
            }
        })
        
    except ValueError as e:
        logger.warning(f"Failed to join lobby: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error joining lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/leave', methods=['POST'])
@audit_endpoint('leave_lobby')
def leave_lobby(lobby_id: str):
    """Leave a lobby"""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username is required'}), 400
    
    try:
        logger.info(f"Player {data['username']} leaving lobby {lobby_id}")
        
        game = _lobby_interactor.leave_lobby(lobby_id, data['username'])
        
        if not game:
            # Lobby was deleted (host left or last player)
            logger.info(f"Lobby {lobby_id} deleted")
            return jsonify({'success': True, 'lobby_deleted': True})
        
        logger.info(f"Player left: {data['username']}")
        
        return jsonify({
            'success': True,
            'lobby_deleted': False
        })
        
    except Exception as e:
        logger.error(f"Error leaving lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/deck', methods=['PUT'])
@audit_endpoint('choose_deck')
def choose_deck(lobby_id: str):
    """Choose a deck for the game"""
    data = request.get_json()
    
    required = ['username', 'deck_id']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {", ".join(required)}'}), 400
    
    try:
        logger.info(f"Player {data['username']} choosing deck {data['deck_id']}")
        
        game = _lobby_interactor.choose_deck(
            lobby_id,
            data['username'],
            data['deck_id']
        )
        
        logger.info(f"Deck chosen: {data['deck_id']}")
        
        return jsonify({
            'success': True,
            'player': {
                'username': data['username'],
                'deck_id': data['deck_id']
            }
        })
        
    except ValueError as e:
        logger.warning(f"Failed to choose deck: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error choosing deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/encounter', methods=['PUT'])
@audit_endpoint('set_encounter_deck')
def set_encounter_deck(lobby_id: str):
    """Set the encounter deck (host only)"""
    data = request.get_json()
    
    required = ['username', 'encounter_deck_id']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {", ".join(required)}'}), 400
    
    try:
        logger.info(f"Setting encounter deck {data['encounter_deck_id']}")
        
        game = _lobby_interactor.set_encounter_deck(
            lobby_id,
            data['username'],
            data['encounter_deck_id']
        )
        
        logger.info(f"Encounter deck set: {data['encounter_deck_id']}")
        
        return jsonify({
            'success': True,
            'encounter_deck_id': data['encounter_deck_id']
        })
        
    except ValueError as e:
        logger.warning(f"Failed to set encounter deck: {e}")
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"Error setting encounter deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/ready', methods=['POST'])
@audit_endpoint('toggle_ready')
def toggle_ready(lobby_id: str):
    """Toggle ready status"""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username is required'}), 400
    
    try:
        logger.info(f"Player {data['username']} toggling ready")
        
        game = _lobby_interactor.toggle_ready(lobby_id, data['username'])
        
        player = game.get_lobby_player(data['username'])
        
        logger.info(f"Player ready status: {player.is_ready}")
        
        return jsonify({
            'success': True,
            'player': {
                'username': player.username,
                'is_ready': player.is_ready
            },
            'all_ready': game.all_players_ready()
        })
        
    except ValueError as e:
        logger.warning(f"Failed to toggle ready: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error toggling ready: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>/start', methods=['POST'])
@audit_endpoint('start_game')
def start_game(lobby_id: str):
    """Start the game (host only)"""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username is required'}), 400
    
    try:
        logger.info(f"Host {data['username']} starting game {lobby_id}")
        
        game = _lobby_interactor.start_game(lobby_id, data['username'])
        
        logger.info(f"Game started: {game.id} (status: {game.phase.value})")
        
        return jsonify({
            'success': True,
            'game_id': game.id,
            'status': game.phase.value,
            'players': [p.player_name for p in game.state.players]
        })
        
    except ValueError as e:
        logger.warning(f"Failed to start game: {e}")
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"Error starting game: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lobby_bp.route('/<lobby_id>', methods=['DELETE'])
@audit_endpoint('delete_lobby')
def delete_lobby(lobby_id: str):
    """Delete a lobby (host only)"""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'username is required'}), 400
    
    try:
        logger.info(f"Deleting lobby {lobby_id}")
        
        success = _lobby_interactor.delete_lobby(lobby_id, data['username'])
        
        if not success:
            return jsonify({'error': 'Lobby not found'}), 404
        
        logger.info(f"Lobby deleted: {lobby_id}")
        
        return jsonify({'success': True})
        
    except ValueError as e:
        logger.warning(f"Failed to delete lobby: {e}")
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"Error deleting lobby: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# Export blueprint
__all__ = ['lobby_bp', 'init_lobby_controller']