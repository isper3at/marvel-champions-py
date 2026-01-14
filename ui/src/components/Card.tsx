/**
 * Card component - Displays individual cards with hover effects
 */

import React, { useState } from 'react';
import { Card as CardType, CardInPlay } from '../types';
import '../styles/Card.css';

interface CardProps {
  card: CardType | CardInPlay;
  isInPlay?: boolean;
  faceDown?: boolean;
  onDragStart?: (e: React.DragEvent) => void;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({
  card,
  isInPlay = false,
  faceDown = false,
  onDragStart,
  onClick,
  className = '',
  style = {},
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const cardData = card as CardType;
  const inPlayData = card as CardInPlay;

  return (
    <div
      className={`card ${faceDown ? 'face-down' : ''} ${className}`}
      draggable
      onDragStart={onDragStart}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        ...style,
        transform: isHovered && !isInPlay ? 'translateY(-20px)' : '',
        zIndex: isHovered ? 1000 : 'auto',
      }}
    >
      {faceDown ? (
        <div className="card-back">
          <div className="card-back-pattern" />
        </div>
      ) : (
        <div className="card-front">
          <div className="card-image">
            {cardData.image_url && (
              <img src={cardData.image_url} alt={cardData.name} />
            )}
          </div>
          <div className="card-info">
            <h3 className="card-name">{cardData.name}</h3>
            <p className="card-text">{cardData.text}</p>
          </div>
          {isInPlay && inPlayData.counter !== undefined && (
            <div className="card-counter">{inPlayData.counter}</div>
          )}
          {isInPlay && inPlayData.rotated && (
            <div className="card-rotated-indicator">↻</div>
          )}
        </div>
      )}
    </div>
  );
};
