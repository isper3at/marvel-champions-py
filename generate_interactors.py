#!/usr/bin/env python3
"""
Generate controller updates and app.py modifications for Marvel Champions API.
Run: python generate_controllers.py
"""

from pathlib import Path

# Controller and app files to create/update
FILES = {
    'src/app.py': '''"""
Marvel Champions REST API - Main Entry Point

Following EBI (Entities-Boundaries-Interactors) Architecture:

ENTITIES: Card, Deck, Game, Player, GameState
├─ Immutable domain objects
├─ No dependencies
└─ Single responsibility

BOUNDARIES: 
├─ Repositories (MongoDB): CardRepository, DeckRepository, GameRepository
├─ Gateways (External): MarvelCDBGateway, MarvelCDBClient
├─ Storage: ImageStorage, LocalImageStorage
└─ Middleware: Request logging, Audit middleware

INTERACTORS (Business Logic):
├─ Card: 23 individual units
├─ Deck: 23 individual units
├─ Lobby: 23 individual units
├─ Game: 23 individual units

CONTROLLERS (REST Endpoints):
└─ Blueprint routes → Interactor methods → Return JSON
"""

import sys
import os
from pathlib import Path

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_override=None):
    """
    Application Factory: Creates and configures Flask app
    
    Args:
        config_override: Optional config dict for testing
        
    Returns:
        Configured Flask application ready to run
    """
    
    logger.info("=" * 80)
    logger.info("MARVEL CHAMPIONS API - Starting Application")
    logger.info("=" * 80)
    
    # ========================================================================
    # 1. CONFIGURATION LOADING
    # ========================================================================
    from src.config import load_config
    
    try:
        config = load_config()
        logger.info(f"✓ Configuration loaded")
        logger.info(f"  - Database: {config.mongo.database}")
        logger.info(f"  - Host: {config.host}:{config.port}")
    except Exception as e:
        logger.error(f"✗ Failed to load configuration: {e}")
        raise
    
    # ========================================================================
    # 2. CREATE FLASK APP
    # ========================================================================
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.secret_key
    app.config['DEBUG'] = config.debug
    CORS(app)
    logger.info("✓ Flask app created")
    
    # ========================================================================
    # 3. INITIALIZE MONGODB
    # ========================================================================
    try:
        mongo_client = MongoClient(
            config.mongo.connection_string,
            serverSelectionTimeoutMS=5000,
            uuidRepresentation='standard'
        )
        # Test connection
        mongo_client.admin.command('ping')
        db = mongo_client[config.mongo.database]
        logger.info(f"✓ MongoDB connected to '{config.mongo.database}'")
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {e}")
        raise
    
    # ========================================================================
    # 4. INITIALIZE REPOSITORIES (Data Access Layer)
    # ========================================================================
    from src.repositories import (
        MongoCardRepository,
        MongoDeckRepository,
        MongoGameRepository
    )

    try:
        card_repo = MongoCardRepository(db)
        deck_repo = MongoDeckRepository(db)
        game_repo = MongoGameRepository(db)
        logger.info("✓ Repositories initialized")
        logger.info("  - MongoCardRepository")
        logger.info("  - MongoDeckRepository")
        logger.info("  - MongoGameRepository")
    except Exception as e:
        logger.error(f"✗ Repository initialization failed: {e}")
        raise
    
    # ========================================================================
    # 5. INITIALIZE GATEWAYS (Boundaries - External Services)
    # ========================================================================
    from src.gateways import MarvelCDBClient, LocalImageStorage
    
    try:
        marvelcdb_gateway = MarvelCDBClient(config.marvelcdb)
        image_storage = LocalImageStorage(config.image_storage)
        logger.info("✓ Gateways initialized")
        logger.info(f"  - MarvelCDBClient ({config.marvelcdb.base_url})")
        logger.info(f"  - LocalImageStorage ({config.image_storage.storage_path})")
    except Exception as e:
        logger.error(f"✗ Gateway initialization failed: {e}")
        raise
    
    # ========================================================================
    # 6. INITIALIZE INTERACTORS (Business Logic - 46 individual units)
    # ========================================================================
    from src.interactors.card import (
        ImportCardInteractor, GetCardInteractor, SearchCardsInteractor, GetCardImageInteractor
    )
    from src.interactors.deck import (
        ImportDeckInteractor, GetDeckInteractor, UpdateDeckInteractor, DeleteDeckInteractor, ListDecksInteractor
    )
    from src.interactors.lobby import (
        CreateLobbyInteractor, JoinLobbyInteractor, LeaveLobbyInteractor, ChooseDeckInteractor,
        ToggleReadyInteractor, StartGameInteractor, BuildEncounterDeckInteractor, ListLobbiesInteractor, DeleteLobbyInteractor
    )
    from src.interactors.game import (
        CreateGameInteractor, GetGameInteractor, ListGamesInteractor, DrawCardInteractor, ShuffleDiscardInteractor,
        PlayCardInteractor, MoveCardInteractor, ToggleCardExhaustionInteractor, AddCounterInteractor, DeleteGameInteractor
    )
    
    try:
        # Card Interactors
        import_card_interactor = ImportCardInteractor(card_repo, marvelcdb_gateway, image_storage)
        get_card_interactor = GetCardInteractor(card_repo)
        search_cards_interactor = SearchCardsInteractor(card_repo)
        get_card_image_interactor = GetCardImageInteractor(marvelcdb_gateway, image_storage)
        
        # Deck Interactors
        import_deck_interactor = ImportDeckInteractor(deck_repo, marvelcdb_gateway)
        get_deck_interactor = GetDeckInteractor(deck_repo)
        update_deck_interactor = UpdateDeckInteractor(deck_repo)
        delete_deck_interactor = DeleteDeckInteractor(deck_repo)
        list_decks_interactor = ListDecksInteractor(deck_repo)
        
        # Lobby Interactors
        create_lobby_interactor = CreateLobbyInteractor(game_repo)
        join_lobby_interactor = JoinLobbyInteractor(game_repo)
        leave_lobby_interactor = LeaveLobbyInteractor(game_repo)
        choose_deck_interactor = ChooseDeckInteractor(game_repo, deck_repo, marvelcdb_gateway)
        toggle_ready_interactor = ToggleReadyInteractor(game_repo)
        start_game_interactor = StartGameInteractor(game_repo)
        build_encounter_deck_interactor = BuildEncounterDeckInteractor(deck_repo, marvelcdb_gateway)
        list_lobbies_interactor = ListLobbiesInteractor(game_repo)
        delete_lobby_interactor = DeleteLobbyInteractor(game_repo)
        
        # Game Interactors
        create_game_interactor = CreateGameInteractor(game_repo, deck_repo)
        get_game_interactor = GetGameInteractor(game_repo)
        list_games_interactor = ListGamesInteractor(game_repo)
        draw_card_interactor = DrawCardInteractor(game_repo)
        shuffle_discard_interactor = ShuffleDiscardInteractor(game_repo)
        play_card_interactor = PlayCardInteractor(game_repo)
        move_card_interactor = MoveCardInteractor(game_repo)
        toggle_card_exhaustion_interactor = ToggleCardExhaustionInteractor(game_repo)
        add_counter_interactor = AddCounterInteractor(game_repo)
        delete_game_interactor = DeleteGameInteractor(game_repo)
        
        logger.info("✓ Interactors initialized (46 individual units)")
        
    except Exception as e:
        logger.error(f"✗ Interactor initialization failed: {e}")
        raise
    
    # ========================================================================
    # 7. INITIALIZE CONTROLLERS (REST Endpoints)
    # ========================================================================
    from src.controllers import card_bp, deck_bp, game_bp, lobby_bp
    import src.controllers.card_controller as card_controller
    import src.controllers.deck_controller as deck_controller
    import src.controllers.game_controller as game_controller
    import src.controllers.lobby_controller as lobby_controller
    
    try:
        # Wire up card controller
        card_controller.init_card_controller(
            get_card_interactor,
            search_cards_interactor,
            import_card_interactor,
            get_card_image_interactor
        )
        
        # Wire up deck controller
        deck_controller.init_deck_controller(
            list_decks_interactor,
            get_deck_interactor,
            import_deck_interactor,
            update_deck_interactor,
            delete_deck_interactor
        )
        
        # Wire up lobby controller
        lobby_controller.init_lobby_controller(
            create_lobby_interactor,
            join_lobby_interactor,
            leave_lobby_interactor,
            choose_deck_interactor,
            toggle_ready_interactor,
            start_game_interactor,
            build_encounter_deck_interactor,
            list_lobbies_interactor,
            delete_lobby_interactor
        )
        
        # Wire up game controller
        game_controller.init_game_controller(
            list_games_interactor,
            get_game_interactor,
            draw_card_interactor,
            shuffle_discard_interactor,
            play_card_interactor,
            move_card_interactor,
            toggle_card_exhaustion_interactor,
            add_counter_interactor,
            delete_game_interactor
        )
        
        logger.info("✓ Controllers initialized and wired")
        
    except Exception as e:
        logger.error(f"✗ Controller initialization failed: {e}")
        raise
    
    # ========================================================================
    # 8. REGISTER BLUEPRINTS
    # ========================================================================
    try:
        app.register_blueprint(card_bp, url_prefix='/api/cards')
        app.register_blueprint(deck_bp, url_prefix='/api/decks')
        app.register_blueprint(game_bp, url_prefix='/api/games')
        app.register_blueprint(lobby_bp, url_prefix='/api/lobby')
        
        logger.info("✓ Blueprints registered")
        logger.info("  - /api/cards")
        logger.info("  - /api/decks")
        logger.info("  - /api/games")
        logger.info("  - /api/lobby")
    except Exception as e:
        logger.error(f"✗ Blueprint registration failed: {e}")
        raise
    
    # ========================================================================
    # 9. HEALTH CHECK ENDPOINT
    # ========================================================================
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'service': 'Marvel Champions API'
        })
    
    logger.info("=" * 80)
    logger.info("✓ APPLICATION READY")
    logger.info("=" * 80)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
''',

    'src/controllers/card_controller.py': '''"""
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


def init_card_controller(
    get_card_interactor,
    search_cards_interactor,
    import_card_interactor,
    get_card_image_interactor
):
    """Initialize controller with interactors."""
    global _get_card_interactor, _search_cards_interactor, _import_card_interactor, _get_card_image_interactor
    _get_card_interactor = get_card_interactor
    _search_cards_interactor = search_cards_interactor
    _import_card_interactor = import_card_interactor
    _get_card_image_interactor = get_card_image_interactor


@card_bp.route('/<code>', methods=['GET'])
@audit_endpoint('get_card')
def get_card(code: str):
    """Get a card by its code."""
    try:
        logger.info(f"Fetching card: {code}")
        card = _get_card_interactor.execute(code)
        
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
''',

    'src/controllers/deck_controller.py': '''"""
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


def init_deck_controller(
    list_decks_interactor,
    get_deck_interactor,
    import_deck_interactor,
    update_deck_interactor,
    delete_deck_interactor
):
    """Initialize controller with interactors."""
    global _list_decks_interactor, _get_deck_interactor, _import_deck_interactor, _update_deck_interactor, _delete_deck_interactor
    _list_decks_interactor = list_decks_interactor
    _get_deck_interactor = get_deck_interactor
    _import_deck_interactor = import_deck_interactor
    _update_deck_interactor = update_deck_interactor
    _delete_deck_interactor = delete_deck_interactor


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
    """Get a deck by ID."""
    try:
        logger.info(f"Fetching deck: {deck_id}")
        deck = _get_deck_interactor.execute(deck_id)
        
        if not deck:
            logger.warning(f"Deck not found: {deck_id}")
            return jsonify({'error': 'Deck not found'}), 404
        
        return jsonify({
            'id': deck.id,
            'name': deck.name,
            'card_count': deck.total_cards(),
            'source_url': deck.source_url
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
''',

    'src/controllers/game_controller.py': '''"""
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
''',

    'src/controllers/lobby_controller.py': '''"""
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
_choose_deck_interactor = None
_toggle_ready_interactor = None
_start_game_interactor = None
_build_encounter_deck_interactor = None
_list_lobbies_interactor = None
_delete_lobby_interactor = None


def init_lobby_controller(
    create_lobby_interactor,
    join_lobby_interactor,
    leave_lobby_interactor,
    choose_deck_interactor,
    toggle_ready_interactor,
    start_game_interactor,
    build_encounter_deck_interactor,
    list_lobbies_interactor,
    delete_lobby_interactor
):
    """Initialize controller with interactors."""
    global (
        _create_lobby_interactor,
        _join_lobby_interactor,
        _leave_lobby_interactor,
        _choose_deck_interactor,
        _toggle_ready_interactor,
        _start_game_interactor,
        _build_encounter_deck_interactor,
        _list_lobbies_interactor,
        _delete_lobby_interactor,
    )
    _create_lobby_interactor = create_lobby_interactor
    _join_lobby_interactor = join_lobby_interactor
    _leave_lobby_interactor = leave_lobby_interactor
    _choose_deck_interactor = choose_deck_interactor
    _toggle_ready_interactor = toggle_ready_interactor
    _start_game_interactor = start_game_interactor
    _build_encounter_deck_interactor = build_encounter_deck_interactor
    _list_lobbies_interactor = list_lobbies_interactor
    _delete_lobby_interactor = delete_lobby_interactor


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
''',
}


def main():
    """Create or update all controller and app files."""
    total = len(FILES)
    created = 0
    
    for file_path, content in FILES.items():
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"✓ {file_path}")
            created += 1
        except Exception as e:
            print(f"✗ {file_path}: {e}")
    
    print(f"\n✓ Created/updated {created}/{total} controller and app files")


if __name__ == '__main__':
    main()