"""
Deck Controller - REST API endpoints for deck operations.

Endpoints:
- GET /api/decks - Get all decks
- GET /api/decks/<id> - Get deck by ID
- POST /api/decks - Create new deck
- PUT /api/decks/<id> - Update deck
- DELETE /api/decks/<id> - Delete deck
- GET /api/decks/<id>/cards - Get deck with all card details
- POST /api/decks/import - Import deck from MarvelCDB
- GET /api/decks/marvelcdb/mine - Get user's MarvelCDB decks
"""

from flask import jsonify, request
from src.controllers import deck_bp
from src.middleware import audit_endpoint
from src.interactors import DeckInteractor
from src.entities import DeckCard
import logging

logger = logging.getLogger(__name__)

_deck_interactor: DeckInteractor = None


def init_deck_controller(deck_interactor: DeckInteractor):
    """Initialize controller with interactor"""
    global _deck_interactor
    _deck_interactor = deck_interactor


@deck_bp.route('', methods=['GET'])
@audit_endpoint('list_decks')
def list_decks():
    """Get all decks"""
    try:
        logger.info("Fetching all decks")
        
        decks = _deck_interactor.get_all_decks()
        
        return jsonify({
            'decks': [
                {
                    'id': deck.id,
                    'name': deck.name,
                    'card_count': deck.total_cards(),
                    'source_url': deck.source_url
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
    """Get deck by ID"""
    try:
        logger.info(f"Fetching deck: {deck_id}")
        
        deck = _deck_interactor.get_deck(deck_id)
        
        if not deck:
            logger.warning(f"Deck not found: {deck_id}")
            return jsonify({'error': 'Deck not found'}), 404
        
        return jsonify({
            'id': deck.id,
            'name': deck.name,
            'cards': [
                {'code': c.code, 'quantity': c.quantity}
                for c in deck.cards
            ],
            'card_count': deck.total_cards(),
            'source_url': deck.source_url
        })
        
    except Exception as e:
        logger.error(f"Error fetching deck {deck_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('', methods=['POST'])
@audit_endpoint('create_deck')
def create_deck():
    """Create a new deck"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'cards' not in data:
        return jsonify({'error': 'Name and cards are required'}), 400
    
    try:
        logger.info(f"Creating deck: {data['name']}")
        
        # Convert cards to list of tuples
        cards = [(c['code'], c['quantity']) for c in data['cards']]
        
        deck = _deck_interactor.create_deck(data['name'], cards)
        
        logger.info(f"Created deck: {deck.id}")
        
        return jsonify({
            'success': True,
            'deck': {
                'id': deck.id,
                'name': deck.name,
                'card_count': deck.total_cards()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating deck: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/<deck_id>', methods=['PUT'])
@audit_endpoint('update_deck')
def update_deck(deck_id: str):
    """Update an existing deck"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    try:
        logger.info(f"Updating deck: {deck_id}")
        
        deck = _deck_interactor.get_deck(deck_id)
        if not deck:
            return jsonify({'error': 'Deck not found'}), 404
        
        # Create updated deck (immutable pattern)
        from src.entities import Deck
        updated_deck = Deck(
            id=deck.id,
            name=data.get('name', deck.name),
            cards=tuple(
                DeckCard(code=c['code'], quantity=c['quantity'])
                for c in data.get('cards', [{'code': c.code, 'quantity': c.quantity} for c in deck.cards])
            ),
            source_url=data.get('source_url', deck.source_url),
            created_at=deck.created_at
        )
        
        saved = _deck_interactor.update_deck(updated_deck)
        
        logger.info(f"Updated deck: {deck_id}")
        
        return jsonify({
            'success': True,
            'deck': {
                'id': saved.id,
                'name': saved.name,
                'card_count': saved.total_cards()
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating deck {deck_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/<deck_id>', methods=['DELETE'])
@audit_endpoint('delete_deck')
def delete_deck(deck_id: str):
    """Delete a deck"""
    try:
        logger.info(f"Deleting deck: {deck_id}")
        
        success = _deck_interactor.delete_deck(deck_id)
        
        if not success:
            return jsonify({'error': 'Deck not found'}), 404
        
        logger.info(f"Deleted deck: {deck_id}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting deck {deck_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/<deck_id>/cards', methods=['GET'])
@audit_endpoint('get_deck_cards')
def get_deck_with_cards(deck_id: str):
    """Get deck with all card details"""
    try:
        logger.info(f"Fetching deck with cards: {deck_id}")
        
        result = _deck_interactor.get_deck_with_cards(deck_id)
        
        if not result:
            return jsonify({'error': 'Deck not found'}), 404
        
        deck, cards = result
        
        return jsonify({
            'id': deck.id,
            'name': deck.name,
            'cards': [
                {
                    'code': card.code,
                    'name': card.name,
                    'text': card.text
                }
                for card in cards
            ]
        })
        
    except Exception as e:
        logger.error(f"Error fetching deck cards {deck_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/import', methods=['POST'])
@audit_endpoint('import_deck')
def import_deck():
    """Import deck from MarvelCDB"""
    data = request.get_json()
    
    if not data or 'deck_id' not in data:
        return jsonify({'error': 'deck_id is required'}), 400
    
    deck_id = data['deck_id']
    
    try:
        logger.info(f"Importing deck from MarvelCDB: {deck_id}")
        
        deck = _deck_interactor.import_deck_from_marvelcdb(deck_id)
        
        logger.info(f"Successfully imported deck: {deck.name}")
        
        return jsonify({
            'success': True,
            'deck': {
                'id': deck.id,
                'name': deck.name,
                'card_count': deck.total_cards(),
                'source_url': deck.source_url
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error importing deck {deck_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@deck_bp.route('/marvelcdb/mine', methods=['GET'])
@audit_endpoint('get_marvelcdb_decks')
def get_marvelcdb_decks():
    """Get user's decks from MarvelCDB"""
    # Expect session cookie in request
    cookie = request.headers.get('X-MarvelCDB-Cookie')
    
    if not cookie:
        return jsonify({'error': 'MarvelCDB session cookie required'}), 400
    
    try:
        logger.info("Fetching user's MarvelCDB decks")
        
        decks = _deck_interactor.get_user_decks_from_marvelcdb(cookie)
        
        return jsonify({
            'decks': decks,
            'count': len(decks)
        })
        
    except Exception as e:
        logger.error(f"Error fetching MarvelCDB decks: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500