/**
 * PlayerZone component - Player's board area showing play field, resources, threats
 * Located above player hand, below encounter zone
 */

import React from 'react';
import { Player } from '../types';
import { Card } from './Card';
import '../styles/PlayerZone.css';

interface PlayerZoneProps {
  player: Player;
  playerName: string;
  onDeckClick?: () => void;
}

export const PlayerZone: React.FC<PlayerZoneProps> = ({
  player,
  playerName,
  onDeckClick,
}) => {
  return (
    <div className="player-zone">
      <div className="player-zone-header">
        <h3>{playerName}'s Play Area</h3>
      </div>

      <div className="player-zones-container">
        {/* Play Field */}
        <div className="zone-section">
          <h4 className="zone-title">Play Field</h4>
          <div className="zone-content">
            {player.zones.play_field.length === 0 ? (
              <p className="empty-zone">No cards in play</p>
            ) : (
              <div className="cards-grid">
                {player.zones.play_field.map((card) => (
                  <div key={card.id} className="card-in-zone">
                    <Card
                      card={card}
                      isInPlay={true}
                      faceDown={card.face_down}
                      style={{
                        width: '100px',
                        height: '150px',
                      }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Resource Zone */}
        <div className="zone-section">
          <h4 className="zone-title">Resources</h4>
          <div className="zone-content">
            {player.zones.resource_zone.length === 0 ? (
              <p className="empty-zone">No resources</p>
            ) : (
              <div className="cards-grid">
                {player.zones.resource_zone.map((card) => (
                  <div key={card.id} className="card-in-zone">
                    <Card
                      card={card}
                      isInPlay={true}
                      faceDown={card.face_down}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Threat Zone */}
        <div className="zone-section">
          <h4 className="zone-title">Threats</h4>
          <div className="zone-content">
            {player.zones.threat_zone.length === 0 ? (
              <p className="empty-zone">No threats</p>
            ) : (
              <div className="cards-grid">
                {player.zones.threat_zone.map((card) => (
                  <div key={card.id} className="card-in-zone">
                    <Card
                      card={card}
                      isInPlay={true}
                      faceDown={card.face_down}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Deck controls */}
      <div className="deck-controls">
        <button className="deck-button" onClick={onDeckClick}>
          📋 View Deck
        </button>
      </div>
    </div>
  );
};
