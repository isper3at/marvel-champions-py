#!/usr/bin/env python3
"""
Marvel Champions Digital Play Application

Main application entry point that wires up all dependencies
and starts the Flask server.
"""

from flask import Flask, send_from_directory, jsonify, request
import requests
import uuid
import threading
import os
from flask_socketio import SocketIO, join_room, leave_room

# Create SocketIO instance (will be initialized with the Flask app later)
# Let Flask-SocketIO auto-detect the best async mode available instead of forcing one
socketio = SocketIO()
from config import load_config
from logging_service import initialize_logger, get_logger, LogLevel
from repositories.mongo_game_repository import MongoGameRepository
from repositories.mongo_deck_repository import MongoDeckRepository
from repositories.mongo_card_repository import MongoCardRepository
from gateways.marvelcdb_client import MarvelCDBClient
from pymongo import MongoClient

# Initialize logging early
_verbosity = os.getenv('LOG_LEVEL', 'INFO').upper()
try:
    verbosity_level = LogLevel[_verbosity]
except KeyError:
    verbosity_level = LogLevel.INFO

logger = None  # Will be initialized in create_app


def create_app():
    """
    Application factory pattern.
    Creates and configures the Flask application.
    """
    global logger
    
    # Load configuration
    config = load_config()
    
    # Initialize logging service
    logger = initialize_logger(
        app_name="marvel-champions",
        verbosity=verbosity_level,
        log_dir=os.path.join(os.getcwd(), "logs"),
        mongo_connection=config.mongo.connection_string,
        mongo_database=config.mongo.database,
        mongo_collection="logs"
    )
    logger.info("=== Marvel Champions Server Starting ===")
    logger.debug(f"Configuration: {config}")
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.secret_key
    logger.debug(f"Flask app created with secret key")

    # Initialize SocketIO (will be attached after create_app returns via init_app)
    # We'll initialize socketio at module-level and call socketio.init_app(app) below
    
    # Initialize MongoDB connection
    # Connect to Mongo if possible; if not, fall back to in-memory store for lobbies (testing/dev)
    db = None
    db_available = False
    try:
        logger.info(f"Attempting MongoDB connection: {config.mongo.host}:{config.mongo.port}")
        client = MongoClient(config.mongo.connection_string, serverSelectionTimeoutMS=2000)
        # try a quick ping
        client.admin.command('ping')
        db = client[config.mongo.database]
        lobbies_col = db['lobbies']
        db_available = True
        logger.info(f"MongoDB connected successfully: {config.mongo.database}")
    except Exception as e:
        logger.warning(f"MongoDB connection failed, using in-memory storage: {e}")
        lobbies_col = None
        db_available = False
    
    # Initialize repositories only if DB is available
    card_repo = None
    deck_repo = None
    game_repo = None
    if db_available and db is not None:
        try:
            card_repo = MongoCardRepository(db)
            deck_repo = MongoDeckRepository(db)
            game_repo = MongoGameRepository(db)
            logger.info("Repositories initialized successfully")
        except Exception as e:
            logger.error(f"Could not initialize repositories: {e}")
    
    # Initialize gateways
    marvelcdb_gateway = MarvelCDBClient(config.marvelcdb)
    logger.debug(f"MarvelCDB gateway initialized: {config.marvelcdb.base_url}")
    # image_storage = LocalImageStorage(config.image_storage)
    
    # TODO: Initialize interactors with dependency injection
    # card_interactor = CardInteractor(card_repo, marvelcdb_gateway, image_storage)
    # deck_interactor = DeckInteractor(deck_repo, card_repo, marvelcdb_gateway)
    # etc.
    
    # TODO: Register controllers (blueprints)
    # app.register_blueprint(card_controller)
    # app.register_blueprint(deck_controller)
    # etc.
    
    # Basic health check endpoint
    @app.route('/health')
    def health():
        logger.debug("Health check endpoint called")
        return {'status': 'healthy', 'service': 'marvel-champions'}
    
    @app.route('/')
    def index():
        logger.debug("Root (index) endpoint called")
        # Serve the React UI entrypoint
        return send_from_directory('static/ui', 'index.html')

    # Serve other UI static files from static/ui via /ui/<path>
    @app.route('/ui/<path:filename>')
    def ui_files(filename):
        return send_from_directory('static/ui', filename)

    # Simple proxy endpoints for MarvelCDB (limited, public proxy)
    @app.route('/api/marvelcdb/deck/<int:deck_id>')
    def proxy_deck(deck_id):
        """Proxy a deck request from MarvelCDB. Client will cache results in localStorage."""
        try:
            logger.debug(f"Fetching MarvelCDB deck: {deck_id}")
            url = f"https://marvelcdb.com/api/public/decklist/{deck_id}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"Successfully fetched deck {deck_id} with {len(result.get('cards', []))} cards")
            return jsonify(result)
        except Exception as e:
            logger.error(f"Failed to fetch deck {deck_id}: {e}")
            return jsonify({'error': str(e)}), 502

    @app.route('/api/marvelcdb/module/<module_name>')
    def proxy_module(module_name):
        """Proxy a module/pack card list request from MarvelCDB. Client will cache results in localStorage."""
        try:
            logger.debug(f"Fetching MarvelCDB module: {module_name}")
            # Try a couple of plausible endpoints; this is a best-effort proxy.
            # Primary: cards by pack name
            url = f"https://marvelcdb.com/api/public/cards?pack_name={module_name}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and resp.headers.get('Content-Type','').startswith('application/json'):
                result = resp.json()
                logger.info(f"Successfully fetched module {module_name} with {len(result)} cards (by pack name)")
                return jsonify(result)
            # Fallback: try pack code
            url2 = f"https://marvelcdb.com/api/public/cards?pack_code={module_name}"
            resp2 = requests.get(url2, timeout=10)
            resp2.raise_for_status()
            result = resp2.json()
            logger.info(f"Successfully fetched module {module_name} with {len(result)} cards (by pack code)")
            return jsonify(result)
        except Exception as e:
            logger.error(f"Failed to fetch module {module_name}: {e}")
            return jsonify({'error': str(e)}), 502

    # Simple in-memory lobby API
    def _serialize_doc(doc):
        if not doc:
            return doc
        out = {}
        for k, v in doc.items():
            # convert ObjectId to str
            try:
                from bson.objectid import ObjectId
                if isinstance(v, ObjectId):
                    out[k] = str(v)
                    continue
            except Exception:
                pass
            # convert lists and nested dicts naively
            if isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, 'to_dict'):
                        out[k].append(item.to_dict())
                    else:
                        try:
                            # try to convert ObjectId inside lists
                            from bson.objectid import ObjectId
                            if isinstance(item, ObjectId):
                                out[k].append(str(item))
                                continue
                        except Exception:
                            pass
                        out[k].append(item)
                continue
            out[k] = v
        return out
    @app.route('/api/lobby/create', methods=['POST'])
    def api_lobby_create():
        data = request.get_json() or {}
        host_name = data.get('host', 'host')
        room_id = uuid.uuid4().hex[:8]
        logger.info(f"Creating lobby: room_id={room_id}, host={host_name}")
        
        lobby_doc = {
            'id': room_id,
            'host': host_name,
            'players': [],
            'encounter_module': None,
            'started': False,
        }
        if lobbies_col is not None:
            lobbies_col.insert_one(lobby_doc)
            logger.debug(f"Lobby {room_id} inserted into MongoDB")
        else:
            # store to in-memory app config
            if 'LOBBIES' not in app.config:
                app.config['LOBBIES'] = {}
            app.config['LOBBIES'][room_id] = lobby_doc
            logger.debug(f"Lobby {room_id} stored in memory")
        # emit update to any listeners
        try:
            socketio.emit('lobby_update', lobby_doc, room=room_id)
        except Exception as e:
            logger.warning(f"Failed to emit lobby_update for {room_id}: {e}")
        return jsonify({'room': room_id})

    @app.route('/api/lobby/<room_id>/join', methods=['POST'])
    def api_lobby_join(room_id):
        lobby = lobbies_col.find_one({'id': room_id}) if lobbies_col is not None else app.config.get('LOBBIES', {}).get(room_id)
        if not lobby:
            logger.warning(f"Join attempt on non-existent lobby: {room_id}")
            return jsonify({'error': 'room not found'}), 404
        
        data = request.get_json() or {}
        player_name = data.get('name', 'player')
        player = {
            'id': uuid.uuid4().hex[:8],
            'name': player_name,
            'deck_id': data.get('deck_id'),
            'ready': False,
            'zone': {'hand': [], 'deck': [], 'discard': [], 'play': []}
        }
        logger.info(f"Player joining lobby {room_id}: player_id={player['id']}, name={player_name}")
        
        if lobbies_col is not None:
            lobbies_col.update_one({'id': room_id}, {'$push': {'players': player}})
            updated = lobbies_col.find_one({'id': room_id})
            logger.debug(f"Player {player['id']} added to MongoDB lobby {room_id}")
        else:
            app.config['LOBBIES'][room_id]['players'].append(player)
            updated = app.config['LOBBIES'][room_id]
            logger.debug(f"Player {player['id']} added to memory lobby {room_id}")
        try:
            socketio.emit('lobby_update', updated, room=room_id)
        except Exception as e:
            logger.warning(f"Failed to emit lobby_update for {room_id}: {e}")
        return jsonify(player)

    @app.route('/api/lobby/<room_id>')
    def api_lobby_get(room_id):
        logger.debug(f"Fetching lobby: {room_id}")
        lobby = lobbies_col.find_one({'id': room_id}) if lobbies_col is not None else app.config.get('LOBBIES', {}).get(room_id)
        if not lobby:
            logger.warning(f"Lobby not found: {room_id}")
            return jsonify({'error': 'room not found'}), 404
        return jsonify(_serialize_doc(lobby))

    @app.route('/api/lobby/<room_id>/set_encounter', methods=['POST'])
    def api_lobby_set_encounter(room_id):
        lobby = lobbies_col.find_one({'id': room_id}) if lobbies_col is not None else app.config.get('LOBBIES', {}).get(room_id)
        if not lobby:
            logger.warning(f"Set encounter on non-existent lobby: {room_id}")
            return jsonify({'error': 'room not found'}), 404
        data = request.get_json() or {}
        module = data.get('module')
        logger.info(f"Setting encounter for lobby {room_id}: module={module}")
        
        if lobbies_col is not None:
            lobbies_col.update_one({'id': room_id}, {'$set': {'encounter_module': module}})
            updated = lobbies_col.find_one({'id': room_id})
        else:
            app.config['LOBBIES'][room_id]['encounter_module'] = module
            updated = app.config['LOBBIES'][room_id]
        try:
            socketio.emit('lobby_update', _serialize_doc(updated), room=room_id)
        except Exception as e:
            logger.warning(f"Failed to emit lobby_update for {room_id}: {e}")
        return jsonify({'ok': True})

    @app.route('/api/lobby/<room_id>/player/<player_id>/ready', methods=['POST'])
    def api_player_ready(room_id, player_id):
        lobby = lobbies_col.find_one({'id': room_id}) if lobbies_col is not None else app.config.get('LOBBIES', {}).get(room_id)
        if not lobby:
            logger.warning(f"Ready request on non-existent lobby: {room_id}")
            return jsonify({'error': 'room not found'}), 404
        ready_val = request.get_json().get('ready', True)
        logger.info(f"Player {player_id} in lobby {room_id} set ready={ready_val}")
        
        # update embedded player's ready flag
        if lobbies_col is not None:
            lobbies_col.update_one({'id': room_id, 'players.id': player_id}, {'$set': {'players.$.ready': ready_val}})
            updated = lobbies_col.find_one({'id': room_id})
        else:
            for p in app.config['LOBBIES'][room_id]['players']:
                if p['id'] == player_id:
                    p['ready'] = ready_val
            updated = app.config['LOBBIES'][room_id]
        try:
            socketio.emit('lobby_update', _serialize_doc(updated), room=room_id)
        except Exception as e:
            logger.warning(f"Failed to emit lobby_update for {room_id}: {e}")
        return jsonify({'ok': True})

    @app.route('/api/lobby/<room_id>/start', methods=['POST'])
    def api_lobby_start(room_id):
        lobby = lobbies_col.find_one({'id': room_id}) if lobbies_col is not None else app.config.get('LOBBIES', {}).get(room_id)
        if not lobby:
            logger.warning(f"Start request on non-existent lobby: {room_id}")
            return jsonify({'error': 'room not found'}), 404
        data = request.get_json() or {}
        if data.get('host') != lobby.get('host'):
            logger.warning(f"Unauthorized start attempt on lobby {room_id}")
            return jsonify({'error': 'only host can start'}), 403
        if not all(p.get('ready') for p in lobby.get('players', [])):
            logger.warning(f"Start attempt on lobby {room_id} with unready players")
            return jsonify({'error': 'not all players ready'}), 400
        logger.info(f"Starting game in lobby {room_id} with {len(lobby.get('players', []))} players")
        
        if lobbies_col is not None:
            lobbies_col.update_one({'id': room_id}, {'$set': {'started': True}})
            updated = lobbies_col.find_one({'id': room_id})
        else:
            app.config['LOBBIES'][room_id]['started'] = True
            updated = app.config['LOBBIES'][room_id]
        try:
            socketio.emit('lobby_update', _serialize_doc(updated), room=room_id)
        except Exception as e:
            logger.warning(f"Failed to emit lobby_update for {room_id}: {e}")
        return jsonify({'ok': True})

    # Socket.IO handlers for joining/leaving real-time rooms
    @socketio.on('join_lobby')
    def on_join_lobby(data):
        room = data.get('room')
        sid = request.sid
        logger.debug(f"Socket {sid} joining room: {room}")
        join_room(room)
        lobby = lobbies_col.find_one({'id': room}) if lobbies_col is not None else app.config.get('LOBBIES', {}).get(room)
        if lobby:
            socketio.emit('lobby_update', lobby, room=room)

    @socketio.on('leave_lobby')
    def on_leave_lobby(data):
        room = data.get('room')
        logger.debug(f"Socket leaving room: {room}")
        leave_room(room)
    
    logger.info("Flask app configured successfully")
    return app


