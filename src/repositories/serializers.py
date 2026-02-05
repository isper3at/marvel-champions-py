"""
MongoDB serializers for converting entities to/from MongoDB documents.
Each entity has a serializer class with to_doc() and to_entity() methods.
"""

from datetime import datetime
from src.entities import (
    Card, Deck, DeckList, DeckCard, Game, GamePhase, Player, 
    PlayZone, CardInPlay, Position, DeckInPlay, Dial
)
from src.entities.encounter_deck import EncounterDeck
from src.entities.encounter_deck_in_play import EncounterDeckInPlay


class CardSerializer:
    @staticmethod
    def to_entity(doc: dict) -> Card:
        """Convert MongoDB document to Card entity"""
        return Card(
            code=doc['code'],
            name=doc['name'],
            text=doc.get('text', ''),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )
    
    @staticmethod
    def to_doc(card: Card) -> dict:
        """Convert Card entity to MongoDB document"""
        return {
            'code': card.code,
            'name': card.name,
            'text': card.text
        }


class DeckCardSerializer:
    @staticmethod
    def to_entity(doc: dict) -> DeckCard:
        """Convert MongoDB document to DeckCard entity"""
        return DeckCard(
            code=doc['code'],
            quantity=doc['quantity']
        )
    
    @staticmethod
    def to_doc(deck_card: DeckCard) -> dict:
        """Convert DeckCard entity to MongoDB document"""
        return {
            'code': deck_card.code,
            'quantity': deck_card.quantity
        }

class DeckListSerializer:
    @staticmethod
    def to_entity(doc: dict) -> DeckList:
        """Convert MongoDB document to DeckList entity"""
        cards = tuple(
            DeckCardSerializer.to_entity(c)
            for c in doc.get('cards', [])
        )
        return DeckList(
            id=doc['deck_id'],
            name=doc['name'],
            cards=cards
        )
    
    @staticmethod
    def to_doc(deck_list: DeckList) -> dict:
        """Convert DeckList entity to MongoDB document"""
        return {
            'deck_id': deck_list.id,
            'name': deck_list.name,
            'cards': [DeckCardSerializer.to_doc(c) for c in deck_list.cards]
        }

