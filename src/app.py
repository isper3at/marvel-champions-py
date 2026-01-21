"""
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
├─ CardInteractor: Card import, caching, image management
├─ DeckInteractor: Deck CRUD, MarvelCDB import
└─ GameInteractor: Game state, player actions, card movement

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
            serverSelectionTimeoutMS=5000
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
    # 6. INITIALIZE INTERACTORS (Business Logic)
    # ========================================================================
    from src.interactors import (
        CardInteractor,
        DeckInteractor,
        GameInteractor,
        LobbyInteractor
    )
    
    try:
        card_interactor = CardInteractor(
            card_repo,
            marvelcdb_gateway,
            image_storage
        )
        deck_interactor = DeckInteractor(
            deck_repo,
            card_interactor,
            marvelcdb_gateway
        )
        game_interactor = GameInteractor(game_repo, card_repo)
        lobby_interactor = LobbyInteractor(game_repo, deck_repo)
        
        logger.info("✓ Interactors initialized")
        logger.info("  - CardInteractor")
        logger.info("  - DeckInteractor")
        logger.info("  - GameInteractor")
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
        # Wire up controllers with interactors
        card_controller.init_card_controller(card_interactor)
        deck_controller.init_deck_controller(deck_interactor)
        game_controller.init_game_controller(game_interactor)
        lobby_controller.init_lobby_controller(lobby_interactor)
        
        # Register blueprints
        app.register_blueprint(card_bp)
        app.register_blueprint(deck_bp)
        app.register_blueprint(game_bp)
        app.register_blueprint(lobby_controller.lobby_bp)
        
        logger.info("✓ Controllers initialized and blueprints registered")
        logger.info("  - /api/cards")
        logger.info("  - /api/decks")
        logger.info("  - /api/games")
    except Exception as e:
        logger.error(f"✗ Controller initialization failed: {e}")
        raise
    
    # ========================================================================
    # 8. SETUP MIDDLEWARE
    # ========================================================================
    from src.middleware import setup_request_logging
    from src.api_documentation import setup_api_documentation
    from src.swagger_ui import init_swagger_ui
    
    try:
        setup_request_logging(app)
        setup_api_documentation(app)
        init_swagger_ui(app)
        logger.info("✓ Middleware and documentation initialized")
        logger.info("  - Request logging")
        logger.info("  - API documentation")
        logger.info("  - Swagger UI")
    except Exception as e:
        logger.error(f"✗ Middleware initialization failed: {e}")
        raise
    
    # ========================================================================
    # 9. DEFINE HEALTH CHECK & ROOT ENDPOINTS
    # ========================================================================
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring"""
        return jsonify({
            'status': 'ok',
            'service': 'marvel-champions-api',
            'version': '1.0.0'
        })
    
    @app.route('/', methods=['GET'])
    def index():
        """API root endpoint"""
        return jsonify({
            'service': 'marvel-champions-api',
            'version': '1.0.0',
            'docs': '/api/docs',
            'health': '/health',
            'endpoints': {
                'cards': '/api/cards',
                'decks': '/api/decks',
                'games': '/api/games'
            }
        })
    
    # ========================================================================
    # 10. ERROR HANDLERS
    # ========================================================================
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({'error': 'Not found', 'status': 404}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'status': 500
        }), 500
    
    # Shutdown endpoint for graceful server termination
    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        """Gracefully shutdown the server"""
        logger.info("=" * 80)
        logger.info("SHUTDOWN REQUESTED - Terminating server gracefully")
        logger.info("=" * 80)
        
        def do_shutdown():
            import time
            time.sleep(0.5)  # Give time to send response
            os.kill(os.getpid(), 15)  # Send SIGTERM to self
        
        from threading import Thread
        shutdown_thread = Thread(target=do_shutdown)
        shutdown_thread.daemon = True
        shutdown_thread.start()
        
        return jsonify({'status': 'shutdown initiated'}), 200
    
    logger.info("=" * 80)
    logger.info("✓ APPLICATION INITIALIZED SUCCESSFULLY")
    logger.info("=" * 80)
    
    return app


if __name__ == '__main__':
    from src.config import load_config
    
    config = load_config()
    app = create_app()
    
    logger.info(f"\n🚀 Starting server on {config.host}:{config.port}\n")
    logger.info("Visit:")
    logger.info(f"  - API Docs: http://{config.host}:{config.port}/api/docs")
    logger.info(f"  - API Root: http://{config.host}:{config.port}/")
    logger.info(f"  - Health:   http://{config.host}:{config.port}/health")
    logger.info("\nPress Ctrl+C to stop\n")
    
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug,
        use_reloader=config.debug
    )
