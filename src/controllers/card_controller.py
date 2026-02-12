"""
Card Controller - REST API endpoints for card operations.

Endpoints:
- GET /api/cards/<code> - Get card by code
- GET /api/cards/search?q=<query> - Search cards
- POST /api/cards/import - Import card from MarvelCDB
- GET /api/cards/<code>/image - Get card image
"""

from flask import jsonify, request, send_file
from src.controllers import card_bp
from src.middleware import audit_endpoint
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# Global interactors
_get_card_interactor = None
_search_cards_interactor = None
_import_card_interactor = None
_get_card_image_interactor = None
_save_card_interactor = None


def init_card_controller(
    get_card_interactor,
    search_cards_interactor,
    import_card_interactor,
    get_card_image_interactor,
    save_card_interactor
):
    """Initialize controller with interactors."""
    global _get_card_interactor, _search_cards_interactor, _import_card_interactor, _get_card_image_interactor, _save_card_interactor
    _get_card_interactor = get_card_interactor
    _search_cards_interactor = search_cards_interactor
    _import_card_interactor = import_card_interactor
    _get_card_image_interactor = get_card_image_interactor
    _save_card_interactor = save_card_interactor


@card_bp.route('/<code>', methods=['GET'])
@audit_endpoint('get_card')
def get_card(code: str):
    """Get a card by its code."""
    try:
        logger.info(f"Fetching card: {code}")
        card = _get_card_interactor.execute(code)
        
        if not card:
            logger.warning(f"Card not found: {code}, importing....")

            card = _import_card_interactor.execute(code)
            _save_card_interactor.execute(card)
            if not card:
                logger.warning(f"Card not found in MarvelCDB: {code}")
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
    """Search for cards by name."""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    try:
        logger.info(f"Searching cards: {query}")
        results = _search_cards_interactor.execute(query)
        
        return jsonify({
            'results': [
                {'code': c.code, 'name': c.name}
                for c in results
            ],
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error searching cards: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@card_bp.route('/import', methods=['POST'])
@audit_endpoint('import_card')
def import_card():
    """Import a card from MarvelCDB."""
    data = request.get_json()
    
    if not data or 'code' not in data:
        return jsonify({'error': 'Card code required'}), 400
    
    try:
        logger.info(f"Importing card: {data['code']}")
        card = _import_card_interactor.execute(data['code'])
        
        return jsonify({
            'success': True,
            'card': {
                'code': card.code,
                'name': card.name,
                'text': card.text
            }
        })
        
    except Exception as e:
        logger.error(f"Error importing card: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@card_bp.route('/<code>/image', methods=['GET'])
@audit_endpoint('get_card_image')
def get_card_image(code: str):
    """Get card image."""
    try:
        logger.info(f"Fetching card image: {code}")
        image = _get_card_image_interactor.execute(code)
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        img_io = BytesIO()
        image.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        logger.error(f"Error fetching card image {code}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
