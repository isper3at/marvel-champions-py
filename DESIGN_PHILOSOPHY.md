# Design Philosophy: No Rules, Just Tools

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
