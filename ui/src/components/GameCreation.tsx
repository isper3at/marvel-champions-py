/**
 * GameCreation Component - Lobby for setting up a game
 * Allows host to manage encounter modules and players to select decks
 */

import React, { useState, useEffect } from 'react';
import { lobbyAPI, deckAPI } from '../utils/lobbyAPI';
import '../styles/GameCreation.css';

interface GameCreationProps {
  lobbyId: string;
  playerName: string;
  isHost: boolean;
  onStartGame: (gameId: string) => void;
  onLeave: () => void;
}

interface Player {
  name: string;
  is_host: boolean;
  is_ready: boolean;
  deck?: {
    id: string;
    name: string;
  };
}

interface Deck {
  id: string;
  name: string;
  card_count?: number;
  cards: Array<{
    code: string;
    name: string;
    quantity: number;
  }>;
  source_url?: string;
}

interface Module {
  id: string;
  name: string;
}

interface LobbyState {
  id: string;
  name: string;
  host: string;
  players: Player[];
  encounter_deck_id?: string;
  modules: Module[];
  all_ready: boolean;
  can_start: boolean;
}

export const GameCreation: React.FC<GameCreationProps> = ({
  lobbyId,
  playerName,
  isHost,
  onStartGame,
  onLeave,
}) => {
  const [lobby, setLobby] = useState<LobbyState | null>(null);
  const [deckCode, setDeckCode] = useState<string>('');
  const [loadedDeck, setLoadedDeck] = useState<Deck | null>(null);
  const [moduleName, setModuleName] = useState<string>('');
  const [modules, setModules] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  // Load initial data
  useEffect(() => {
    loadLobby();
  }, [lobbyId]);

  // Poll for lobby updates
  useEffect(() => {
    if (pollInterval === null) {
      const interval = setInterval(loadLobby, 2000);
      setPollInterval(interval);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [lobbyId]);

  const loadLobby = async () => {
    try {
      const data = await lobbyAPI.getLobby(lobbyId);
      setLobby(data);
      setError('');
    } catch (err) {
      console.error('Failed to load lobby:', err);
      setError('Failed to load lobby state');
    }
  };

  const loadDeckFromMarvelCDB = async () => {
    if (!deckCode.trim()) {
      setError('Please enter a deck code');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const deck = await deckAPI.getMarvelCDBDeck(deckCode.trim());
      setLoadedDeck(deck);
    } catch (err) {
      console.error('Failed to load deck:', err);
      setError('Failed to load deck from MarvelCDB');
    } finally {
      setLoading(false);
    }
  };

  const handleAddModule = () => {
    if (!moduleName.trim()) {
      setError('Please enter a module name');
      return;
    }

    if (modules.includes(moduleName.trim())) {
      setError('Module already added');
      return;
    }

    setModules([...modules, moduleName.trim()]);
    setModuleName('');
    setError('');
  };

  const handleRemoveModule = (index: number) => {
    setModules(modules.filter((_, i) => i !== index));
  };

  const handleBuildEncounter = async () => {
    if (modules.length === 0) {
      setError('Please add at least one module');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // This would call a backend endpoint to build the encounter deck
      // For now, we'll just set it as configured
      console.log('Building encounter with modules:', modules);
      setError('');
    } catch (err) {
      setError('Failed to build encounter deck');
    } finally {
      setLoading(false);
    }
  };

  const handleChooseDeck = async () => {
    if (!loadedDeck) return;

    setLoading(true);
    setError('');
    try {
      await lobbyAPI.chooseDeck(lobbyId, playerName, loadedDeck.id);
      setLoadedDeck(null);
      setDeckCode('');
      // Lobby will be updated via polling
    } catch (err) {
      console.error('Failed to choose deck:', err);
      setError('Failed to choose deck');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleReady = async () => {
    setLoading(true);
    setError('');

    try {
      await lobbyAPI.toggleReady(lobbyId, playerName);
      await loadLobby();
    } catch (err) {
      console.error('Failed to toggle ready:', err);
      setError('Failed to update ready status');
    } finally {
      setLoading(false);
    }
  };

  const handleStartGame = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await lobbyAPI.startGame(lobbyId, playerName);
      onStartGame(response.game_id);
    } catch (err) {
      console.error('Failed to start game:', err);
      setError('Failed to start game');
    } finally {
      setLoading(false);
    }
  };

  const currentPlayer = lobby?.players.find((p) => p.name === playerName);
  const isReady = currentPlayer?.is_ready || false;
  const hasSelectedDeck = currentPlayer?.deck !== undefined;

  if (!lobby) {
    return (
      <div className="game-creation loading">
        <div className="loading-spinner">Loading lobby...</div>
      </div>
    );
  }

  return (
    <div className="game-creation">
      <div className="creation-container">
        {/* Header */}
        <header className="creation-header">
          <div className="header-content">
            <div className="game-info">
              <h1 className="game-title">{lobby.name}</h1>
              <div className="game-meta">
                <span className="host-badge">Host: {lobby.host}</span>
                <span className="player-count">{lobby.players.length} Players</span>
              </div>
            </div>
            <button className="btn-leave" onClick={onLeave}>
              Leave Game
            </button>
          </div>
        </header>

        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠</span>
            {error}
            <button className="error-dismiss" onClick={() => setError('')}>
              ✕
            </button>
          </div>
        )}

        <div className="creation-grid">
          {/* Left Panel - Players */}
          <aside className="players-panel">
            <div className="panel-header">
              <h2>Players</h2>
              <div className="ready-indicator">
                {lobby.all_ready ? (
                  <span className="status-ready">✓ All Ready</span>
                ) : (
                  <span className="status-waiting">Waiting...</span>
                )}
              </div>
            </div>

            <div className="players-list">
              {lobby.players.map((player) => (
                <div
                  key={player.name}
                  className={`player-card ${player.is_ready ? 'ready' : ''} ${
                    player.name === playerName ? 'current' : ''
                  }`}
                >
                  <div className="player-header">
                    <div className="player-name">
                      {player.name}
                      {player.is_host && <span className="host-star">★</span>}
                    </div>
                    <div className={`ready-badge ${player.is_ready ? 'ready' : ''}`}>
                      {player.is_ready ? '✓ Ready' : 'Not Ready'}
                    </div>
                  </div>

                  {player.deck ? (
                    <div className="player-deck">
                      <div className="deck-info">
                        <span className="deck-icon">🃏</span>
                        <span className="deck-name">{player.deck.name}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="no-deck">No deck selected</div>
                  )}
                </div>
              ))}
            </div>
          </aside>

          {/* Center Panel - Setup */}
          <main className="setup-panel">
            {/* Encounter Setup (Host Only) */}
            {isHost && (
              <section className="setup-section encounter-section">
                <div className="section-header">
                  <h2>Encounter Setup</h2>
                  <span className="section-subtitle">Configure villain and modules</span>
                </div>

                <div className="module-builder">
                  <div className="input-group">
                    <input
                      type="text"
                      className="module-input"
                      placeholder="Enter module name (e.g., 'Kree Fanatic')"
                      value={moduleName}
                      onChange={(e) => setModuleName(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddModule()}
                    />
                    <button className="btn-add" onClick={handleAddModule} disabled={loading}>
                      Add Module
                    </button>
                  </div>

                  {modules.length > 0 && (
                    <div className="modules-list">
                      {modules.map((module, index) => (
                        <div key={index} className="module-chip">
                          <span className="module-name">{module}</span>
                          <button
                            className="module-remove"
                            onClick={() => handleRemoveModule(index)}
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <button
                    className="btn-build-encounter"
                    onClick={handleBuildEncounter}
                    disabled={loading || modules.length === 0}
                  >
                    {loading ? 'Building...' : 'Build Encounter Deck'}
                  </button>
                </div>
              </section>
            )}

            {/* Deck Selection */}
            <section className="setup-section deck-section">
              <div className="section-header">
                <h2>Choose Your Deck</h2>
                <span className="section-subtitle">Select a hero deck to play</span>
              </div>

              <div className="deck-selector">
                <div className="deck-input-group">
                  <label htmlFor="deck-code">Enter MarvelCDB Deck Code</label>
                  <div className="deck-input-row">
                    <input
                      id="deck-code"
                      type="text"
                      value={deckCode}
                      onChange={(e) => setDeckCode(e.target.value)}
                      placeholder="e.g., 12345"
                      disabled={loading}
                    />
                    <button
                      className="btn-secondary"
                      onClick={loadDeckFromMarvelCDB}
                      disabled={loading || !deckCode.trim()}
                    >
                      {loading ? 'Loading...' : 'Load Deck'}
                    </button>
                  </div>
                </div>

                {loadedDeck && (
                  <div className="loaded-deck">
                    <div className="loaded-deck-header">
                      <h3>{loadedDeck.name}</h3>
                      <span>{loadedDeck.card_count} cards</span>
                    </div>
                    <div className="loaded-deck-cards">
                      {loadedDeck.cards.slice(0, 10).map((card, index) => (
                        <div key={index} className="deck-card-item">
                          {card.quantity}x {card.name}
                        </div>
                      ))}
                      {loadedDeck.cards.length > 10 && (
                        <div className="deck-card-item more">
                          ... and {loadedDeck.cards.length - 10} more cards
                        </div>
                      )}
                    </div>
                    <div className="loaded-deck-actions">
                      <button
                        className="btn-primary"
                        onClick={handleChooseDeck}
                        disabled={loading}
                      >
                        Choose This Deck
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => setLoadedDeck(null)}
                        disabled={loading}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {hasSelectedDeck && (
                  <div className="selected-deck-info">
                    <p>✓ Deck selected: {currentPlayer.deck?.name}</p>
                  </div>
                )}
              </div>
            </section>

            {/* Ready Button */}
            <div className="action-bar">
              <button
                className={`btn-ready ${isReady ? 'ready' : ''}`}
                onClick={handleToggleReady}
                disabled={loading || !hasSelectedDeck}
              >
                {isReady ? '✓ Ready' : 'Mark as Ready'}
              </button>
            </div>
          </main>

          {/* Right Panel - Game Info */}
          <aside className="info-panel">
            <div className="panel-header">
              <h2>Game Status</h2>
            </div>

            <div className="status-items">
              <div className="status-item">
                <span className="status-label">Players Ready</span>
                <span className="status-value">
                  {lobby.players.filter((p) => p.is_ready).length} / {lobby.players.length}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">Encounter Configured</span>
                <span className="status-value">
                  {modules.length > 0 ? `${modules.length} modules` : 'Not set'}
                </span>
              </div>

              {isHost && (
                <div className="host-actions">
                  <button
                    className="btn-start-game"
                    onClick={handleStartGame}
                    disabled={loading || !lobby.can_start}
                  >
                    {loading ? 'Starting...' : 'Start Game'}
                  </button>

                  {!lobby.can_start && (
                    <div className="start-requirements">
                      <p className="requirements-title">Requirements:</p>
                      <ul className="requirements-list">
                        <li className={lobby.all_ready ? 'met' : ''}>
                          All players ready
                        </li>
                        <li className={modules.length > 0 ? 'met' : ''}>
                          Encounter configured
                        </li>
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>

    </div>
  );
};

export default GameCreation;