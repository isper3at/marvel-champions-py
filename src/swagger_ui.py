"""
Swagger UI / OpenAPI Documentation Setup

This module provides Swagger UI integration for the Flask app.
It serves the OpenAPI specification and provides interactive documentation.

Usage:
    from src.swagger_ui import init_swagger_ui
    
    app = Flask(__name__)
    init_swagger_ui(app)
"""

from flask import Blueprint, send_file, jsonify
import yaml
import os
from pathlib import Path


swagger_bp = Blueprint('swagger', __name__, url_prefix='/api')


def init_swagger_ui(app):
    """
    Initialize Swagger UI for the Flask app.
    
    Registers routes for:
    - /api/docs - Swagger UI
    - /api/redoc - ReDoc UI
    - /openapi.yaml - OpenAPI specification
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(swagger_bp)
    
    @app.route('/api/docs')
    def swagger_ui():
        """Serve Swagger UI"""
        html = """
        <!DOCTYPE html>
        <html>
          <head>
            <title>API Documentation</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
            <style>
              html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
              *, *:before, *:after { box-sizing: inherit; }
              body { margin:0; padding: 0; }
            </style>
          </head>
          <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.js"></script>
            <script>
            SwaggerUIBundle({
              url: "/openapi.yaml",
              dom_id: '#swagger-ui',
              presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
              ],
              layout: "StandaloneLayout"
            })
            </script>
          </body>
        </html>
        """
        return html, 200, {'Content-Type': 'text/html'}

    @app.route('/api/redoc')
    def redoc_ui():
        """Serve ReDoc UI"""
        html = """
        <!DOCTYPE html>
        <html>
          <head>
            <title>API Documentation</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
            <style>
              body { margin: 0; padding: 0; }
            </style>
          </head>
          <body>
            <redoc spec-url="/openapi.yaml"></redoc>
            <script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"></script>
          </body>
        </html>
        """
        return html, 200, {'Content-Type': 'text/html'}

    @app.route('/openapi.yaml')
    def openapi_spec():
        """Serve OpenAPI specification"""
        spec_path = Path(__file__).parent.parent.parent / 'openapi.yaml'
        
        try:
            with open(spec_path, 'r') as f:
                spec = yaml.safe_load(f)
            return jsonify(spec)
        except FileNotFoundError:
            return jsonify({'error': 'OpenAPI spec not found'}), 404


@swagger_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with status
    """
    return jsonify({'status': 'ok'})


# ============================================================================
# Documentation Generation Helpers
# ============================================================================

def validate_openapi_spec():
    """
    Validate the OpenAPI specification.
    
    Returns:
        Tuple of (is_valid, errors)
    """
    try:
        from openapi_spec_validator import validate_spec
        from openapi_spec_validator.validation.exceptions import OpenAPIValidationError
        
        spec_path = Path(__file__).parent.parent.parent / 'openapi.yaml'
        
        with open(spec_path, 'r') as f:
            spec = yaml.safe_load(f)
        
        validate_spec(spec)
        return True, []
        
    except ImportError:
        return None, ["openapi-spec-validator not installed"]
    except OpenAPIValidationError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [str(e)]


def generate_client_stub(language: str = 'python'):
    """
    Generate a client SDK stub.
    
    Args:
        language: Programming language (python, typescript, etc)
    
    Returns:
        Generated client code as string
    """
    spec_path = Path(__file__).parent.parent.parent / 'openapi.yaml'
    
    with open(spec_path, 'r') as f:
        spec = yaml.safe_load(f)
    
    if language == 'python':
        return _generate_python_client(spec)
    elif language == 'typescript':
        return _generate_typescript_client(spec)
    else:
        raise ValueError(f"Unsupported language: {language}")


