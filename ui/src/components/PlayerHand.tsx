/**
 * PlayerHand Component - Displays cards in an arc at the bottom of the screen
 * Allows adding/removing cards from the hand
 */

import React, { useState } from 'react';
import { Card as CardType } from '../types';
import { Card } from './Card';
import '../styles/PlayerHand.css';

export interface PlayerHandProps {
  cards: CardType[];
  onAddCard?: (card: CardType) => void;
  onRemoveCard?: (cardCode: string) => void;
  onCardFlip?: (cardCode: string) => void;
  onCardSelected?: (cardCode: string | null) => void;
}

export const PlayerHand: React.FC<PlayerHandProps> = ({
  cards,
  onAddCard,
  onRemoveCard,
  onCardFlip,
  onCardSelected,
}) => {
  const [flippedCards, setFlippedCards] = useState<Set<string>>(new Set());
  const [selectedCard, setSelectedCard] = useState<string | null>(null);
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  /**
   * Add a card to the hand
   */
  const addCard = (card: CardType) => {
    onAddCard?.(card);
  };

  /**
   * Remove a card from the hand by code
   */
  const removeCard = (cardCode: string) => {
    setFlippedCards((prev) => {
      const updated = new Set(prev);
      updated.delete(cardCode);
      return updated;
    });
    if (selectedCard === cardCode) {
      setSelectedCard(null);
    }
    onRemoveCard?.(cardCode);
  };

  /**
   * Toggle flip state of a card
   */
  const toggleCardFlip = (cardCode: string) => {
    setFlippedCards((prev) => {
      const updated = new Set(prev);
      if (updated.has(cardCode)) {
        updated.delete(cardCode);
      } else {
        updated.add(cardCode);
      }
      return updated;
    });
    onCardFlip?.(cardCode);
  };

  /**
   * Select/deselect a card
   */
  const toggleCardSelection = (cardCode: string) => {
    const newSelected = selectedCard === cardCode ? null : cardCode;
    setSelectedCard(newSelected);
    onCardSelected?.(newSelected);
  };

  /**
   * Calculate card position in arc
   */
  const getCardStyle = (index: number, total: number) => {
    const spread = 60; // degrees of arc spread
    const arcRadius = 400; // radius of the arc
    const cardWidth = 120;
    const cardHeight = 180;

    // Calculate angle for this card
    const startAngle = -spread / 2;
    const angleStep = total > 1 ? spread / (total - 1) : 0;
    const angle = startAngle + angleStep * index;

    // Calculate position on arc
    const radian = (angle * Math.PI) / 180;
    const x = Math.sin(radian) * arcRadius;
    const y = arcRadius - Math.cos(radian) * arcRadius;

    const isHovered = hoveredCard === cards[index].code;
    const isSelected = selectedCard === cards[index].code;

    return {
      position: 'absolute' as const,
      width: `${cardWidth}px`,
      height: `${cardHeight}px`,
      left: '50%',
      bottom: isHovered || isSelected ? '60px' : '0px',
      transform: `translateX(calc(-50% + ${x}px)) translateY(${isHovered || isSelected ? -40 : y}px) rotate(${isHovered || isSelected ? 0 : angle}deg)`,
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      zIndex: isHovered || isSelected ? 100 : 10 + index,
    };
  };

  return (
    <div className="player-hand">
      <div className="hand-container">
        <div className="hand-info">
          <h3>Hand ({cards.length})</h3>
          {selectedCard && (
            <div className="selected-info">
              Selected: {cards.find((c) => c.code === selectedCard)?.name}
            </div>
          )}
        </div>

        <div className="hand-cards-area">
          {cards.length === 0 ? (
            <div className="empty-hand">
              <p>No cards in hand</p>
            </div>
          ) : (
            <div className="hand-arc">
              {cards.map((card, index) => (
                <div
                  key={card.code}
                  style={getCardStyle(index, cards.length)}
                  onMouseEnter={() => setHoveredCard(card.code)}
                  onMouseLeave={() => setHoveredCard(null)}
                  className="hand-card-wrapper"
                >
                  <div className="hand-card-container">
                    <Card
                      code={card.code}
                      name={card.name}
                      frontImage={card.image_url || 'https://via.placeholder.com/120x180?text=No+Image'}
                      backImage="https://images.unsplash.com/photo-1618269548381-4f965b3e3e49?w=400&h=600&fit=crop"
                      isFlipped={flippedCards.has(card.code)}
                      onFlip={() => toggleCardFlip(card.code)}
                      className={`${selectedCard === card.code ? 'selected' : ''}`}
                    />
                    <div className="card-controls">
                      <button
                        className="control-btn select-btn"
                        onClick={() => toggleCardSelection(card.code)}
                        title={selectedCard === card.code ? 'Deselect' : 'Select'}
                      >
                        ◉
                      </button>
                      <button
                        className="control-btn remove-btn"
                        onClick={() => removeCard(card.code)}
                        title="Remove from hand"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Example usage section (can be removed in production) */}
        <div className="hand-controls">
          <h4>Hand Controls</h4>
          <div className="control-buttons">
            <button
              className="btn btn-add"
              onClick={() => {
                const exampleCard: CardType = {
                  code: `card-${Date.now()}`,
                  name: `Test Card ${cards.length + 1}`,
                  text: 'This is a test card',
                  image_url: undefined,
                };
                addCard(exampleCard);
              }}
            >
              + Add Card
            </button>
            {selectedCard && (
              <button
                className="btn btn-remove"
                onClick={() => {
                  removeCard(selectedCard);
                }}
              >
                - Remove Selected
              </button>
            )}
            <button
              className="btn btn-clear"
              onClick={() => {
                cards.forEach((card) => removeCard(card.code));
              }}
              disabled={cards.length === 0}
            >
              Clear Hand
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerHand;