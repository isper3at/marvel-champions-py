from flask import Blueprint

# Create blueprints
card_bp = Blueprint('card', __name__, url_prefix='/api/cards')
deck_bp = Blueprint('deck', __name__, url_prefix='/api/decks')
game_bp = Blueprint('game', __name__, url_prefix='/api/games')
lobby_bp = Blueprint('lobby', __name__, url_prefix='/api/lobbies')

__all__ = ['card_bp', 'deck_bp', 'game_bp', 'lobby_bp']