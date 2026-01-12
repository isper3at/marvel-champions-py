#!/usr/bin/env python3
"""
Marvel Champions Digital Play Application

Main application entry point that wires up all dependencies
and starts the Flask server.
"""

from flask import Flask
from config import load_config
from repositories.mongo_game_repository import MongoGameRepository
from repositories.mongo_deck_repository import MongoDeckRepository
from repositories.mongo_card_repository import MongoCardRepository
from gateways.marvelcdb_client import MarvelCDBClient
from pymongo import MongoClient


def create_app():
    """
    Application factory pattern.
    Creates and configures the Flask application.
    """
    # Load configuration
    config = load_config()
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.secret_key
    
    # Initialize MongoDB connection
    client = MongoClient(config.mongo.connection_string)
    db = client[config.mongo.database]
    
    # Initialize repositories
    card_repo = MongoCardRepository(db)
    deck_repo = MongoDeckRepository(db)
    game_repo = MongoGameRepository(db)
    
    # Initialize gateways
    marvelcdb_gateway = MarvelCDBClient(config.marvelcdb)
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
        return {'status': 'healthy', 'service': 'marvel-champions'}
    
    @app.route('/')
    def index():
        return """
<html>
<head><title>Marvel Champions</title></head>
<body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
    <h1>Marvel Champions Digital Play</h1>
    <p>Service is running!</p>
    <h2>Status</h2>
    <ul>
        <li>✅ Flask server running</li>
        <li>✅ Repositories not yet implemented</li>
        <li>⏳ Gateways not yet implemented</li>
        <li>⏳ Interactors not yet implemented</li>
    </ul>
    <h2>Next Steps</h2>
    <ol>
        <li>Install MongoDB and start it</li>
        <li>Implement repository classes</li>
        <li>Implement gateway classes</li>
        <li>Implement interactor classes</li>
        <li>Create API controllers</li>
    </ol>
</body>
</html>
"""
    
    return app


def main():
    """Main entry point"""
    config = load_config()
    app = create_app()
    
    print("=" * 60)
    print("Marvel Champions Digital Play")
    print("=" * 60)
    print(f"Starting server on {config.host}:{config.port}")
    print(f"Debug mode: {config.debug}")
    print(f"MongoDB: {config.mongo.host}:{config.mongo.port}/{config.mongo.database}")
    print()
    print(f"Visit: http://{config.host if config.host != '0.0.0.0' else 'localhost'}:{config.port}")
    print("=" * 60)
    print()
    
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug
    )


if __name__ == '__main__':
    main()
