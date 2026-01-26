/**
 * DeckView Component - Displays a deck that players can draw from
 * Double-click to draw a card
 * Click and drag to manually draw the top card as an InteractiveCard
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card as CardType } from '../types';
import { Card } from './Card';
import { InteractiveCard } from './InteractiveCard';
import '../styles/DeckView.css';

export interface DeckViewProps {
  deckName: string;
  cards: CardType[];
  backImage?: string;
  position?: { x: number; y: number };
  onCardDrawn?: (card: CardType, position: { x: number; y: number }) => void;
  onDeckEmpty?: () => void;
  isPlayerDeck?: boolean;
  canDraw?: boolean;
  className?: string;
}

interface DrawnCard extends CardType {
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
  rotation: number;
  isBeingDragged: boolean;
}

export const DeckView: React.FC<DeckViewProps> = ({
  deckName,
  cards,
  backImage = 'https://images.unsplash.com/photo-1618269548381-4f965b3e3e49?w=400&h=600&fit=crop',
  position = { x: 0, y: 0 },
  onCardDrawn,
  onDeckEmpty,
  isPlayerDeck = true,
  canDraw = true,
  className = '',
}) => {
  const [drawnCards, setDrawnCards] = useState<DrawnCard[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [draggedCardIndex, setDraggedCardIndex] = useState<number | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [lastClickTime, setLastClickTime] = useState(0);
  const deckRef = useRef<HTMLDivElement>(null);

  /**
   * Draw the top card from the deck
   */
  const drawCard = () => {
    if (cards.length === 0) {
      onDeckEmpty?.();
      return;
    }

    const topCard = cards[0];
    const deckRect = deckRef.current?.getBoundingClientRect();
    const startPosition = {
      x: deckRect?.x || position.x,
      y: deckRect?.y || position.y,
    };

    const drawnCard: DrawnCard = {
      ...topCard,
      startX: startPosition.x,
      startY: startPosition.y,
      currentX: startPosition.x,
      currentY: startPosition.y,
      rotation: 0,
      isBeingDragged: false,
    };

    setDrawnCards((prev) => [...prev, drawnCard]);
    onCardDrawn?.(topCard, startPosition);
  };

  /**
   * Handle deck click (double-click to draw)
   */
  const handleDeckClick = () => {
    if (!canDraw || cards.length === 0) return;

    const now = Date.now();
    const isDoubleClick = now - lastClickTime < 300;
    setLastClickTime(now);

    if (isDoubleClick) {
      drawCard();
    }
  };

  /**
   * Handle starting to drag a card from the deck
   */
  const handleDeckMouseDown = (e: React.MouseEvent) => {
    if (!canDraw || cards.length === 0 || e.button !== 0) return;

    e.preventDefault();

    const deckRect = deckRef.current?.getBoundingClientRect();
    if (!deckRect) return;

    setIsDragging(true);
    setDraggedCardIndex(0);
    setDragOffset({
      x: e.clientX - deckRect.x,
      y: e.clientY - deckRect.y,
    });
  };

  /**
   * Handle dragging the card
   */
  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || draggedCardIndex === null) return;

    const deckRect = deckRef.current?.getBoundingClientRect();
    if (!deckRect) return;

    if (drawnCards.length > draggedCardIndex) {
      setDrawnCards((prev) =>
        prev.map((card, idx) =>
          idx === draggedCardIndex
            ? {
                ...card,
                currentX: e.clientX - dragOffset.x,
                currentY: e.clientY - dragOffset.y,
                isBeingDragged: true,
              }
            : card
        )
      );
    } else {
      const topCard = cards[0];
      const drawnCard: DrawnCard = {
        ...topCard,
        startX: deckRect.x,
        startY: deckRect.y,
        currentX: e.clientX - dragOffset.x,
        currentY: e.clientY - dragOffset.y,
        rotation: 0,
        isBeingDragged: true,
      };
      setDrawnCards((prev) => [...prev, drawnCard]);
    }
  };

  /**
   * Handle dropping the card
   */
  const handleMouseUp = () => {
    if (isDragging && draggedCardIndex !== null && drawnCards.length > draggedCardIndex) {
      setIsDragging(false);
      setDraggedCardIndex(null);

      setDrawnCards((prev) =>
        prev.map((card, idx) =>
          idx === draggedCardIndex
            ? {
                ...card,
                isBeingDragged: false,
              }
            : card
        )
      );
    }
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseMove);
      };
    }
    return undefined;
  }, [isDragging, dragOffset, draggedCardIndex]);

  const cardsRemaining = cards.length;

  return (
    <div className={`deck-view ${className}`}>
      {/* Deck Stack */}
      <div
        ref={deckRef}
        className={`deck-stack ${!canDraw || cardsRemaining === 0 ? 'disabled' : ''}`}
        onClick={handleDeckClick}
        onMouseDown={handleDeckMouseDown}
      >
        {cardsRemaining > 0 ? (
          <>
            {[2, 1, 0].map((offset) => (
              <div key={offset} className={`deck-layer deck-layer-${offset}`}>
                <Card
                  code="card-back"
                  name={deckName}
                  frontImage="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 150'%3E%3Crect fill='%234a4a6a' width='100' height='150'/%3E%3C/svg%3E"
                  backImage={backImage}
                  isFlipped={true}
                  className="deck-card"
                />
              </div>
            ))}
            <div className="deck-label">
              <span className="deck-name">{deckName}</span>
              <span className="card-count">{cardsRemaining}</span>
            </div>
            <div className="deck-hint">
              {isPlayerDeck ? (
                <>
                  <div className="hint-text">Double-click to draw</div>
                  <div className="hint-text">Drag to draw & play</div>
                </>
              ) : (
                <div className="hint-text">Click to draw</div>
              )}
            </div>
          </>
        ) : (
          <>
            <div className="deck-empty">
              <span>Empty</span>
            </div>
            <div className="deck-label">
              <span className="deck-name">{deckName}</span>
              <span className="card-count">0</span>
            </div>
          </>
        )}
      </div>

      {/* Drawn Cards - Interactive on the board */}
      {drawnCards.map((drawnCard, index) => (
        <InteractiveCard
          key={`drawn-${index}`}
          code={drawnCard.code}
          name={drawnCard.name}
          frontImage={drawnCard.image_url || 'https://via.placeholder.com/120x180?text=No+Image'}
          backImage={backImage}
          initialX={drawnCard.currentX}
          initialY={drawnCard.currentY}
          initialRotation={drawnCard.rotation}
          initialFlipped={true}
          isDragging={drawnCard.isBeingDragged}
          onMove={(x, y) => {
            setDrawnCards((prev) =>
              prev.map((card, idx) =>
                idx === index ? { ...card, currentX: x, currentY: y } : card
              )
            );
          }}
          onRotate={(rotation) => {
            setDrawnCards((prev) =>
              prev.map((card, idx) =>
                idx === index ? { ...card, rotation } : card
              )
            );
          }}
        />
      ))}
    </div>
  );
};

export default DeckView;