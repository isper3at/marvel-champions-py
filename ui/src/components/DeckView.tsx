/**
 * DeckView component - List view of deck cards with context-dependent actions
 * Shows cards from deck, encounter deck, and discard pile
 */

import React, { useState } from 'react';
import { Card as CardType } from '../types';
import '../styles/DeckView.css';

interface DeckViewProps {
  deckCards: CardType[];
  encounterCards: CardType[];
  discardCards: CardType[];
  onCardAction?: (card: CardType, action: 'move-hand' | 'move-play' | 'shuffle-back') => void;
  isOpen: boolean;
  onClose?: () => void;
}

type DeckSection = 'deck' | 'encounter' | 'discard';

export const DeckView: React.FC<DeckViewProps> = ({
  deckCards,
  encounterCards,
  discardCards,
  onCardAction,
  isOpen,
  onClose,
}) => {
  const [activeSection, setActiveSection] = useState<DeckSection>('deck');

  if (!isOpen) return null;

  const getSectionCards = (): CardType[] => {
    switch (activeSection) {
      case 'encounter':
        return encounterCards;
      case 'discard':
        return discardCards;
      default:
        return deckCards;
    }
  };

  const getAvailableActions = (): string[] => {
    switch (activeSection) {
      case 'deck':
        return ['move-hand', 'move-play'];
      case 'encounter':
        return ['move-hand', 'move-play'];
      case 'discard':
        return ['shuffle-back', 'move-hand'];
      default:
        return [];
    }
  };

  const cards = getSectionCards();
  const actions = getAvailableActions();

  return (
    <div className="deck-view-overlay">
      <div className="deck-view-modal">
        <div className="deck-view-header">
          <h2>Deck View</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="section-tabs">
          <button
            className={`tab ${activeSection === 'deck' ? 'active' : ''}`}
            onClick={() => setActiveSection('deck')}
          >
            Deck ({deckCards.length})
          </button>
          <button
            className={`tab ${activeSection === 'encounter' ? 'active' : ''}`}
            onClick={() => setActiveSection('encounter')}
          >
            Encounter ({encounterCards.length})
          </button>
          <button
            className={`tab ${activeSection === 'discard' ? 'active' : ''}`}
            onClick={() => setActiveSection('discard')}
          >
            Discard ({discardCards.length})
          </button>
        </div>

        <div className="deck-view-content">
          <div className="cards-list">
            {cards.length === 0 ? (
              <p className="empty-message">No cards in this section</p>
            ) : (
              cards.map((card, index) => (
                <div key={`${card.code}-${index}`} className="card-list-item">
                  <div className="card-info">
                    <span className="card-name">{card.name}</span>
                    <span className="card-code">{card.code}</span>
                  </div>
                  <div className="card-actions">
                    {actions.map((action) => (
                      <button
                        key={action}
                        className={`action-button ${action}`}
                        onClick={() =>
                          onCardAction?.(
                            card,
                            action as 'move-hand' | 'move-play' | 'shuffle-back'
                          )
                        }
                      >
                        {getActionLabel(action)}
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

function getActionLabel(action: string): string {
  switch (action) {
    case 'move-hand':
      return 'To Hand';
    case 'move-play':
      return 'To Play';
    case 'shuffle-back':
      return 'Shuffle Back';
    default:
      return action;
  }
}
