/**
 * GameBoard component - Main game container
 * Orchestrates layout: opponent zones, encounter zone, player zone, player hand
 * Handles drag-drop and game state management
 */

import React, { useState, useEffect } from 'react';
import { GameState, Card as CardType } from '../types';
import { PlayerHand } from './PlayerHand';
import { EncounterZone } from './EncounterZone';
import { PlayerZone } from './PlayerZone';
import { OpponentZone } from './OpponentZone';
import { DeckView } from './DeckView';
import { gameAPI } from '../utils/api';
import '../styles/GameBoard.css';

interface GameBoardProps {
  gameId: string;
  playerName: string;
}

export const GameBoard: React.FC<GameBoardProps> = ({
  gameId,
  playerName,
}) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [deckViewOpen, setDeckViewOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load game state
  useEffect(() => {
    const loadGame = async () => {
      try {
        const game = await gameAPI.getGame(gameId);
        setGameState(game);
        setLoading(false);
      } catch (err) {
        setError('Failed to load game');
        setLoading(false);
      }
    };

    loadGame();
    // Poll for updates every 2 seconds
    const interval = setInterval(loadGame, 2000);
    return () => clearInterval(interval);
  }, [gameId]);

  if (loading) return <div className="game-board loading">Loading game...</div>;
  if (error) return <div className="game-board error">{error}</div>;
  if (!gameState) return <div className="game-board error">Game not found</div>;

  const currentPlayer = gameState.players.find((p) => p.name === playerName);
  const opponents = gameState.players.filter((p) => p.name !== playerName);

  if (!currentPlayer) return <div className="game-board error">Player not found</div>;

  // Drag handlers
  const handleCardDragStart = (card: CardType, e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('card', JSON.stringify(card));
  };

  const handlePlayCardClick = async (card: CardType) => {
    try {
      await gameAPI.playCard(gameId, playerName, card.code, 'play_field');
      // Refresh game state
      const updated = await gameAPI.getGame(gameId);
      setGameState(updated);
    } catch (err) {
      console.error('Failed to play card:', err);
    }
  };

  const handleDrawEncounterClick = async () => {
    try {
      await gameAPI.drawEncounterCard(gameId);
      const updated = await gameAPI.getGame(gameId);
      setGameState(updated);
    } catch (err) {
      console.error('Failed to draw encounter card:', err);
    }
  };

  const handleDeckViewAction = async (
    card: CardType,
    action: 'move-hand' | 'move-play' | 'shuffle-back'
  ) => {
    try {
      switch (action) {
        case 'move-hand':
          await gameAPI.playCard(gameId, playerName, card.code, 'hand');
          break;
        case 'move-play':
          await gameAPI.playCard(gameId, playerName, card.code, 'play_field');
          break;
        case 'shuffle-back':
          await gameAPI.shuffleEncounterDiscard(gameId);
          break;
      }
      const updated = await gameAPI.getGame(gameId);
      setGameState(updated);
    } catch (err) {
      console.error('Action failed:', err);
    }
  };

  return (
    <div className="game-board">
      {/* Opponent zones */}
      <div className="opponent-zones">
        {opponents.map((opponent, index) => (
          <OpponentZone
            key={opponent.id}
            player={opponent}
            position={getOpponentPosition(index, opponents.length)}
          />
        ))}
      </div>

      {/* Main game area */}
      <div className="main-game-area">
        {/* Encounter zone */}
        <EncounterZone
          zone={gameState.encounter_zone}
          onDeckClick={handleDrawEncounterClick}
          onDiscardClick={() => setDeckViewOpen(true)}
        />

        {/* Player zone (board) */}
        <PlayerZone
          player={currentPlayer}
          playerName={playerName}
          onDeckClick={() => setDeckViewOpen(true)}
        />
      </div>

      {/* Player hand */}
      <PlayerHand
        cards={currentPlayer.zones.hand}
        playerName={playerName}
        onCardClick={handlePlayCardClick}
        onCardDragStart={handleCardDragStart}
      />

      {/* Deck view modal */}
      <DeckView
        deckCards={currentPlayer.zones.discard_pile}
        encounterCards={gameState.encounter_zone.deck}
        discardCards={gameState.encounter_zone.discard_pile}
        onCardAction={handleDeckViewAction}
        isOpen={deckViewOpen}
        onClose={() => setDeckViewOpen(false)}
      />
    </div>
  );
};

function getOpponentPosition(
  index: number,
  total: number
): 'top-left' | 'top-right' | 'left' | 'right' {
  if (total === 1) return 'top-left';
  if (total === 2) return index === 0 ? 'top-left' : 'top-right';
  return index % 2 === 0 ? 'left' : 'right';
}
