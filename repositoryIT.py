#!/usr/bin/env python3
"""
Test script for MongoDB repositories.
Run this to verify everything works.

Prerequisites:
1. MongoDB running on localhost:27017
2. All entity and repository files in place

Usage:
    python3 test_repositories.py
"""

from pymongo import MongoClient
from repositories.mongo_card_repository import MongoCardRepository
from repositories.mongo_deck_repository import MongoDeckRepository
from repositories.mongo_game_repository import MongoGameRepository
from entities import Card, Deck, DeckCard, Game, GameState, PlayerZones, CardInPlay, Position


def test_card_repository():
    """Test CardRepository CRUD operations"""
    print("\n" + "="*60)
    print("Testing Card Repository")
    print("="*60)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['marvel_champions_test']
    repo = MongoCardRepository(db)
    
    # Clean up first
    db['cards'].delete_many({})
    
    # Test 1: Save a card
    print("\n1. Testing save...")
    card = Card(code='01001a', name='Spider-Man (Peter Parker)', text='Friendly neighborhood hero')
    saved = repo.save(card)
    print(f"   Saved: {saved.name}")
    assert saved.code == '01001a'
    assert saved.name == 'Spider-Man (Peter Parker)'
    
    # Test 2: Find by code
    print("\n2. Testing find_by_code...")
    found = repo.find_by_code('01001a')
    print(f"   Found: {found.name}")
    assert found is not None
    assert found.code == '01001a'
    
    # Test 3: Save multiple cards
    print("\n3. Testing save_all...")
    cards = [
        Card(code='01002a', name='Captain Marvel', text='Higher, further, faster'),
        Card(code='01003a', name='Iron Man', text='Genius billionaire'),
        Card(code='01004a', name='Black Panther', text='Wakanda forever')
    ]
    saved_all = repo.save_all(cards)
    print(f"   Saved {len(saved_all)} cards")
    assert len(saved_all) == 3
    
    # Test 4: Find by codes
    print("\n4. Testing find_by_codes...")
    found_many = repo.find_by_codes(['01001a', '01002a', '01003a'])
    print(f"   Found {len(found_many)} cards")
    assert len(found_many) == 3
    
    # Test 5: Search by name
    print("\n5. Testing search_by_name...")
    results = repo.search_by_name('spider')
    print(f"   Search 'spider' returned {len(results)} results")
    assert len(results) >= 1
    
    # Test 6: Exists
    print("\n6. Testing exists...")
    exists = repo.exists('01001a')
    not_exists = repo.exists('99999z')
    print(f"   01001a exists: {exists}")
    print(f"   99999z exists: {not_exists}")
    assert exists is True
    assert not_exists is False
    
    print("\n✅ Card Repository tests passed!")


def test_deck_repository():
    """Test DeckRepository CRUD operations"""
    print("\n" + "="*60)
    print("Testing Deck Repository")
    print("="*60)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['marvel_champions_test']
    repo = MongoDeckRepository(db)
    
    # Clean up first
    db['decks'].delete_many({})
    
    # Test 1: Save a deck
    print("\n1. Testing save (new deck)...")
    deck = Deck(
        id=None,
        name='Justice Spider-Man',
        cards=(
            DeckCard(code='01001a', quantity=1),
            DeckCard(code='01002a', quantity=3),
            DeckCard(code='01003a', quantity=2)
        ),
        source_url='https://marvelcdb.com/decklist/12345'
    )
    saved = repo.save(deck)
    print(f"   Saved deck: {saved.name}")
    print(f"   Deck ID: {saved.id}")
    assert saved.id is not None
    assert saved.name == 'Justice Spider-Man'
    assert len(saved.cards) == 3
    
    deck_id = saved.id
    
    # Test 2: Find by ID
    print("\n2. Testing find_by_id...")
    found = repo.find_by_id(deck_id)
    print(f"   Found: {found.name}")
    assert found is not None
    assert found.id == deck_id
    
    # Test 3: Update deck
    print("\n3. Testing save (update existing)...")
    updated_deck = Deck(
        id=deck_id,
        name='Justice Spider-Man v2',
        cards=saved.cards,
        source_url=saved.source_url
    )
    updated = repo.save(updated_deck)
    print(f"   Updated name: {updated.name}")
    assert updated.name == 'Justice Spider-Man v2'
    assert updated.id == deck_id
    
    # Test 4: Find all
    print("\n4. Testing find_all...")
    all_decks = repo.find_all()
    print(f"   Found {len(all_decks)} decks")
    assert len(all_decks) >= 1
    
    # Test 5: Delete
    print("\n5. Testing delete...")
    deleted = repo.delete(deck_id)
    print(f"   Deleted: {deleted}")
    assert deleted is True
    
    # Verify deletion
    not_found = repo.find_by_id(deck_id)
    assert not_found is None
    
    print("\n✅ Deck Repository tests passed!")


