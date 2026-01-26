/**
 * InteractiveCard Component - Used on GameBoard
 * Extends Card with dragging, rotation, flipping, and context menu
 * Can be moved between zones (decks, discard piles, hands)
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card } from './Card';
import '../styles/InteractiveCard.css';

export interface InteractiveCardProps {
  code: string;
  name: string;
  frontImage: string;
  backImage: string;
  initialX?: number;
  initialY?: number;
  initialRotation?: number;
  initialFlipped?: boolean;
  onMove?: (x: number, y: number) => void;
  onRotate?: (rotation: number) => void;
  onFlip?: () => void;
  isDragging?: boolean;
  isSelected?: boolean;
}

export const InteractiveCard: React.FC<InteractiveCardProps> = ({
  code,
  name,
  frontImage,
  backImage,
  initialX = 0,
  initialY = 0,
  initialRotation = 0,
  initialFlipped = false,
  onMove,
  onRotate,
  onFlip,
  isSelected = false,
}) => {
  const [cardState, setCardState] = useState({
    x: initialX,
    y: initialY,
    rotation: initialRotation,
    isFlipped: initialFlipped,
  });

  const [isDragging, setIsDragging] = useState(false);
  const [isRotating, setIsRotating] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [examining, setExamining] = useState(false);
  const [clickTime, setClickTime] = useState(0);

  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;

    const rect = cardRef.current?.getBoundingClientRect();
    if (!rect) return;

    const clickX = e.clientX;
    const clickY = e.clientY;

    const corners = [
      { x: rect.left, y: rect.top },
      { x: rect.right, y: rect.top },
      { x: rect.left, y: rect.bottom },
      { x: rect.right, y: rect.bottom },
    ];

    const distancesToCorners = corners.map((corner) =>
      Math.sqrt(Math.pow(clickX - corner.x, 2) + Math.pow(clickY - corner.y, 2))
    );

    const minDistance = Math.min(...distancesToCorners);
    const isOnRotateHandle = minDistance <= 30;

    if (isOnRotateHandle) {
      setIsRotating(true);
      e.preventDefault();
      e.stopPropagation();
    } else {
      setIsDragging(true);
      setDragOffset({
        x: e.clientX - cardState.x,
        y: e.clientY - cardState.y,
      });

      if (!isOnRotateHandle) {
        const now = Date.now();
        if (now - clickTime < 300) {
          handleFlip();
        }
        setClickTime(now);
      }
    }
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      const newX = e.clientX - dragOffset.x;
      const newY = e.clientY - dragOffset.y;
      setCardState((prev) => ({
        ...prev,
        x: newX,
        y: newY,
      }));
      onMove?.(newX, newY);
    } else if (isRotating && cardRef.current) {
      const rect = cardRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX) * (180 / Math.PI);

      const newRotation = angle + 90;
      setCardState((prev) => ({
        ...prev,
        rotation: newRotation,
      }));
      onRotate?.(newRotation);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsRotating(false);
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY });
  };

  const handleFlip = () => {
    setCardState((prev) => ({
      ...prev,
      isFlipped: !prev.isFlipped,
    }));
    onFlip?.();
  };

  const closeContextMenu = () => {
    setContextMenu(null);
  };

  const examineCard = () => {
    setExamining(true);
    closeContextMenu();
  };

  const closeExamine = () => {
    setExamining(false);
  };

  useEffect(() => {
    if (isDragging || isRotating) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
    return undefined;
  }, [isDragging, isRotating, dragOffset, cardState]);

  useEffect(() => {
    if (contextMenu) {
      const handler = closeContextMenu;
      window.addEventListener('click', handler);
      return () => window.removeEventListener('click', handler);
    }
    return undefined;
  }, [contextMenu]);

  return (
    <>
      {/* Card on board */}
      <div
        ref={cardRef}
        className={`interactive-card ${isSelected ? 'selected' : ''}`}
        style={{
          left: `${cardState.x}px`,
          top: `${cardState.y}px`,
          transform: `rotate(${cardState.rotation}deg)`,
          transformOrigin: 'center center',
        }}
        onMouseDown={handleMouseDown}
        onContextMenu={handleContextMenu}
      >
        <Card
          code={code}
          name={name}
          frontImage={frontImage}
          backImage={backImage}
          isFlipped={cardState.isFlipped}
          className="pointer-events-none"
        />
        {isRotating && <div className="rotation-handle" />}
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div className="context-menu" style={{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }}>
          <button className="menu-item" onClick={examineCard}>
            Examine Card
          </button>
          <button className="menu-item" onClick={handleFlip}>
            Flip Card
          </button>
          <button
            className="menu-item"
            onClick={() => {
              setCardState((prev) => ({ ...prev, rotation: 0 }));
              closeContextMenu();
            }}
          >
            Reset Rotation
          </button>
        </div>
      )}

      {/* Examine Modal */}
      {examining && (
        <div className="examine-modal" onClick={closeExamine}>
          <div className="examine-content" onClick={(e) => e.stopPropagation()}>
            <button className="examine-close" onClick={closeExamine}>
              ✕
            </button>
            <Card
              code={code}
              name={name}
              frontImage={frontImage}
              backImage={backImage}
              isFlipped={cardState.isFlipped}
              onFlip={handleFlip}
              className="examine-card"
            />
            <p className="examine-help">Click card to flip • Click outside to close</p>
          </div>
        </div>
      )}
    </>
  );
};

/**
 * Utility function to convert from Card type to InteractiveCard
 */
export function createInteractiveCard(
  card: any,
  initialX: number = 0,
  initialY: number = 0,
  initialRotation: number = 0,
  initialFlipped: boolean = false
): InteractiveCardProps {
  return {
    code: card.code,
    name: card.name,
    frontImage: card.image_url || 'https://via.placeholder.com/200x300?text=No+Image',
    backImage: 'https://images.unsplash.com/photo-1618269548381-4f965b3e3e49?w=400&h=600&fit=crop',
    initialX,
    initialY,
    initialRotation,
    initialFlipped,
  };
}

export default InteractiveCard;