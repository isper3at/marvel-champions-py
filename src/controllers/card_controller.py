"""
Card Controller - REST API endpoints for card operations.

Endpoints:
- GET /api/cards/<code> - Get card by code
- GET /api/cards/search?q=<query> - Search cards
- POST /api/cards/import - Import card from MarvelCDB
- POST /api/cards/import/bulk - Import multiple cards
- GET /api/cards/<code>/image - Get card image
"""

from flask import jsonify, request, send_file
from src.controllers import card_bp
from src.middleware import audit_endpoint
from src.interactors import CardInteractor
import logging

logger = logging.getLogger(__name__)


# These will be injected by the app factory
_card_interactor: CardInteractor = None


def init_card_controller(card_interactor: CardInteractor):
    """Initialize controller with interactor (dependency injection)"""
    global _card_interactor
    _card_interactor = card_interactor


@card_bp.route('/<code>', methods=['GET'])
@audit_endpoint('get_card')
def get_card(code: str):
    """Get a card by its code"""
    try:
        logger.info(f"Fetching card: {code}")
        
        card = _card_interactor.get_card(code)
        
        if not card:
            logger.warning(f"Card not found: {code}")
            return jsonify({'error': 'Card not found'}), 404
        
        return jsonify({
            'code': card.code,
            'name': card.name,
            'text': card.text
        })
        
    except Exception as e:
        logger.error(f"Error fetching card {code}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@card_bp.route('/search', methods=['GET'])
@audit_endpoint('search_cards')
def search_cards():
    """Search for cards by name"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        logger.info(f"Searching cards: {query}")
        
        cards = _card_interactor.search_cards(query)
        
        return jsonify({
            'results': [
                {
                    'code': card.code,
                    'name': card.name,
                    'text': card.text
                }
                for card in cards
            ],
            'count': len(cards)
        })
        
    except Exception as e:
        logger.error(f"Error searching cards: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@card_bp.route('/import', methods=['POST'])
@audit_endpoint('import_card')
def import_card():
    """Import a card from MarvelCDB"""
    data = request.get_json()
    
    if not data or 'code' not in data:
        return jsonify({'error': 'Card code is required'}), 400
    
    code = data['code']
    
    try:
        logger.info(f"Importing card from MarvelCDB: {code}")
        
        card = _card_interactor.import_card_from_marvelcdb(code)
        
        logger.info(f"Successfully imported card: {card.name}")
        
        return jsonify({
            'success': True,
            'card': {
                'code': card.code,
                'name': card.name,
                'text': card.text
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error importing card {code}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@card_bp.route('/import/bulk', methods=['POST'])
@audit_endpoint('import_cards_bulk')
def import_cards_bulk():
    """Import multiple cards from MarvelCDB"""
    data = request.get_json()
    
    if not data or 'codes' not in data:
        return jsonify({'error': 'Card codes array is required'}), 400
    
    codes = data['codes']
    
    if not isinstance(codes, list):
        return jsonify({'error': 'Codes must be an array'}), 400
    
    try:
        logger.info(f"Bulk importing {len(codes)} cards")
        
        cards = _card_interactor.import_cards_bulk(codes)
        
        logger.info(f"Successfully imported {len(cards)} cards")
        
        return jsonify({
            'success': True,
            'imported': len(cards),
            'cards': [
                {
                    'code': card.code,
                    'name': card.name,
                    'text': card.text
                }
                for card in cards
            ]
        }), 201
        
    except Exception as e:
        logger.error(f"Error bulk importing cards: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@card_bp.route('/<code>/image', methods=['GET'])
def get_card_image(code: str):
    """Get card image (no audit - too frequent)"""
    try:
        image_path = _card_interactor.get_card_image_path(code)
        
        if not image_path:
            logger.debug(f"Image not found for card: {code}")
            return jsonify({'error': 'Image not found'}), 404
        
        return send_file(image_path, mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Error fetching image for {code}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500