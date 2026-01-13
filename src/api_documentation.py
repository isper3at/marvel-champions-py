"""
OpenAPI/Swagger documentation for Marvel Champions API.

This module provides structured API documentation using Flask-RESTX
which automatically generates OpenAPI/Swagger specifications.
"""

from flask import Flask
from flask_restx import Api, Resource, fields, Namespace
from typing import Dict, Any, List


def setup_api_documentation(app: Flask) -> Api:
    """
    Setup OpenAPI/Swagger documentation for the Flask app.
    
    Returns:
        Api: Flask-RESTX API instance configured with documentation
    """
    api = Api(
        app,
        version='1.0',
        title='Marvel Champions API',
        description='RESTful API for Marvel Champions digital play application',
        doc='/api/docs',
        prefix='/api'
    )
    
    # Define namespaces
    cards_ns = Namespace('cards', description='Card operations')
    decks_ns = Namespace('decks', description='Deck operations')
    games_ns = Namespace('games', description='Game operations')
    
    # Add namespaces to API
    api.add_namespace(cards_ns, path='/cards')
    api.add_namespace(decks_ns, path='/decks')
    api.add_namespace(games_ns, path='/games')
    
    # Define data models for documentation
    setup_card_models(api, cards_ns)
    setup_deck_models(api, decks_ns)
    setup_game_models(api, games_ns)
    
    return api


def setup_card_models(api: Api, ns: Namespace) -> None:
    """Define Card-related models and endpoints"""
    
    card_model = api.model('Card', {
        'code': fields.String(required=True, description='Unique card code'),
        'name': fields.String(required=True, description='Card name'),
        'cost': fields.Integer(description='Card cost'),
        'type': fields.String(description='Card type (Hero, Ally, Support, etc.)'),
        'text': fields.String(description='Card text/effects'),
        'set_id': fields.String(description='Set ID from MarvelCDB')
    })
    
    @ns.route('/<string:code>')
    class CardResource(Resource):
        @ns.doc('get_card')
        @ns.marshal_with(card_model)
        def get(self, code):
            """Get a card by its code"""
            pass
    
    @ns.route('/')
    class CardListResource(Resource):
        @ns.doc('search_cards', params={'q': 'Search query'})
        def get(self):
            """Search for cards"""
            pass


def setup_deck_models(api: Api, ns: Namespace) -> None:
    """Define Deck-related models and endpoints"""
    
    deck_card_model = api.model('DeckCard', {
        'code': fields.String(required=True, description='Card code'),
        'name': fields.String(required=True, description='Card name'),
        'quantity': fields.Integer(required=True, description='Number of copies')
    })
    
    deck_model = api.model('Deck', {
        'id': fields.String(description='Deck ID'),
        'name': fields.String(required=True, description='Deck name'),
        'hero_code': fields.String(required=True, description='Hero card code'),
        'cards': fields.List(fields.Nested(deck_card_model)),
        'created_at': fields.DateTime(description='Creation timestamp'),
        'updated_at': fields.DateTime(description='Last update timestamp')
    })
    
    @ns.route('/')
    class DeckListResource(Resource):
        @ns.doc('list_decks')
        @ns.marshal_list_with(deck_model)
        def get(self):
            """List all decks
            
            Returns:
                List of all available decks with full card information
            """
            pass
        
        @ns.doc('create_deck')
        @ns.expect(deck_model)
        @ns.marshal_with(deck_model, code=201)
        def post(self):
            """Create a new deck
            
            Args:
                name: Deck name
                hero_code: Hero card code
                cards: List of cards in deck
            
            Returns:
                Created deck object with ID
            """
            pass
    
    @ns.route('/<string:deck_id>')
    class DeckResource(Resource):
        @ns.doc('get_deck')
        @ns.marshal_with(deck_model)
        def get(self, deck_id):
            """Get a specific deck by ID"""
            pass
        
        @ns.doc('update_deck')
        @ns.expect(deck_model)
        @ns.marshal_with(deck_model)
        def put(self, deck_id):
            """Update a deck"""
            pass
        
        @ns.doc('delete_deck')
        @ns.response(204, 'Deck deleted')
        def delete(self, deck_id):
            """Delete a deck"""
            pass
    
    @ns.route('/<string:deck_id>/cards')
    class DeckCardsResource(Resource):
        @ns.doc('get_deck_cards')
        def get(self, deck_id):
            """Get detailed card information for a deck"""
            pass


def setup_game_models(api: Api, ns: Namespace) -> None:
    """Define Game-related models and endpoints"""
    
    player_zone_model = api.model('PlayerZone', {
        'deck': fields.List(fields.String, description='Cards in deck'),
        'hand': fields.List(fields.String, description='Cards in hand'),
        'play': fields.List(fields.String, description='Cards in play'),
        'discard': fields.List(fields.String, description='Cards in discard')
    })
    
    game_state_model = api.model('GameState', {
        'current_player': fields.Integer(description='Current player index'),
        'round': fields.Integer(description='Current round number'),
        'players': fields.List(fields.Nested(player_zone_model))
    })
    
    game_model = api.model('Game', {
        'id': fields.String(description='Game ID'),
        'name': fields.String(required=True, description='Game name'),
        'players': fields.List(fields.String, description='Player names'),
        'state': fields.Nested(game_state_model),
        'created_at': fields.DateTime(description='Creation timestamp'),
        'updated_at': fields.DateTime(description='Last update timestamp')
    })
    
    @ns.route('/')
    class GameListResource(Resource):
        @ns.doc('list_games')
        @ns.marshal_list_with(game_model)
        def get(self):
            """List all games
            
            Returns:
                List of all games with current state
            """
            pass
        
        @ns.doc('create_game')
        @ns.expect(game_model)
        @ns.marshal_with(game_model, code=201)
        def post(self):
            """Create a new game
            
            Args:
                name: Game name
                players: List of player information
            
            Returns:
                Created game object with ID
            """
            pass
    
    @ns.route('/<string:game_id>')
    class GameResource(Resource):
        @ns.doc('get_game')
        @ns.marshal_with(game_model)
        def get(self, game_id):
            """Get a specific game by ID"""
            pass
    
    @ns.route('/<string:game_id>/draw')
    class GameDrawResource(Resource):
        @ns.doc('draw_card', params={'player_id': 'Player ID'})
        def post(self, game_id):
            """Draw a card for a player
            
            Args:
                game_id: Game ID
                player_id: Player ID
            
            Returns:
                Updated game state
            """
            pass
    
    @ns.route('/<string:game_id>/play')
    class GamePlayResource(Resource):
        @ns.doc('play_card', params={
            'player_id': 'Player ID',
            'card_index': 'Index of card in hand'
        })
        def post(self, game_id):
            """Play a card from hand to table
            
            Args:
                game_id: Game ID
                player_id: Player ID
                card_index: Index of card in player's hand
            
            Returns:
                Updated game state
            """
            pass
    
    @ns.route('/<string:game_id>/shuffle')
    class GameShuffleResource(Resource):
        @ns.doc('shuffle_discard', params={'player_id': 'Player ID'})
        def post(self, game_id):
            """Shuffle discard pile back into deck
            
            Args:
                game_id: Game ID
                player_id: Player ID
            
            Returns:
                Updated game state
            """
            pass
    
    @ns.route('/recent')
    class RecentGamesResource(Resource):
        @ns.doc('get_recent_games', params={'limit': 'Number of recent games'})
        @ns.marshal_list_with(game_model)
        def get(self):
            """Get recent games
            
            Query Parameters:
                limit: Number of recent games to return (default: 10)
            
            Returns:
                List of recent games ordered by creation time
            """
            pass
