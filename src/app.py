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
        ImportCardInteractor, GetCardInteractor, SearchCardsInteractor, GetCardImageInteractor, SaveCardInteractor
    )
    from src.interactors.deck import (
        ImportDeckInteractor, GetDeckInteractor, UpdateDeckInteractor, DeleteDeckInteractor, ListDecksInteractor, SaveDeckInteractor
    )
    from src.interactors.lobby import (
        CreateLobbyInteractor, JoinLobbyInteractor, LeaveLobbyInteractor, GetLobbyInteractor, ChooseDeckInteractor,
        ToggleReadyInteractor, StartGameInteractor, BuildEncounterDeckInteractor, ListLobbiesInteractor, DeleteLobbyInteractor,
        ListSavedEncounterDecksInteractor, LoadSavedEncounterDeckInteractor
    )
    from src.interactors.game import (
        CreateGameInteractor, GetGameInteractor, ListGamesInteractor, DrawCardInteractor, ShuffleDiscardInteractor,
        PlayCardInteractor, MoveCardInteractor, ToggleCardExhaustionInteractor, AddCounterInteractor, DeleteGameInteractor
    )
    
    try:
        # Card Interactors
        import_card_interactor = ImportCardInteractor(marvelcdb_gateway, image_storage)
        get_card_interactor = GetCardInteractor(card_repo)
        search_cards_interactor = SearchCardsInteractor(card_repo)
        get_card_image_interactor = GetCardImageInteractor(marvelcdb_gateway, image_storage)
        save_card_interactor = SaveCardInteractor(card_repo)
        
        # Deck Interactors
        import_deck_interactor = ImportDeckInteractor(marvelcdb_gateway)
        get_deck_interactor = GetDeckInteractor(deck_repo)
        update_deck_interactor = UpdateDeckInteractor(deck_repo)
        delete_deck_interactor = DeleteDeckInteractor(deck_repo)
        list_decks_interactor = ListDecksInteractor(deck_repo)
        save_deck_interactor = SaveDeckInteractor(deck_repo)
        
        # Lobby Interactors
        create_lobby_interactor = CreateLobbyInteractor(game_repo)
        join_lobby_interactor = JoinLobbyInteractor(game_repo)
        leave_lobby_interactor = LeaveLobbyInteractor(game_repo)
        get_lobby_interactor = GetLobbyInteractor(game_repo)
        choose_deck_interactor = ChooseDeckInteractor(game_repo, deck_repo, marvelcdb_gateway)
        toggle_ready_interactor = ToggleReadyInteractor(game_repo)
        start_game_interactor = StartGameInteractor(game_repo)
        build_encounter_deck_interactor = BuildEncounterDeckInteractor(deck_repo, marvelcdb_gateway)
        list_lobbies_interactor = ListLobbiesInteractor(game_repo)
        delete_lobby_interactor = DeleteLobbyInteractor(game_repo)
        save_encounter_deck_interactor = SaveDeckInteractor(deck_repo),
        list_saved_encounter_decks_interactor = ListSavedEncounterDecksInteractor(deck_repo),
        load_saved_encounter_deck_interactor = LoadSavedEncounterDeckInteractor(deck_repo)
        
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
            get_card_image_interactor,
            save_card_interactor
        )
        
        # Wire up deck controller
        deck_controller.init_deck_controller(
            list_decks_interactor,
            get_deck_interactor,
            import_deck_interactor,
            update_deck_interactor,
            delete_deck_interactor,
            save_deck_interactor
        )
        
        # Wire up lobby controller
        lobby_controller.init_lobby_controller(
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
