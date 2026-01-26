"""
Pytest configuration and shared fixtures.
Run tests with: pytest tests/
"""

import pytest
from pymongo import MongoClient
from src.config import load_config, MongoConfig, MarvelCDBConfig, ImageStorageConfig
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def test_config():
    """Create test configuration"""
    return load_config()


@pytest.fixture
def test_db():
    """Create test database connection"""
    client = MongoClient('mongodb://localhost:27017/', uuidRepresentation='standard')
    db = client['marvel_champions_test']
    
    yield db
    
    # Cleanup: drop all collections after each test
    for collection in db.list_collection_names():
        db[collection].drop()

@pytest.fixture
def test_marvel_client():
    """Create MarvelCDBClient with test config"""
    config = MarvelCDBConfig(
        base_url='https://marvelcdb.com',
        rate_limit_calls=10,
        rate_limit_period=60,
        request_delay=0.1  # Faster for tests
    )
    from src.gateways.marvelcdb_client import MarvelCDBClient
    return MarvelCDBClient(config)


@pytest.fixture
def temp_image_dir():
    """Create temporary directory for image storage"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def image_storage_config(temp_image_dir):
    """Create image storage config with temp directory"""
    return ImageStorageConfig(
        storage_path=temp_image_dir,
        max_image_size=5 * 1024 * 1024
    )


@pytest.fixture
def marvelcdb_config():
    """Create MarvelCDB config"""
    return MarvelCDBConfig(
        base_url='https://marvelcdb.com',
        rate_limit_calls=10,
        rate_limit_period=60,
        request_delay=0.1  # Faster for tests
    )