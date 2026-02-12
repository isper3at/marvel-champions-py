"""
Deck Controller - REST API endpoints for deck operations.

Endpoints:
- GET /api/decks - Get all decks
- GET /api/decks/<id> - Get deck by ID
- POST /api/decks - Create/import new deck
- PUT /api/decks/<id> - Update deck
- DELETE /api/decks/<id> - Delete deck
"""

from flask import jsonify, request
from src.controllers import deck_bp
from src.middleware import audit_endpoint
import logging

logger = logging.getLogger(__name__)

# Global interactors
_list_decks_interactor = None
_get_deck_interactor = None
_import_deck_interactor = None
_update_deck_interactor = None
_delete_deck_interactor = None
_save_deck_interactor = None

def init_deck_controller(
    list_decks_interactor,
    get_deck_interactor,
    import_deck_interactor,
    update_deck_interactor,
    delete_deck_interactor,
    save_deck_interactor
):
    """Initialize controller with interactors."""
    global _list_decks_interactor, _get_deck_interactor, _import_deck_interactor, _update_deck_interactor, _delete_deck_interactor, _save_deck_interactor
    _list_decks_interactor = list_decks_interactor
    _get_deck_interactor = get_deck_interactor
    _import_deck_interactor = import_deck_interactor
    _update_deck_interactor = update_deck_interactor
    _delete_deck_interactor = delete_deck_interactor
    _save_deck_interactor = save_deck_interactor



@deck_bp.route('', methods=['GET'])
@audit_endpoint('list_decks')
def list_decks():
    """Get all decks."""
    try:
        logger.info("Fetching all decks")
        decks = _list_decks_interactor.execute()
        
        return jsonify({
            'decks': [
                {
                    'id': deck.id,
                    'name': deck.name,
                    'card_count': deck.card_count(),
                    'source_url': f"https://marvelcdb.com/deck/view/{deck.id}"
                }
                for deck in decks
            ],
            'count': len(decks)
        })
        
    except Exception as e:
        logger.error(f"Error listing decks: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/<deck_id>', methods=['GET'])
@audit_endpoint('get_deck')
def get_deck(deck_id: str):
    """Get a deck by ID. If the deck is not found locally, attempt to import from MarvelCDB, then save it locally."""
    try:
        logger.info(f"Fetching deck: {deck_id}")
        deck = _get_deck_interactor.execute(deck_id)
        
        if not deck:
            logger.warning(f"Deck not found, importing from marvelcdb: {deck_id}")
            deck = _import_deck_interactor.execute(deck_id)

            _save_deck_interactor.execute(deck)

            if not deck:
                logger.warning(f"Deck not found in MarvelCDB: {deck_id}")
                return jsonify({'error': 'Deck not found'}), 404
        
        return jsonify({
            'id': deck.id,
            'name': deck.name,
            'cards': deck.cards,
        })
        
    except Exception as e:
        logger.error(f"Error fetching deck {deck_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/import', methods=['POST'])
@audit_endpoint('import_deck')
def import_deck():
    """Import a deck from MarvelCDB."""
    data = request.get_json()
    
    if not data or 'deck_id' not in data:
        return jsonify({'error': 'deck_id required'}), 400
    
    try:
        logger.info(f"Importing deck: {data['deck_id']}")
        deck = _import_deck_interactor.execute(data['deck_id'])
        
        return jsonify({
            'success': True,
            'deck': {
                'id': deck.id,
                'name': deck.name,
                'card_count': deck.total_cards()
            }
        })
        
    except Exception as e:
        logger.error(f"Error importing deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/<deck_id>', methods=['PUT'])
@audit_endpoint('update_deck')
def update_deck(deck_id: str):
    """Update a deck."""
    data = request.get_json()
    
    try:
        logger.info(f"Updating deck: {deck_id}")
        deck = _get_deck_interactor.execute(deck_id)
        
        if not deck:
            return jsonify({'error': 'Deck not found'}), 404
        
        # Update deck fields (simplified - adapt as needed)
        if 'name' in data:
            from dataclasses import replace
            deck = replace(deck, name=data['name'])
        
        updated_deck = _update_deck_interactor.execute(deck)
        
        return jsonify({
            'success': True,
            'deck': {
                'id': updated_deck.id,
                'name': updated_deck.name
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/<deck_id>', methods=['DELETE'])
@audit_endpoint('delete_deck')
def delete_deck(deck_id: str):
    """Delete a deck."""
    try:
        logger.info(f"Deleting deck: {deck_id}")
        success = _delete_deck_interactor.execute(deck_id)
        
        if not success:
            return jsonify({'error': 'Deck not found'}), 404
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