class DeckSerializer:
    @staticmethod
    def to_entity(doc: dict) -> Deck:
        """Convert MongoDB document to Deck entity"""
        cards = tuple(
            CardSerializer.to_entity(c)
            for c in doc.get('cards', [])
        )
        return Deck(
            id=doc['deck_id'],
            name=doc['name'],
            cards=cards,
            source_url=doc.get('source_url'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )
    
    @staticmethod
    def to_doc(deck: Deck) -> dict:
        """Convert Deck entity to MongoDB document"""
        return {
            'deck_id': deck.id,
            'name': deck.name,
            'cards': [CardSerializer.to_doc(c) for c in deck.cards],
            'source_url': deck.source_url,
            'created_at': deck.created_at,
            'updated_at': deck.updated_at
        }


class PositionSerializer:
    @staticmethod
    def to_entity(doc: dict) -> Position:
        """Convert MongoDB document to Position entity"""
        return Position(
            x=doc['x'],
            y=doc['y'],
            rotation=doc.get('rotation', 0),
            flip_state=doc.get('flip_state', 'face_up')
        )
    
    @staticmethod
    def to_doc(position: Position) -> dict:
        """Convert Position entity to MongoDB document"""
        return {
            'x': position.x,
            'y': position.y,
            'rotation': position.rotation,
            'flip_state': position.flip_state.value if hasattr(position.flip_state, 'value') else position.flip_state
        }


class PlayerSerializer:
    @staticmethod
    def to_entity(doc: dict) -> Player:
        """Convert MongoDB document to Player entity"""
        deck = DeckSerializer.to_entity(doc['deck']) if doc.get('deck') else None
        hand = tuple(CardSerializer.to_entity(c) for c in doc.get('hand', [])) if doc.get('hand') else ()
        discard_pile = tuple(CardSerializer.to_entity(c) for c in doc.get('discard_pile', [])) if doc.get('discard_pile') else ()
        
        return Player(
            name=doc['name'],
            is_ready=doc.get('is_ready', False),
            is_host=doc.get('is_host', False),
            deck=deck,
            hand=hand,
            discard_pile=discard_pile
        )
    
    @staticmethod
    def to_doc(player: Player) -> dict:
        """Convert Player entity to MongoDB document"""
        return {
            'name': player.name,
            'is_ready': player.is_ready,
            'is_host': player.is_host,
            'deck': DeckSerializer.to_doc(player.deck) if player.deck else None,
            'hand': [CardSerializer.to_doc(card) for card in player.hand] if player.hand else [],
            'discard_pile': [CardSerializer.to_doc(card) for card in player.discard_pile] if player.discard_pile else []
        }


class DialSerializer:
    @staticmethod
    def to_entity(doc: dict) -> Dial:
        """Convert MongoDB document to Dial entity"""
        position = PositionSerializer.to_entity(doc['position'])
        return Dial(
            type=doc['type'],
            value=doc['value'],
            position=position
        )
    
    @staticmethod
    def to_doc(dial: Dial) -> dict:
        """Convert Dial entity to MongoDB document"""
        return {
            'type': dial.type,
            'value': dial.value,
            'position': PositionSerializer.to_doc(dial.position)
        }


class CardInPlaySerializer:
    @staticmethod
    def to_entity(doc: dict) -> CardInPlay:
        """Convert MongoDB document to CardInPlay entity"""
        position = PositionSerializer.to_entity(doc['position'])
        card = CardSerializer.to_entity(doc['card'])
        return CardInPlay(
            card=card,
            position=position,
            counters=doc.get('counters', {})
        )
    
    @staticmethod
    def to_doc(card_in_play: CardInPlay) -> dict:
        """Convert CardInPlay entity to MongoDB document"""
        return {
            'card': CardSerializer.to_doc(card_in_play.card),
            'position': PositionSerializer.to_doc(card_in_play.position),
            'counters': card_in_play.counters
        }


class DeckInPlaySerializer:
    @staticmethod
    def to_entity(doc: dict) -> DeckInPlay:
        """Convert MongoDB document to DeckInPlay entity"""
        deck = DeckSerializer.to_entity(doc['deck'])
        draw_position = PositionSerializer.to_entity(doc['draw_position'])
        discard_position = PositionSerializer.to_entity(doc['discard_position'])
        draw_pile = tuple(doc.get('draw_pile', []))
        discard_pile = tuple(doc.get('discard_pile', []))
        hand = tuple(doc.get('hand', []))
        
        return DeckInPlay(
            deck=deck,
            draw_position=draw_position,
            discard_position=discard_position,
            draw_pile=draw_pile,
            discard_pile=discard_pile,
            hand=hand
        )
    
    @staticmethod
    def to_doc(deck_in_play: DeckInPlay) -> dict:
        """Convert DeckInPlay entity to MongoDB document"""
        return {
            'deck': DeckSerializer.to_doc(deck_in_play.deck),
            'draw_position': PositionSerializer.to_doc(deck_in_play.draw_position),
            'discard_position': PositionSerializer.to_doc(deck_in_play.discard_position),
            'draw_pile': list(deck_in_play.draw_pile),
            'discard_pile': list(deck_in_play.discard_pile),
            'hand': list(deck_in_play.hand)
        }


class PlayZoneSerializer:
    @staticmethod
    def to_entity(doc: dict) -> PlayZone:
        """Convert MongoDB document to PlayZone entity"""
        encounter_deck = EncounterDeckInPlaySerializer.to_entity(doc['encounter_deck'])
        decks_in_play = tuple(
            DeckInPlaySerializer.to_entity(dip)
            for dip in doc.get('decks_in_play', [])
        )
        cards_in_play = tuple(
            CardInPlaySerializer.to_entity(cip)
            for cip in doc.get('cards_in_play', [])
        )
        dials = tuple(
            DialSerializer.to_entity(dial)
            for dial in doc.get('dials', [])
        )
        
        return PlayZone(
            encounter_deck=encounter_deck,
            decks_in_play=decks_in_play,
            cards_in_play=cards_in_play,
            dials=dials
        )
    
    @staticmethod
    def to_doc(play_zone: PlayZone) -> dict:
        """Convert PlayZone entity to MongoDB document"""
        return {
            'encounter_deck': EncounterDeckInPlaySerializer.to_doc(play_zone.encounter_deck),
            'decks_in_play': [DeckInPlaySerializer.to_doc(dip) for dip in play_zone.decks_in_play],
            'cards_in_play': [CardInPlaySerializer.to_doc(cip) for cip in play_zone.cards_in_play],
            'dials': [DialSerializer.to_doc(dial) for dial in play_zone.dials]
        }


class GameSerializer:
    @staticmethod
    def to_entity(doc: dict) -> Game:
        """Convert MongoDB document to Game entity"""
        phase = GamePhase(doc.get('phase', 'lobby'))
        
        players = tuple(
            PlayerSerializer.to_entity(p)
            for p in doc.get('players', [])
        )
        
        play_zone = None
        if 'play_zone' in doc and doc['play_zone']:
            play_zone = PlayZoneSerializer.to_entity(doc['play_zone'])
        
        encounter_deck = None
        if 'encounter_deck' in doc and doc['encounter_deck']:
            encounter_deck = EncounterDeckSerializer.to_entity(doc['encounter_deck'])
        
        return Game(
            id=doc['_id'],
            name=doc['name'],
            host=doc.get('host', ''),
            phase=phase,
            players=players,
            encounter_deck=encounter_deck,
            play_zone=play_zone,
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )
    
    @staticmethod
    def to_doc(game: Game) -> dict:
        """Convert Game entity to MongoDB document"""
        doc = {
            '_id': game.id,
            'name': game.name,
            'host': game.host,
            'phase': game.phase.value,
            'created_at': game.created_at or datetime.now()
        }
        
        doc['players'] = [PlayerSerializer.to_doc(p) for p in game.players]
        
        if game.play_zone:
            doc['play_zone'] = PlayZoneSerializer.to_doc(game.play_zone)
        
        if game.updated_at:
            doc['updated_at'] = game.updated_at
        
        if game.encounter_deck:
            doc['encounter_deck'] = EncounterDeckSerializer.to_doc(game.encounter_deck)
        
        return doc

class EncounterDeckSerializer:
    @staticmethod
    def to_entity(doc: dict) -> EncounterDeck:
        """Convert MongoDB document to EncounterDeck entity"""
        villian_cards = tuple(
            CardSerializer.to_entity(c)
            for c in doc.get('villian_cards', [])
        )
        main_scheme_cards = tuple(
            CardSerializer.to_entity(c)
            for c in doc.get('main_scheme_cards', [])
        )
        scenario_cards = tuple(
            CardSerializer.to_entity(c)
            for c in doc.get('scenario_cards', [])
        )
        
        return EncounterDeck(
            id=doc['deck_id'],
            name=doc['name'],
            cards=tuple(
                DeckCardSerializer.to_entity(dc)
                for dc in doc.get('cards', [])
            ),
            villian_cards=villian_cards,
            main_scheme_cards=main_scheme_cards,
            scenario_cards=scenario_cards,
            source_url=doc.get('source_url'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )
        
    @staticmethod
    def to_doc(encounter_deck: EncounterDeck) -> dict:
        """Convert EncounterDeck entity to MongoDB document"""
        return {
            'deck_id': encounter_deck.id,
            'name': encounter_deck.name,
            'cards': [DeckCardSerializer.to_doc(c) for c in encounter_deck.cards],
            'villian_cards': [CardSerializer.to_doc(c) for c in encounter_deck.villian_cards],
            'main_scheme_cards': [CardSerializer.to_doc(c) for c in encounter_deck.main_scheme_cards],
            'scenario_cards': [CardSerializer.to_doc(c) for c in encounter_deck.scenario_cards],
            'source_url': encounter_deck.source_url,
            'created_at': encounter_deck.created_at,
            'updated_at': encounter_deck.updated_at
        }
        
class EncounterDeckInPlaySerializer:
    @staticmethod
    def to_entity(doc: dict) -> EncounterDeckInPlay:
        """Convert MongoDB document to EncounterDeckInPlay entity for EncounterDeck"""
        encounterDeck = EncounterDeckSerializer.to_entity(doc['encounterDeck'])
        draw_position = PositionSerializer.to_entity(doc['draw_position'])
        discard_position = PositionSerializer.to_entity(doc['discard_position'])
        draw_pile = tuple(doc.get('draw_pile', []))
        discard_pile = tuple(doc.get('discard_pile', []))
        hand = tuple(doc.get('hand', []))
        
        return EncounterDeckInPlay(
            encounterDeck=encounterDeck,
            draw_position=draw_position,
            discard_position=discard_position,
            draw_pile=draw_pile,
            discard_pile=discard_pile
        )
    
    @staticmethod
    def to_doc(deck_in_play: EncounterDeckInPlay) -> dict:
        """Convert EncounterDeckInPlay entity for EncounterDeck to MongoDB document"""
        return {
            'encounterDeck': EncounterDeckSerializer.to_doc(deck_in_play.encounterDeck),
            'draw_position': PositionSerializer.to_doc(deck_in_play.draw_position),
            'discard_position': PositionSerializer.to_doc(deck_in_play.discard_position),
            'draw_pile': list(deck_in_play.draw_pile) if deck_in_play.draw_pile else [],
            'discard_pile': list(deck_in_play.discard_pile) if deck_in_play.discard_pile else []
        }