#!/usr/bin/env python3
"""
Update project to simplified, no-rules design.

Philosophy: Players know the rules. We just provide:
- A way to import decks
- A way to display cards
- A flexible play area
- NO rules enforcement

Run: python3 update_to_simplified.py
"""

from pathlib import Path


def write_file(filepath, content):
    """Write content to a file"""
    Path(filepath).write_text(content)
    print(f"✓ Updated {filepath}")


def update_entities():
    """Update entity files to simplified design"""
    
    # entities/__init__.py
    init_content = '''from .card import Card
from .deck import Deck, DeckCard
from .game import Game, GameState, CardInPlay, Position

__all__ = [
    'Card',
    'Deck', 'DeckCard',
    'Game', 'GameState', 'CardInPlay', 'Position'
]
'''
    write_file('entities/__init__.py', init_content)
    
    # Remove old files we don't need anymore
    old_files = ['entities/encounter.py', 'entities/module.py']
    for f in old_files:
        filepath = Path(f)
        if filepath.exists():
            filepath.unlink()
            print(f"✓ Removed {f}")


def update_boundaries():
    """Update boundary interfaces to simplified design"""
    
    # boundaries/__init__.py
    init_content = '''from .repository import CardRepository, DeckRepository, GameRepository
from .marvelcdb_gateway import MarvelCDBGateway
from .image_storage import ImageStorage

__all__ = [
    'CardRepository',
    'DeckRepository',
    'GameRepository',
    'MarvelCDBGateway',
    'ImageStorage'
]
'''
    write_file('boundaries/__init__.py', init_content)


def create_readme_philosophy():
    """Create a design philosophy document"""
    content = '''# Design Philosophy: No Rules, Just Tools

## Core Belief
**Players know the rules. We just provide the digital play space.**

## What We DO
✅ Import decks from MarvelCDB
✅ Display card images
✅ Provide zones (deck, hand, discard, play area)
✅ Allow free positioning of cards
✅ Support rotation (for exhausting)
✅ Support generic counters (damage, threat, whatever)
✅ Save/load game state

## What We DON'T DO
❌ Enforce deck-building rules
❌ Validate card types
❌ Check if moves are "legal"
❌ Calculate automatic damage/threat
❌ Force turn structure
❌ Prevent "illegal" plays

## Why?
1. **Simpler Code**: No complex rules engine
2. **Flexibility**: Players can house-rule however they want
3. **Updates**: No need to update when FFG changes rules
4. **Variants**: Works for any variant (true solo, co-op, challenge modes)
5. **Learning**: Players learn by doing, not fighting the app

## Design Principles
1. **Minimal Data**: Cards are just code + name + text (for accessibility)
2. **No Validation**: If a player wants 10 copies of a card, who cares?
3. **Visual States**: Rotated/flipped/counters are just visual - no meaning enforced
4. **Trust Players**: They know what they're doing
5. **One Source of Truth**: MongoDB for persistence, memory for game state

## Example
A card doesn't need to know:
- Its type (ally, event, etc.) - the image shows that
- Its cost - the image shows that
- Its stats - the image shows that
- Its aspect - the image shows that

All the card needs is:
- `code`: To identify and load the image
- `name`: For accessibility/search
- `text`: For screen readers

Everything else is on the card image itself.
'''
    write_file('DESIGN_PHILOSOPHY.md', content)


def main():
    print("=" * 60)
    print("Updating to Simplified, No-Rules Design")
    print("=" * 60)
    print()
    
    update_entities()
    update_boundaries()
    create_readme_philosophy()
    
    print()
    print("=" * 60)
    print("✓ Update complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review DESIGN_PHILOSOPHY.md")
    print("2. Copy the simplified entity code from artifacts")
    print("3. Copy the simplified boundary code from artifacts")
    print("4. We'll create simplified repositories next")
    print()
    print("Key changes:")
    print("- Removed Encounter and Module entities")
    print("- Simplified Card to just: code, name, text")
    print("- Simplified Deck to just: name, cards")
    print("- Simplified Game to just: zones and play area")
    print("- NO rules enforcement anywhere")
    print()


if __name__ == '__main__':
    main()
