/**
 * GameBoard - Main game interface with draggable cards and deck management
 */

import React, { useState, useEffect } from 'react';
import { gameAPI } from '../utils/lobbyAPI';
import { GameState } from '../types';
import '../styles/GameBoard.css';

interface GameBoardProps {
  gameId: string;
  playerName: string;
}

export const GameBoard: React.FC<GameBoardProps> = ({ gameId, playerName }) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  // Load game state
  useEffect(() => {
    const loadGame = async () => {
      try {
        const state = await gameAPI.getGame(gameId);
        setGameState(state);
        setError('');
      } catch (err) {
        console.error('Failed to load game:', err);
        setError('Failed to load game state');
      } finally {
        setLoading(false);
      }
    };

    loadGame();
    const interval = setInterval(loadGame, 3000);
    return () => clearInterval(interval);
  }, [gameId]);

  const currentPlayer = gameState?.players.find((p) => p.name === playerName);

  if (loading) {
    return <div className="game-board loading">Loading game...</div>;
  }

  if (!gameState || !currentPlayer) {
    return <div className="game-board error">{error || 'Game not found'}</div>;
  }

  return (
    <div className="game-board">
      <div className="game-container">
        {/* Top - Opponent Zone */}
        <div className="opponent-zone">
          <h3>Opponents</h3>
          <div className="opponents-area">
            {gameState.players
              .filter((p) => p.name !== playerName)
              .map((opponent) => (
                <div key={opponent.id} className="opponent-card">
                  <h4>{opponent.name}</h4>
                  <div className="opponent-info">
                    <div className="opponent-stat">
                      <span className="label">Hand:</span>
                      <span className="value">{opponent.zones.hand.length}</span>
                    </div>
                    <div className="opponent-stat">
                      <span className="label">In Play:</span>
                      <span className="value">{opponent.zones.play_field.length}</span>
                    </div>
                  </div>
                  <div className="opponent-deck">
                    <div className="deck-stack">🂠</div>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Middle - Play Area */}
        <div className="play-area">
          {/* Left - Encounter Deck */}
          <div className="encounter-area">
            <div className="encounter-section">
              <h3>Encounter</h3>
              <div className="encounter-decks">
                <div className="drop-zone">
                  <div className="zone-header">
                    <span>Deck</span>
                    <span className="card-count">({gameState.encounter_zone.deck.length})</span>
                  </div>
                  <div className="zone-content">
                    {gameState.encounter_zone.deck.length > 0 ? (
                      <div className="card-back">🂠</div>
                    ) : (
                      <div className="empty-zone">Empty</div>
                    )}
                  </div>
                </div>

                <div className="drop-zone">
                  <div className="zone-header">
                    <span>Discard</span>
                    <span className="card-count">({gameState.encounter_zone.discard_pile.length})</span>
                  </div>
                  <div className="zone-content">
                    {gameState.encounter_zone.discard_pile.length > 0 ? (
                      <div className="card-preview">Discard</div>
                    ) : (
                      <div className="empty-zone">Empty</div>
                    )}
                  </div>
                </div>

                <div className="encounter-in-play">
                  <h4>In Play</h4>
                  <div className="cards-container">
                    {gameState.encounter_zone.in_play.map((card) => (
                      <div key={card.id} className="card-in-play">
                        {card.name}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Center - Main Play Area */}
          <div className="main-play-area">
            <div className="play-field">
              <h3>Play Field</h3>
              <div className="drop-zone">
                <div className="zone-header">
                  <span>Drop Cards Here</span>
                </div>
                <div className="zone-content">
                  {currentPlayer.zones.play_field.length === 0 ? (
                    <div className="empty-zone">Empty</div>
                  ) : (
                    <div className="cards-container">
                      {currentPlayer.zones.play_field.map((card) => (
                        <div key={card.id} className="card-in-play">
                          {card.name}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Resource and Threat */}
            <div className="resources-area">
              <div className="resource-zone">
                <h4>Resources</h4>
                <div className="drop-zone">
                  <div className="zone-header">
                    <span>Resources</span>
                    <span className="card-count">({currentPlayer.zones.resource_zone.length})</span>
                  </div>
                  <div className="zone-content">
                    {currentPlayer.zones.resource_zone.length === 0 ? (
                      <div className="empty-zone">Empty</div>
                    ) : (
                      <div className="cards-container">
                        {currentPlayer.zones.resource_zone.map((card) => (
                          <div key={card.id} className="card-in-play">
                            {card.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="threat-zone">
                <h4>Threat</h4>
                <div className="drop-zone">
                  <div className="zone-header">
                    <span>Threat</span>
                    <span className="card-count">({currentPlayer.zones.threat_zone.length})</span>
                  </div>
                  <div className="zone-content">
                    {currentPlayer.zones.threat_zone.length === 0 ? (
                      <div className="empty-zone">Empty</div>
                    ) : (
                      <div className="cards-container">
                        {currentPlayer.zones.threat_zone.map((card) => (
                          <div key={card.id} className="card-in-play">
                            {card.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom - Player Hand and Decks */}
        <div className="player-zone">
          <div className="player-decks">
            <div className="drop-zone">
              <div className="zone-header">
                <span>Deck</span>
              </div>
              <div className="zone-content">
                <div className="card-back">🂠</div>
              </div>
            </div>

            <div className="drop-zone">
              <div className="zone-header">
                <span>Discard</span>
                <span className="card-count">({currentPlayer.zones.discard_pile.length})</span>
              </div>
              <div className="zone-content">
                {currentPlayer.zones.discard_pile.length === 0 ? (
                  <div className="empty-zone">Empty</div>
                ) : (
                  <div className="card-preview">Discard</div>
                )}
              </div>
            </div>
          </div>

          {/* Hand */}
          <div className="hand-zone">
            <h3>Hand ({currentPlayer.zones.hand.length})</h3>
            <div className="drop-zone">
              <div className="hand-cards">
                {currentPlayer.zones.hand.map((card) => (
                  <div key={card.code} className="card-preview">
                    {card.name}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
    </div>
  );
};

export default GameBoard;