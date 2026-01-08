import os
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