def _generate_python_client(spec):
    """Generate Python client SDK"""
    client_code = """
# Auto-generated Marvel Champions API Client
# Generated from openapi.yaml

import requests
from typing import Optional, List, Dict

class MarvelChampionsClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    # ==================
    # Card Operations
    # ==================
    
    def get_card(self, code: str) -> Dict:
        '''Get card by code'''
        response = self.session.get(f"{self.base_url}/api/cards/{code}")
        response.raise_for_status()
        return response.json()
    
    def search_cards(self, query: str) -> Dict:
        '''Search cards by name'''
        response = self.session.get(
            f"{self.base_url}/api/cards/search",
            params={"q": query}
        )
        response.raise_for_status()
        return response.json()
    
    def import_card(self, code: str) -> Dict:
        '''Import card from MarvelCDB'''
        response = self.session.post(
            f"{self.base_url}/api/cards/import",
            json={"code": code}
        )
        response.raise_for_status()
        return response.json()
    
    def import_cards_bulk(self, codes: List[str]) -> Dict:
        '''Import multiple cards'''
        response = self.session.post(
            f"{self.base_url}/api/cards/import/bulk",
            json={"codes": codes}
        )
        response.raise_for_status()
        return response.json()
    
    # ==================
    # Deck Operations
    # ==================
    
    def list_decks(self) -> Dict:
        '''List all decks'''
        response = self.session.get(f"{self.base_url}/api/decks")
        response.raise_for_status()
        return response.json()
    
    def create_deck(self, name: str, cards: List[Dict]) -> Dict:
        '''Create new deck'''
        response = self.session.post(
            f"{self.base_url}/api/decks",
            json={"name": name, "cards": cards}
        )
        response.raise_for_status()
        return response.json()
    
    def get_deck(self, deck_id: str) -> Dict:
        '''Get deck details'''
        response = self.session.get(f"{self.base_url}/api/decks/{deck_id}")
        response.raise_for_status()
        return response.json()
    
    def update_deck(self, deck_id: str, **kwargs) -> Dict:
        '''Update deck'''
        response = self.session.put(
            f"{self.base_url}/api/decks/{deck_id}",
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def delete_deck(self, deck_id: str) -> Dict:
        '''Delete deck'''
        response = self.session.delete(f"{self.base_url}/api/decks/{deck_id}")
        response.raise_for_status()
        return response.json()
    
    # ==================
    # Game Operations
    # ==================
    
    def list_games(self) -> Dict:
        '''List all games'''
        response = self.session.get(f"{self.base_url}/api/games")
        response.raise_for_status()
        return response.json()
    
    def create_game(self, name: str, deck_ids: List[str], 
                    player_names: List[str]) -> Dict:
        '''Create new game'''
        response = self.session.post(
            f"{self.base_url}/api/games",
            json={
                "name": name,
                "deck_ids": deck_ids,
                "player_names": player_names
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_game(self, game_id: str) -> Dict:
        '''Get game state'''
        response = self.session.get(f"{self.base_url}/api/games/{game_id}")
        response.raise_for_status()
        return response.json()
    
    def draw_card(self, game_id: str, player_name: str) -> Dict:
        '''Draw card for player'''
        response = self.session.post(
            f"{self.base_url}/api/games/{game_id}/draw",
            json={"player_name": player_name}
        )
        response.raise_for_status()
        return response.json()
    
    def play_card(self, game_id: str, player_name: str, 
                  card_code: str, position: Dict) -> Dict:
        '''Play card to table'''
        response = self.session.post(
            f"{self.base_url}/api/games/{game_id}/play",
            json={
                "player_name": player_name,
                "card_code": card_code,
                "position": position
            }
        )
        response.raise_for_status()
        return response.json()
    
    def add_counter(self, game_id: str, card_code: str,
                    counter_type: str, amount: int = 1) -> Dict:
        '''Add counter to card'''
        response = self.session.post(
            f"{self.base_url}/api/games/{game_id}/counter",
            json={
                "card_code": card_code,
                "counter_type": counter_type,
                "amount": amount
            }
        )
        response.raise_for_status()
        return response.json()


# Usage Example
if __name__ == "__main__":
    client = MarvelChampionsClient()
    
    # Import a card
    card = client.import_card("01001a")
    print(f"Imported: {card['card']['name']}")
    
    # Create deck
    deck = client.create_deck("My Deck", [
        {"code": "01001a", "quantity": 2}
    ])
    print(f"Created deck: {deck['deck']['id']}")
    
    # Create game
    game = client.create_game("Test", [deck['deck']['id']], ["Alice"])
    print(f"Created game: {game['game']['id']}")
    
    # Play
    game = client.draw_card(game['game']['id'], "Alice")
    print(f"Drew card, hand size: {len(game['game']['state']['players'][0]['hand'])}")
"""
    return client_code


