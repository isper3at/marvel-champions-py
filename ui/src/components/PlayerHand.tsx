/**
 * PlayerHand component - Displays splayed hand of cards at bottom of screen
 * Cards fan out, hover to bring card forward
 */

import React, { useState } from 'react';
import { Card as CardType } from '../types';
import { Card } from './Card';
import '../styles/PlayerHand.css';

interface PlayerHandProps {
  cards: CardType[];
  playerName: string;
  onCardClick?: (card: CardType) => void;
  onCardDragStart?: (card: CardType, e: React.DragEvent) => void;
}

export const PlayerHand: React.FC<PlayerHandProps> = ({
  cards,
  playerName,
  onCardClick,
  onCardDragStart,
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const getCardStyle = (index: number): React.CSSProperties => {
    const totalCards = cards.length;
    const angle = (index - (totalCards - 1) / 2) * 8; // Spread angle
    const yOffset = Math.abs(index - (totalCards - 1) / 2) * 3; // Slight vertical curve

    return {
      transform: `rotate(${angle}deg) translateY(${yOffset}px)`,
      zIndex: hoveredIndex === index ? 1000 : index,
    };
  };

  return (
    <div className="player-hand">
      <h3 className="hand-label">{playerName}'s Hand</h3>
      <div className="hand-container">
        {cards.length === 0 ? (
          <p className="empty-hand">No cards in hand</p>
        ) : (
          cards.map((card, index) => (
            <div
              key={`${card.code}-${index}`}
              className="hand-card-wrapper"
              style={getCardStyle(index)}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <Card
                card={card}
                onClick={() => onCardClick?.(card)}
                onDragStart={(e) => onCardDragStart?.(card, e)}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
};
