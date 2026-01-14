/**
 * OpponentZone component - Compact display of opponent's game state
 * Shows their board state and hand (as card backs) in smaller size
 * Positioned on sides/top based on number of players
 */

import React from 'react';
import { Player, CardInPlay } from '../types';
import { Card } from './Card';
import '../styles/OpponentZone.css';

interface OpponentZoneProps {
  player: Player;
  position?: 'top-left' | 'top-right' | 'left' | 'right';
}

export const OpponentZone: React.FC<OpponentZoneProps> = ({
  player,
  position = 'top-left',
}) => {
  const allInPlay: CardInPlay[] = [
    ...player.zones.play_field,
    ...player.zones.resource_zone,
    ...player.zones.threat_zone,
  ];

  return (
    <div className={`opponent-zone opponent-zone-${position}`}>
      <div className="opponent-header">
        <h4 className="opponent-name">{player.name}</h4>
        <span className="hand-size">Hand: {player.hand_size}</span>
      </div>

      <div className="opponent-board">
        {allInPlay.length === 0 ? (
          <p className="empty-board">No cards in play</p>
        ) : (
          <div className="compact-cards-grid">
            {allInPlay.map((card) => (
              <div key={card.id} className="compact-card">
                <Card
                  card={card}
                  isInPlay={true}
                  faceDown={card.face_down}
                  style={{ width: '80px', height: '120px' }}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="opponent-hand">
        <div className="hand-label">Hand ({player.hand_size})</div>
        <div className="hand-backs">
          {Array.from({ length: player.hand_size }).map((_, i) => (
            <div key={`back-${i}`} className="card-back-compact">
              <div className="card-back-pattern" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
