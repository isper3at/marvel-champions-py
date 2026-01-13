# gateways/__init__.py
from .marvelcdb_client import MarvelCDBClient
from .local_image_storage import LocalImageStorage

__all__ = ['MarvelCDBClient', 'LocalImageStorage']
