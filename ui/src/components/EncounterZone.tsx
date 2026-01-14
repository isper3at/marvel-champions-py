/**
 * EncounterZone component - Large drag-and-drop area for encounter cards
 * Deck and discard on left, main play area in center
 */

import React from 'react';
import { CardInPlay, EncounterZone as EncounterZoneType } from '../types';
import { Card } from './Card';
import '../styles/EncounterZone.css';

interface EncounterZoneProps {
  zone: EncounterZoneType;
  onDeckClick?: () => void;
  onDiscardClick?: () => void;
  onDragOver?: (e: React.DragEvent) => void;
  onDrop?: (e: React.DragEvent) => void;
  onCardClick?: (card: CardInPlay) => void;
}

export const EncounterZone: React.FC<EncounterZoneProps> = ({
  zone,
  onDeckClick,
  onDiscardClick,
  onDragOver,
  onDrop,
  onCardClick,
}) => {
  return (
    <div
      className="encounter-zone"
      onDragOver={onDragOver}
      onDrop={onDrop}
    >
      {/* Left sidebar with deck and discard */}
      <div className="encounter-sidebar">
        <div className="deck-stack" onClick={onDeckClick}>
          <div className="stack-label">Deck</div>
          <div className="stack-count">{zone.deck.length}</div>
          {zone.deck.length > 0 && (
            <Card card={zone.deck[0]} faceDown={true} />
          )}
        </div>

        <div className="discard-stack" onClick={onDiscardClick}>
          <div className="stack-label">Discard</div>
          <div className="stack-count">{zone.discard_pile.length}</div>
          {zone.discard_pile.length > 0 && (
            <Card card={zone.discard_pile[zone.discard_pile.length - 1]} />
          )}
        </div>
      </div>

      {/* Main play area */}
      <div className="encounter-play-area">
        <div className="play-area-label">Encounter Zone</div>
        <div className="cards-in-play">
          {zone.in_play.length === 0 ? (
            <p className="empty-zone">Drag cards here</p>
          ) : (
            zone.in_play.map((card) => (
              <div
                key={card.id}
                className="in-play-card"
                style={{
                  left: `${card.position.x}px`,
                  top: `${card.position.y}px`,
                  transform: card.rotated ? 'rotate(90deg)' : '',
                }}
                onClick={() => onCardClick?.(card)}
              >
                <Card
                  card={card}
                  isInPlay={true}
                  faceDown={card.face_down}
                />
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