def main():
    """Main entry point"""
    config = load_config()
    app = create_app()
    
    # Attach socketio to the flask app
    socketio.init_app(app)
    
    # Get logger instance
    log = get_logger()
    
    log.info("=" * 60)
    log.info("Marvel Champions Digital Play")
    log.info("=" * 60)
    log.info(f"Starting server on {config.host}:{config.port}")
    log.info(f"Debug mode: {config.debug}")
    log.info(f"MongoDB: {config.mongo.host}:{config.mongo.port}/{config.mongo.database}")
    log.info(f"Log level: {_verbosity}")
    log.info(f"Log file: logs/marvel-champions_{log.get_session_id()}.log")
    log.info("")
    log.info(f"Visit: http://{config.host if config.host != '0.0.0.0' else 'localhost'}:{config.port}")
    log.info("=" * 60)
    log.info("")
    
    # Use socketio.run for production-ready event loop support (eventlet/gevent)
    try:
        socketio.run(app, host=config.host, port=config.port, debug=config.debug)
    except KeyboardInterrupt:
        log.info("Server shutdown requested (KeyboardInterrupt)")
    except Exception as e:
        log.critical(f"Server error: {e}")
        raise
    finally:
        log.info("Server shutdown complete")


if __name__ == '__main__':
    main()