def _generate_typescript_client(spec):
    """Generate TypeScript client SDK"""
    client_code = """
// Auto-generated Marvel Champions API Client
// Generated from openapi.yaml

export interface CardResponse {
    code: string;
    name: string;
    text?: string;
}

export interface DeckCard {
    code: string;
    quantity: number;
}

export interface Position {
    x: number;
    y: number;
}

export class MarvelChampionsClient {
    private baseUrl: string;
    
    constructor(baseUrl: string = "http://localhost:5000") {
        this.baseUrl = baseUrl;
    }
    
    private async request(method: string, path: string, body?: any): Promise<any> {
        const options: RequestInit = {
            method,
            headers: { "Content-Type": "application/json" }
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${this.baseUrl}${path}`, options);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        return response.json();
    }
    
    // Card Operations
    
    async getCard(code: string): Promise<CardResponse> {
        return this.request("GET", `/api/cards/${code}`);
    }
    
    async searchCards(query: string): Promise<any> {
        return this.request("GET", `/api/cards/search?q=${query}`);
    }
    
    async importCard(code: string): Promise<any> {
        return this.request("POST", "/api/cards/import", { code });
    }
    
    async importCardsBulk(codes: string[]): Promise<any> {
        return this.request("POST", "/api/cards/import/bulk", { codes });
    }
    
    // Deck Operations
    
    async listDecks(): Promise<any> {
        return this.request("GET", "/api/decks");
    }
    
    async createDeck(name: string, cards: DeckCard[]): Promise<any> {
        return this.request("POST", "/api/decks", { name, cards });
    }
    
    async getDeck(deckId: string): Promise<any> {
        return this.request("GET", `/api/decks/${deckId}`);
    }
    
    // Game Operations
    
    async createGame(name: string, deckIds: string[], 
                     playerNames: string[]): Promise<any> {
        return this.request("POST", "/api/games", {
            name, deck_ids: deckIds, player_names: playerNames
        });
    }
    
    async getGame(gameId: string): Promise<any> {
        return this.request("GET", `/api/games/${gameId}`);
    }
    
    async drawCard(gameId: string, playerName: string): Promise<any> {
        return this.request("POST", `/api/games/${gameId}/draw`,
            { player_name: playerName }
        );
    }
    
    async playCard(gameId: string, playerName: string, cardCode: string, 
                   position: Position): Promise<any> {
        return this.request("POST", `/api/games/${gameId}/play`, {
            player_name: playerName,
            card_code: cardCode,
            position
        });
    }
    
    async addCounter(gameId: string, cardCode: string, 
                     counterType: string, amount: number = 1): Promise<any> {
        return this.request("POST", `/api/games/${gameId}/counter`, {
            card_code: cardCode,
            counter_type: counterType,
            amount
        });
    }
}

// Usage Example
async function example() {
    const client = new MarvelChampionsClient();
    
    // Import a card
    const card = await client.importCard("01001a");
    console.log(`Imported: ${card.card.name}`);
    
    // Create deck
    const deck = await client.createDeck("My Deck", [
        { code: "01001a", quantity: 2 }
    ]);
    console.log(`Created deck: ${deck.deck.id}`);
    
    // Create game
    const game = await client.createGame("Test", [deck.deck.id], ["Alice"]);
    console.log(`Created game: ${game.game.id}`);
}

export default MarvelChampionsClient;
"""
    return client_code
