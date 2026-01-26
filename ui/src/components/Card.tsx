/**
 * Card Component - Used in PlayerHand
 * Displays a card with front and back images
 * Handles flip animation via 3D CSS
 */

import React from 'react';
import '../styles/Card.css';

export interface CardProps {
  code: string;
  name: string;
  frontImage: string;
  backImage: string;
  isFlipped?: boolean;
  onFlip?: () => void;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  code,
  name,
  frontImage,
  backImage,
  isFlipped = false,
  onFlip,
  className = '',
}) => {
  return (
    <div
      className={`card ${className}`}
      onClick={onFlip}
      style={{ perspective: '1000px' }}
    >
      <div
        className={`card-inner ${isFlipped ? 'flipped' : ''}`}
        style={{
          transformStyle: 'preserve-3d',
          transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}
      >
        {/* Front Face */}
        <div className="card-face card-front" style={{ backfaceVisibility: 'hidden' }}>
          <img src={frontImage} alt={name} className="card-image" />
          <div className="card-label">{code}</div>
        </div>

        {/* Back Face */}
        <div
          className="card-face card-back"
          style={{
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
        >
          <img src={backImage} alt="Card back" className="card-image" />
        </div>
      </div>
    </div>
  );
};

export default Card;