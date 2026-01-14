/**
 * Core type definitions for Marvel Champions Game UI
 */

export interface Card {
  code: string;
  name: string;
  text: string;
  image_url?: string;
  pack_code?: string;
}

export interface Position {
  x: number;
  y: number;
}

export interface CardInPlay extends Card {
  id: string;
  position: Position;
  face_down: boolean;
  rotated: boolean;
  counter?: number;
}

export interface PlayerZones {
  hand: Card[];
  play_field: CardInPlay[];
  resource_zone: CardInPlay[];
  threat_zone: CardInPlay[];
  discard_pile: Card[];
}

export interface Deck {
  id: string;
  name: string;
  cards: Card[];
}

export interface Player {
  name: string;
  id: string;
  hand_size: number;
  zones: PlayerZones;
}

export interface EncounterZone {
  deck: Card[];
  discard_pile: Card[];
  in_play: CardInPlay[];
}

export interface GameState {
  id: string;
  name: string;
  players: Player[];
  encounter_zone: EncounterZone;
  current_player: string;
  status: 'active' | 'paused' | 'finished';
}

export interface DragItem {
  type: 'card';
  card: CardInPlay | Card;
  source_zone: string;
  source_player?: string;
}

export type DropZoneType = 
  | 'player_hand' 
  | 'player_field' 
  | 'player_resource' 
  | 'player_threat'
  | 'encounter_field'
  | 'encounter_discard'
  | 'opponent_field';