def test_game_repository():
    """Test GameRepository CRUD operations"""
    print("\n" + "="*60)
    print("Testing Game Repository")
    print("="*60)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['marvel_champions_test']
    repo = MongoGameRepository(db)
    
    # Clean up first
    db['games'].delete_many({})
    
    # Test 1: Save a game (2 players)
    print("\n1. Testing save (new game)...")
    game = Game(
        id=None,
        name='Alice vs Bob - Rhino',
        deck_ids=('deck_alice_123', 'deck_bob_456'),
        state=GameState(
            players=(
                PlayerZones(
                    player_name='Alice',
                    deck=('01001a', '01002a', '01003a'),
                    hand=('01004a',),
                    discard=()
                ),
                PlayerZones(
                    player_name='Bob',
                    deck=('01010a', '01011a'),
                    hand=('01012a', '01013a'),
                    discard=('01014a',)
                )
            ),
            play_area=(
                CardInPlay(
                    code='01001a',
                    position=Position(x=100, y=200),
                    rotated=True,
                    counters={'damage': 3}
                ),
            )
        )
    )
    
    saved = repo.save(game)
    print(f"   Saved game: {saved.name}")
    print(f"   Game ID: {saved.id}")
    print(f"   Players: {[p.player_name for p in saved.state.players]}")
    assert saved.id is not None
    assert len(saved.state.players) == 2
    assert saved.state.players[0].player_name == 'Alice'
    
    game_id = saved.id
    
    # Test 2: Find by ID
    print("\n2. Testing find_by_id...")
    found = repo.find_by_id(game_id)
    print(f"   Found: {found.name}")
    assert found is not None
    assert len(found.state.players) == 2
    assert len(found.state.play_area) == 1
    assert found.state.play_area[0].counters['damage'] == 3
    
    # Test 3: Update game state
    print("\n3. Testing save (update game state)...")
    # Find player Alice and simulate drawing a card
    print("   Simulating Alice drawing a card...")
    alice = found.state.get_player('Alice')
    print(f"   Alice's hand size before draw: {len(alice.hand)}")
    print(f"   Alice's deck size before draw: {len(alice.deck)}")
    
    # Simulate Alice drawing a card
    new_player_zone, drawn = alice.draw_card()
    updated_game = Game(
        id=game_id,
        name=found.name,
        deck_ids=found.deck_ids,
        state=found.state.update_player(new_player_zone)
    )
    updated = repo.save(updated_game)
    alice = updated.state.get_player('Alice')
    print(f"   Alice's hand size: {len(alice.hand)}")
    print(f"   Alice's deck size: {len(alice.deck)}")
    assert len(alice.hand) == 2  # Had 1, drew 1
    
    # Test 4: Find all and recent
    print("\n4. Testing find_all and find_recent...")
    all_games = repo.find_all()
    recent = repo.find_recent(limit=5)
    print(f"   All games: {len(all_games)}")
    print(f"   Recent games: {len(recent)}")
    assert len(all_games) >= 1
    assert len(recent) >= 1
    
    # Test 5: Delete
    print("\n5. Testing delete...")
    deleted = repo.delete(game_id)
    print(f"   Deleted: {deleted}")
    assert deleted is True
    
    print("\n✅ Game Repository tests passed!")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MONGODB REPOSITORY TESTS")
    print("="*60)
    
    try:
        # Test MongoDB connection
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        print("\n✅ MongoDB connection successful")
    except Exception as e:
        print(f"\n❌ MongoDB connection failed: {e}")
        print("\nMake sure MongoDB is running:")
        print("  brew services start mongodb-community  (macOS)")
        print("  sudo systemctl start mongodb           (Linux)")
        return
    
    try:
        test_card_repository()
        test_deck_repository()
        test_game_repository()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nRepositories are working correctly!")
        print("You can now build the interactors and controllers.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

