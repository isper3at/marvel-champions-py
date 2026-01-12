#!/usr/bin/env python3
"""
Marvel Champions EBI Project Setup Script

This script creates the complete project structure with all files.
Run: python setup_project.py
"""

import os
from pathlib import Path


def create_directory_structure():
    """Create all necessary directories"""
    directories = [
        'entities',
        'boundaries',
        'repositories',
        'gateways',
        'interactors',
        'controllers',
        'dto',
        'utils',
        'static/images/cards',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Create __init__.py for Python packages
        if directory not in ['static/images/cards', 'templates']:
            init_file = Path(directory) / '__init__.py'
            if not init_file.exists():
                init_file.touch()
    
    print("✓ Directory structure created")


def write_file(filepath, content):
    """Write content to a file"""
    Path(filepath).write_text(content)
    print(f"✓ Created {filepath}")


def create_config():
    """Create config.py"""
    content = '''import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MongoConfig:
    """MongoDB configuration"""
    host: str
    port: int
    database: str
    username: str | None
    password: str | None
    
    @property
    def connection_string(self) -> str:
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"mongodb://{self.host}:{self.port}"


@dataclass(frozen=True)
class MarvelCDBConfig:
    """MarvelCDB API configuration"""
    base_url: str
    rate_limit_calls: int
    rate_limit_period: int  # seconds
    request_delay: float  # seconds


@dataclass(frozen=True)
class ImageStorageConfig:
    """Image storage configuration"""
    storage_path: str
    max_image_size: int  # bytes


@dataclass(frozen=True)
class AppConfig:
    """Application configuration"""
    secret_key: str
    debug: bool
    host: str
    port: int
    mongo: MongoConfig
    marvelcdb: MarvelCDBConfig
    image_storage: ImageStorageConfig


def load_config() -> AppConfig:
    """Load configuration from environment variables with defaults"""
    
    mongo_config = MongoConfig(
        host=os.getenv('MONGO_HOST', 'localhost'),
        port=int(os.getenv('MONGO_PORT', 27017)),
        database=os.getenv('MONGO_DATABASE', 'marvel_champions'),
        username=os.getenv('MONGO_USERNAME'),
        password=os.getenv('MONGO_PASSWORD')
    )
    
    marvelcdb_config = MarvelCDBConfig(
        base_url=os.getenv('MARVELCDB_URL', 'https://marvelcdb.com'),
        rate_limit_calls=int(os.getenv('RATE_LIMIT_CALLS', 10)),
        rate_limit_period=int(os.getenv('RATE_LIMIT_PERIOD', 60)),
        request_delay=float(os.getenv('REQUEST_DELAY', 0.5))
    )
    
    image_storage_config = ImageStorageConfig(
        storage_path=os.getenv('IMAGE_STORAGE_PATH', 'static/images/cards'),
        max_image_size=int(os.getenv('MAX_IMAGE_SIZE', 5 * 1024 * 1024))  # 5MB
    )
    
    return AppConfig(
        secret_key=os.getenv('SECRET_KEY', os.urandom(32).hex()),
        debug=os.getenv('DEBUG', 'True').lower() == 'true',
        host=os.getenv('APP_HOST', '0.0.0.0'),
        port=int(os.getenv('APP_PORT', 5000)),
        mongo=mongo_config,
        marvelcdb=marvelcdb_config,
        image_storage=image_storage_config
    )
'''
    write_file('config.py', content)


def create_requirements():
    """Create requirements.txt"""
    content = '''# Web Framework
flask==3.0.0
flask-cors==4.0.0

# MongoDB
pymongo==4.6.1

# HTTP Requests
requests==2.31.0

# HTML Parsing
beautifulsoup4==4.12.2

# Data Validation & Serialization
pydantic==2.5.3

# Date/Time
python-dateutil==2.8.2

# Development
python-dotenv==1.0.0
'''
    write_file('requirements.txt', content)


def create_entities():
    """Create all entity files"""
    
    # entities/__init__.py
    init_content = '''from .card import Card, CardType
from .deck import Deck, DeckCard
from .encounter import Encounter, EncounterCard
from .module import Module, ModuleCard
from .game import Game, GameState, CardInPlay, Position

__all__ = [
    'Card', 'CardType',
    'Deck', 'DeckCard',
    'Encounter', 'EncounterCard',
    'Module', 'ModuleCard',
    'Game', 'GameState', 'CardInPlay', 'Position'
]
'''
    write_file('entities/__init__.py', init_content)
    
    # entities/card.py
    card_content = '''from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class CardType(Enum):
    HERO = "hero"
    ALTER_EGO = "alter_ego"
    ALLY = "ally"
    EVENT = "event"
    SUPPORT = "support"
    UPGRADE = "upgrade"
    RESOURCE = "resource"
    VILLAIN = "villain"
    MINION = "minion"
    SIDE_SCHEME = "side_scheme"
    ATTACHMENT = "attachment"
    TREACHERY = "treachery"
    OBLIGATION = "obligation"
    ENVIRONMENT = "environment"


@dataclass(frozen=True)
class Card:
    """
    Immutable domain entity representing a Marvel Champions card.
    This is the core domain object with no external dependencies.
    """
    code: str
    name: str
    type: CardType
    text: Optional[str] = None
    cost: Optional[int] = None
    
    # Hero/Ally stats
    thwart: Optional[int] = None
    attack: Optional[int] = None
    defense: Optional[int] = None
    health: Optional[int] = None
    hand_size: Optional[int] = None
    
    # Villain/Minion stats
    scheme: Optional[int] = None
    threat: Optional[int] = None
    
    # Resource
    resource_physical: int = 0
    resource_mental: int = 0
    resource_energy: int = 0
    resource_wild: int = 0
    
    # Metadata
    pack_code: Optional[str] = None
    faction_code: Optional[str] = None
    traits: tuple[str, ...] = ()
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validation logic"""
        if not self.code:
            raise ValueError("Card code cannot be empty")
        if not self.name:
            raise ValueError("Card name cannot be empty")
    
    def is_hero(self) -> bool:
        return self.type == CardType.HERO
    
    def is_ally(self) -> bool:
        return self.type == CardType.ALLY
    
    def is_event(self) -> bool:
        return self.type == CardType.EVENT
    
    def is_upgrade(self) -> bool:
        return self.type == CardType.UPGRADE
    
    def is_support(self) -> bool:
        return self.type == CardType.SUPPORT
    
    def has_resource(self) -> bool:
        return (self.resource_physical + self.resource_mental + 
                self.resource_energy + self.resource_wild) > 0
    
    def total_resources(self) -> int:
        return (self.resource_physical + self.resource_mental + 
                self.resource_energy + self.resource_wild)
'''
    write_file('entities/card.py', card_content)
    
    # entities/deck.py
    deck_content = '''from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class DeckCard:
    """Represents a card in a deck with quantity"""
    code: str
    quantity: int
    
    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")
        if self.quantity > 3:
            raise ValueError("Card quantity cannot exceed 3")


@dataclass(frozen=True)
class Deck:
    """
    Immutable domain entity representing a player deck.
    """
    id: Optional[str]
    name: str
    hero_code: str
    aspect: str  # justice, aggression, protection, leadership
    cards: tuple[DeckCard, ...]
    
    # Optional MarvelCDB reference
    marvelcdb_id: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Deck name cannot be empty")
        if not self.hero_code:
            raise ValueError("Hero code cannot be empty")
        if self.aspect not in ['justice', 'aggression', 'protection', 'leadership']:
            raise ValueError(f"Invalid aspect: {self.aspect}")
    
    def total_cards(self) -> int:
        """Calculate total number of cards in deck"""
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """Get list of all card codes with quantities expanded"""
        codes = []
        for deck_card in self.cards:
            codes.extend([deck_card.code] * deck_card.quantity)
        return codes
'''
    write_file('entities/deck.py', deck_content)
    
    # entities/encounter.py
    encounter_content = '''from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class EncounterCard:
    """Represents a card in an encounter deck with quantity"""
    code: str
    quantity: int
    
    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")


@dataclass(frozen=True)
class Encounter:
    """
    Immutable domain entity representing an encounter set.
    """
    id: Optional[str]
    name: str
    villain_code: str
    cards: tuple[EncounterCard, ...]
    
    # Metadata
    set_code: Optional[str] = None
    difficulty: Optional[str] = None  # standard, expert
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Encounter name cannot be empty")
        if not self.villain_code:
            raise ValueError("Villain code cannot be empty")
    
    def total_cards(self) -> int:
        """Calculate total number of cards in encounter"""
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """Get list of all card codes with quantities expanded"""
        codes = []
        for enc_card in self.cards:
            codes.extend([enc_card.code] * enc_card.quantity)
        return codes
'''
    write_file('entities/encounter.py', encounter_content)
    
    # entities/module.py
    module_content = '''from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class ModuleCard:
    """Represents a card in a module with quantity"""
    code: str
    quantity: int
    
    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")


@dataclass(frozen=True)
class Module:
    """
    Immutable domain entity representing an encounter module.
    Modules are mixed into encounter decks for variety.
    """
    id: Optional[str]
    name: str
    set_code: str
    cards: tuple[ModuleCard, ...]
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Module name cannot be empty")
        if not self.set_code:
            raise ValueError("Set code cannot be empty")
    
    def total_cards(self) -> int:
        """Calculate total number of cards in module"""
        return sum(card.quantity for card in self.cards)
    
    def get_card_codes(self) -> list[str]:
        """Get list of all card codes with quantities expanded"""
        codes = []
        for mod_card in self.cards:
            codes.extend([mod_card.code] * mod_card.quantity)
        return codes
'''
    write_file('entities/module.py', module_content)
    
    # entities/game.py
    game_content = '''from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Position:
    """2D position on the play field"""
    x: int
    y: int


@dataclass(frozen=True)
class CardInPlay:
    """
    Represents a card in play with its state.
    Immutable - create new instance for state changes.
    """
    code: str
    position: Position
    exhausted: bool = False
    damage: int = 0
    threat: int = 0
    tokens: dict[str, int] = field(default_factory=dict)
    
    def with_position(self, position: Position) -> 'CardInPlay':
        """Create new instance with updated position"""
        return CardInPlay(
            code=self.code,
            position=position,
            exhausted=self.exhausted,
            damage=self.damage,
            threat=self.threat,
            tokens=self.tokens
        )
    
    def with_exhausted(self, exhausted: bool) -> 'CardInPlay':
        """Create new instance with updated exhausted state"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            exhausted=exhausted,
            damage=self.damage,
            threat=self.threat,
            tokens=self.tokens
        )
    
    def with_damage(self, damage: int) -> 'CardInPlay':
        """Create new instance with updated damage"""
        return CardInPlay(
            code=self.code,
            position=self.position,
            exhausted=self.exhausted,
            damage=damage,
            threat=self.threat,
            tokens=self.tokens
        )


@dataclass(frozen=True)
class GameState:
    """
    Immutable game state snapshot.
    All mutations create new instances.
    """
    # Player deck zones
    player_deck: tuple[str, ...]
    player_hand: tuple[str, ...]
    player_discard: tuple[str, ...]
    player_field: tuple[CardInPlay, ...]
    
    # Encounter deck zones
    encounter_deck: tuple[str, ...]
    encounter_discard: tuple[str, ...]
    villain_field: tuple[CardInPlay, ...]
    
    # Game metadata
    threat_on_main_scheme: int = 0
    
    def draw_player_card(self) -> tuple['GameState', Optional[str]]:
        """Draw a card from player deck. Returns new state and drawn card."""
        if not self.player_deck:
            return self, None
        
        drawn = self.player_deck[0]
        new_deck = self.player_deck[1:]
        new_hand = self.player_hand + (drawn,)
        
        new_state = GameState(
            player_deck=new_deck,
            player_hand=new_hand,
            player_discard=self.player_discard,
            player_field=self.player_field,
            encounter_deck=self.encounter_deck,
            encounter_discard=self.encounter_discard,
            villain_field=self.villain_field,
            threat_on_main_scheme=self.threat_on_main_scheme
        )
        
        return new_state, drawn
    
    def shuffle_player_discard_into_deck(self) -> 'GameState':
        """Shuffle discard pile into deck"""
        import random
        combined = list(self.player_deck) + list(self.player_discard)
        random.shuffle(combined)
        
        return GameState(
            player_deck=tuple(combined),
            player_hand=self.player_hand,
            player_discard=(),
            player_field=self.player_field,
            encounter_deck=self.encounter_deck,
            encounter_discard=self.encounter_discard,
            villain_field=self.villain_field,
            threat_on_main_scheme=self.threat_on_main_scheme
        )


@dataclass(frozen=True)
class Game:
    """
    Immutable domain entity representing a game session.
    """
    id: Optional[str]
    name: str
    deck_id: str
    encounter_id: str
    module_ids: tuple[str, ...]
    state: GameState
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Game name cannot be empty")
        if not self.deck_id:
            raise ValueError("Deck ID cannot be empty")
        if not self.encounter_id:
            raise ValueError("Encounter ID cannot be empty")
'''
    write_file('entities/game.py', game_content)


def create_boundaries():
    """Create all boundary interface files"""
    
    # boundaries/__init__.py
    init_content = '''from .repository import (
    CardRepository,
    DeckRepository,
    EncounterRepository,
    ModuleRepository,
    GameRepository
)
from .marvelcdb_gateway import MarvelCDBGateway
from .image_storage import ImageStorage

__all__ = [
    'CardRepository',
    'DeckRepository',
    'EncounterRepository',
    'ModuleRepository',
    'GameRepository',
    'MarvelCDBGateway',
    'ImageStorage'
]
'''
    write_file('boundaries/__init__.py', init_content)
    
    # boundaries/repository.py
    repository_content = '''from abc import ABC, abstractmethod
from typing import Optional, List
from entities import Card, Deck, Encounter, Module, Game


class CardRepository(ABC):
    """Repository interface for Card entity"""
    
    @abstractmethod
    def find_by_code(self, code: str) -> Optional[Card]:
        """Find a card by its unique code"""
        pass
    
    @abstractmethod
    def find_by_codes(self, codes: List[str]) -> List[Card]:
        """Find multiple cards by their codes"""
        pass
    
    @abstractmethod
    def save(self, card: Card) -> Card:
        """Save a card and return the saved entity"""
        pass
    
    @abstractmethod
    def save_all(self, cards: List[Card]) -> List[Card]:
        """Save multiple cards"""
        pass
    
    @abstractmethod
    def exists(self, code: str) -> bool:
        """Check if a card exists"""
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Card]:
        """Find all cards with pagination"""
        pass
    
    @abstractmethod
    def search_by_name(self, name: str) -> List[Card]:
        """Search cards by name (partial match)"""
        pass


class DeckRepository(ABC):
    """Repository interface for Deck entity"""
    
    @abstractmethod
    def find_by_id(self, deck_id: str) -> Optional[Deck]:
        """Find a deck by its ID"""
        pass
    
    @abstractmethod
    def save(self, deck: Deck) -> Deck:
        """Save a deck and return the saved entity"""
        pass
    
    @abstractmethod
    def delete(self, deck_id: str) -> bool:
        """Delete a deck by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Deck]:
        """Find all decks"""
        pass
    
    @abstractmethod
    def find_by_hero(self, hero_code: str) -> List[Deck]:
        """Find all decks for a specific hero"""
        pass
    
    @abstractmethod
    def find_by_marvelcdb_id(self, marvelcdb_id: str) -> Optional[Deck]:
        """Find a deck by its MarvelCDB ID"""
        pass


class EncounterRepository(ABC):
    """Repository interface for Encounter entity"""
    
    @abstractmethod
    def find_by_id(self, encounter_id: str) -> Optional[Encounter]:
        """Find an encounter by its ID"""
        pass
    
    @abstractmethod
    def save(self, encounter: Encounter) -> Encounter:
        """Save an encounter and return the saved entity"""
        pass
    
    @abstractmethod
    def delete(self, encounter_id: str) -> bool:
        """Delete an encounter by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Encounter]:
        """Find all encounters"""
        pass
    
    @abstractmethod
    def find_by_villain(self, villain_code: str) -> List[Encounter]:
        """Find all encounters for a specific villain"""
        pass


class ModuleRepository(ABC):
    """Repository interface for Module entity"""
    
    @abstractmethod
    def find_by_id(self, module_id: str) -> Optional[Module]:
        """Find a module by its ID"""
        pass
    
    @abstractmethod
    def save(self, module: Module) -> Module:
        """Save a module and return the saved entity"""
        pass
    
    @abstractmethod
    def delete(self, module_id: str) -> bool:
        """Delete a module by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Module]:
        """Find all modules"""
        pass
    
    @abstractmethod
    def find_by_set(self, set_code: str) -> List[Module]:
        """Find all modules for a specific set"""
        pass


class GameRepository(ABC):
    """Repository interface for Game entity"""
    
    @abstractmethod
    def find_by_id(self, game_id: str) -> Optional[Game]:
        """Find a game by its ID"""
        pass
    
    @abstractmethod
    def save(self, game: Game) -> Game:
        """Save a game and return the saved entity"""
        pass
    
    @abstractmethod
    def delete(self, game_id: str) -> bool:
        """Delete a game by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Game]:
        """Find all games"""
        pass
    
    @abstractmethod
    def find_recent(self, limit: int = 10) -> List[Game]:
        """Find recent games"""
        pass
'''
    write_file('boundaries/repository.py', repository_content)
    
    # boundaries/marvelcdb_gateway.py
    gateway_content = '''from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class MarvelCDBGateway(ABC):
    """
    Gateway interface for MarvelCDB external service.
    Similar to a DAO but for external APIs.
    """
    
    @abstractmethod
    def set_session_cookie(self, cookie: str) -> None:
        """Set the session cookie for authenticated requests"""
        pass
    
    @abstractmethod
    def get_user_decks(self) -> List[Dict[str, Any]]:
        """
        Retrieve user's deck list from MarvelCDB.
        Returns raw data that will be converted to domain entities.
        """
        pass
    
    @abstractmethod
    def get_deck_details(self, deck_id: str) -> Dict[str, Any]:
        """
        Retrieve full deck details including card list.
        Returns raw data that will be converted to domain entities.
        """
        pass
    
    @abstractmethod
    def get_card_data(self, card_code: str) -> Dict[str, Any]:
        """
        Retrieve card data from MarvelCDB.
        Returns raw data that will be converted to Card entity.
        """
        pass
    
    @abstractmethod
    def get_card_image_url(self, card_code: str) -> Optional[str]:
        """Get the image URL for a card"""
        pass
    
    @abstractmethod
    def download_card_image(self, image_url: str) -> bytes:
        """Download card image binary data"""
        pass
    
    @abstractmethod
    def search_cards(self, query: str) -> List[Dict[str, Any]]:
        """Search for cards by name"""
        pass
'''
    write_file('boundaries/marvelcdb_gateway.py', gateway_content)
    
    # boundaries/image_storage.py
    storage_content = '''from abc import ABC, abstractmethod
from typing import Optional, List


class ImageStorage(ABC):
    """
    Interface for image storage operations.
    Abstracts the storage mechanism (filesystem, S3, etc.)
    """
    
    @abstractmethod
    def save_image(self, card_code: str, image_data: bytes) -> str:
        """
        Save card image and return the file path/URL.
        
        Args:
            card_code: Unique card identifier
            image_data: Binary image data
            
        Returns:
            Path or URL to the saved image
        """
        pass
    
    @abstractmethod
    def get_image_path(self, card_code: str) -> Optional[str]:
        """
        Get the path/URL for a card image if it exists.
        
        Args:
            card_code: Unique card identifier
            
        Returns:
            Path or URL to the image, or None if not found
        """
        pass
    
    @abstractmethod
    def image_exists(self, card_code: str) -> bool:
        """Check if an image exists for a card"""
        pass
    
    @abstractmethod
    def delete_image(self, card_code: str) -> bool:
        """Delete a card image"""
        pass
    
    @abstractmethod
    def get_all_image_codes(self) -> List[str]:
        """Get list of all card codes that have images"""
        pass
'''
    write_file('boundaries/image_storage.py', storage_content)


def create_readme():
    """Create README.md"""
    content = '''# Marvel Champions - EBI Architecture

A Python-based digital play application for Marvel Champions card game, built with clean EBI (Entity-Boundary-Interactor) architecture.

## Project Structure

```
marvel-champions-ebi/
├── entities/           # Domain models (immutable)
├── boundaries/         # Interfaces (ABC)
├── repositories/       # MongoDB implementations
├── gateways/          # External service integrations
├── interactors/       # Business logic
├── controllers/       # REST API endpoints
├── dto/               # Data Transfer Objects
├── utils/             # Utility functions
├── static/            # Static files & images
├── templates/         # HTML templates
├── config.py          # Configuration
└── app.py             # Application entry point
```

## Setup

1. **Install MongoDB**
   ```bash
   # macOS
   brew install mongodb-community
   brew services start mongodb-community
   
   # Ubuntu
   sudo apt install mongodb
   sudo systemctl start mongodb
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional)
   ```bash
   export MONGO_HOST=localhost
   export MONGO_PORT=27017
   export MONGO_DATABASE=marvel_champions
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

## Architecture Principles

- **Immutability**: All entities are frozen dataclasses
- **Dependency Inversion**: Depend on interfaces, not implementations
- **Single Responsibility**: Each class has one clear purpose
- **Type Safety**: Full type hints throughout

## Next Steps

Currently, the project has:
- ✅ Complete entity models
- ✅ All boundary interfaces
- ✅ Configuration system

Still to implement:
- ⏳ Repository implementations (MongoDB)
- ⏳ Gateway implementations (MarvelCDB, Image Storage)
- ⏳ Business logic (Interactors)
- ⏳ REST API (Controllers)
- ⏳ Frontend UI

## License

Personal/Educational use only. Respects Marvel Champions and MarvelCDB terms of service.
'''
    write_file('README.md', content)


def create_app_py():
    """Create main application entry point"""
    content = '''#!/usr/bin/env python3
"""
Marvel Champions Digital Play Application

Main application entry point that wires up all dependencies
and starts the Flask server.
"""

from flask import Flask
from config import load_config


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
    
    # TODO: Initialize MongoDB connection
    # db = MongoClient(config.mongo.connection_string)
    
    # TODO: Initialize repositories
    # card_repo = MongoCardRepository(db)
    # deck_repo = MongoDeckRepository(db)
    # etc.
    
    # TODO: Initialize gateways
    # marvelcdb_gateway = MarvelCDBClient(config.marvelcdb)
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
        <li>⏳ Repositories not yet implemented</li>
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
'''
    write_file('app.py', content)


def create_gitignore():
    """Create .gitignore"""
    content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local

# Database
*.db
*.sqlite

# Images
static/images/cards/*.jpg
static/images/cards/*.png

# Logs
*.log

# OS
.DS_Store
Thumbs.db
'''
    write_file('.gitignore', content)


def main():
    """Main setup function"""
    print("=" * 60)
    print("Marvel Champions EBI Project Setup")
    print("=" * 60)
    print()
    
    create_directory_structure()
    create_config()
    create_requirements()
    create_entities()
    create_boundaries()
    create_app_py()
    create_readme()
    create_gitignore()
    
    print()
    print("=" * 60)
    print("✓ Project setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. cd marvel-champions-ebi")
    print("2. Create virtual environment: python3 -m venv venv")
    print("3. Activate: source venv/bin/activate (or venv\\Scripts\\activate on Windows)")
    print("4. Install dependencies: pip3 install -r requirements.txt")
    print("5. Start the service: python3 app.py")
    print("6. Visit: http://localhost:5000")
    print()
    print("To push to GitHub:")
    print("1. git init")
    print("2. git add .")
    print("3. git commit -m 'Initial commit'")
    print("4. Create repo on GitHub")
    print("5. git remote add origin <your-repo-url>")
    print("6. git push -u origin main")
    print()


if __name__ == '__main__':
    main()

