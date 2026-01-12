import os
import sys
import json
import pytest
from flask import url_for

# Ensure repo root is on sys.path so tests can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app

class DummyResp:
    def __init__(self):
        self._data = {}

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    # Use an in-memory mongomock for tests by patching MongoClient if needed.
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_and_get_lobby(client):
    rv = client.post('/api/lobby/create', json={'host': 'alice'})
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'room' in data
    room = data['room']

    rv2 = client.get(f'/api/lobby/{room}')
    assert rv2.status_code == 200
    l = rv2.get_json()
    assert l['host'] == 'alice'
    assert l['id'] == room

def test_join_and_ready(client):
    rv = client.post('/api/lobby/create', json={'host': 'bob'})
    room = rv.get_json()['room']
    rv2 = client.post(f'/api/lobby/{room}/join', json={'name': 'charlie'})
    assert rv2.status_code == 200
    p = rv2.get_json()
    assert 'id' in p
    pid = p['id']
    # mark ready
    rv3 = client.post(f'/api/lobby/{room}/player/{pid}/ready', json={'ready': True})
    assert rv3.status_code == 200
    # fetch lobby and ensure player ready is True
    rv4 = client.get(f'/api/lobby/{room}')
    lobby = rv4.get_json()
    found = False
    for pl in lobby['players']:
        if pl['id'] == pid:
            found = True
            assert pl['ready'] is True
    assert found
