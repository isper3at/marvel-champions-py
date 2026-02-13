/**
 * GameCreation Component - Enhanced lobby for setting up a game
 * Features:
 * - Save/load encounter deck configurations
 * - Click-to-select player decks with scrollable list
 * - Orphaned game cleanup (handled by backend)
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

interface SavedEncounterDeck {
  modules: string[];
  names: string[];
  created_at: string;
  updated_at: string;
}

interface LobbyState {
  id: string;
  name: string;
  host: string;
  players: Player[];
  encounter_deck_id?: string;
  modules: string[];
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
  const [availableDecks, setAvailableDecks] = useState<Deck[]>([]);
  const [selectedDeckId, setSelectedDeckId] = useState<string | null>(null);
  const [moduleName, setModuleName] = useState<string>('');
  const [modules, setModules] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);
  
  // Save/Load encounter deck state
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [saveName, setSaveName] = useState<string>('');
  const [savedDecks, setSavedDecks] = useState<SavedEncounterDeck[]>([]);

  // Load initial data
  useEffect(() => {
    loadLobby();
    loadAvailableDecks();
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

  const loadAvailableDecks = async () => {
    try {
      const response = await deckAPI.listDecks();
      setAvailableDecks(response.decks || []);
    } catch (err) {
      console.error('Failed to load available decks:', err);
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
      const deck = await deckAPI.getDeck(deckCode.trim());
      // Add to available decks and select it
      setAvailableDecks(prev => {
        const exists = prev.some(d => d.id === deck.id);
        return exists ? prev : [...prev, deck];
      });
      setSelectedDeckId(deck.id);
      setDeckCode('');
    } catch (err) {
      console.error('Failed to load deck:', err);
      setError('Failed to load deck from MarvelCDB');
    } finally {
      setLoading(false);
    }
  };

  const handleDeckClick = async (deckId: string) => {
    setSelectedDeckId(deckId);
    setLoading(true);
    setError('');
    
    try {
      await lobbyAPI.chooseDeck(lobbyId, playerName, deckId);
      // Lobby will be updated via polling
    } catch (err) {
      console.error('Failed to choose deck:', err);
      setError('Failed to choose deck');
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
      // Build the encounter deck
      console.log('Building encounter with modules:', modules);
      setError('');
    } catch (err) {
      setError('Failed to build encounter deck');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEncounterDeck = async () => {
    if (modules.length === 0) {
      setError('No modules to save');
      return;
    }

    if (!saveName.trim()) {
      setError('Please enter a name for this encounter deck');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await lobbyAPI.saveEncounterDeck(modules, saveName.trim());
      setShowSaveModal(false);
      setSaveName('');
      setError('');
    } catch (err) {
      console.error('Failed to save encounter deck:', err);
      setError('Failed to save encounter deck');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSavedDecks = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await lobbyAPI.listSavedEncounterDecks();
      setSavedDecks(response.saved_decks || []);
      setShowLoadModal(true);
    } catch (err) {
      console.error('Failed to load saved decks:', err);
      setError('Failed to load saved encounter decks');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadEncounterDeck = async (name: string) => {
    setLoading(true);
    setError('');

    try {
      const response = await lobbyAPI.loadSavedEncounterDeck(name);
      if (response.modules) {
        setModules(response.modules);
        setShowLoadModal(false);
      }
    } catch (err) {
      console.error('Failed to load encounter deck:', err);
      setError('Failed to load encounter deck');
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
      onStartGame(response.game.id);
    } catch (err) {
      console.error('Failed to start game:', err);
      setError('Failed to start game');
    } finally {
      setLoading(false);
    }
  };

  const handleLeave = async () => {
    try {
      await lobbyAPI.leaveLobby(lobbyId, playerName);
      onLeave();
    } catch (err) {
      console.error('Failed to leave lobby:', err);
    }
  };

  if (!lobby) {
    return <div className="game-creation loading">Loading lobby...</div>;
  }

  const currentPlayer = lobby.players.find((p) => p.name === playerName);
  const hasSelectedDeck = !!currentPlayer?.deck;
  const isReady = currentPlayer?.is_ready || false;

  return (
    <div className="game-creation">
      <div className="lobby-container">
        <div className="lobby-header">
          <h1>{lobby.name}</h1>
          <button className="btn-leave" onClick={handleLeave}>
            Leave Lobby
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="lobby-layout">
          {/* Left Panel - Players */}
          <aside className="players-panel">
            <div className="panel-header">
              <h2>Players ({lobby.players.length})</h2>
            </div>

            <div className="players-list">
              {lobby.players.map((player) => (
                <div
                  key={player.name}
                  className={`player-card ${
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

                  <div className="encounter-actions">
                    <button
                      className="btn-build-encounter"
                      onClick={handleBuildEncounter}
                      disabled={loading || modules.length === 0}
                    >
                      {loading ? 'Building...' : 'Build Encounter Deck'}
                    </button>
                    
                    <button
                      className="btn-secondary"
                      onClick={() => setShowSaveModal(true)}
                      disabled={loading || modules.length === 0}
                    >
                      Save Deck
                    </button>
                    
                    <button
                      className="btn-secondary"
                      onClick={handleLoadSavedDecks}
                      disabled={loading}
                    >
                      Load Saved Deck
                    </button>
                  </div>
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
                      onKeyPress={(e) => e.key === 'Enter' && loadDeckFromMarvelCDB()}
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

                {availableDecks.length > 0 && (
                  <div className="available-decks">
                    <h4>Available Decks (click to select)</h4>
                    <div className="decks-list-scrollable">
                      {availableDecks.map((deck) => {
                        const isSelected = selectedDeckId === deck.id;
                        const isCurrentPlayerDeck = currentPlayer?.deck?.id === deck.id;
                        
                        return (
                          <div
                            key={deck.id}
                            className={`deck-list-item ${isSelected ? 'selected' : ''} ${
                              isCurrentPlayerDeck ? 'current-deck' : ''
                            }`}
                            onClick={() => handleDeckClick(deck.id)}
                          >
                            <div className="deck-list-header">
                              <span className="deck-list-name">{deck.name}</span>
                              {isCurrentPlayerDeck && <span className="current-badge">✓ Selected</span>}
                            </div>
                            <div className="deck-list-meta">
                              <span className="deck-list-cards">{deck.card_count || deck.cards.length} cards</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
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

      {/* Save Encounter Deck Modal */}
      {showSaveModal && (
        <div className="modal-overlay" onClick={() => setShowSaveModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Save Encounter Deck</h3>
            <p>Modules: {modules.join(', ')}</p>
            <input
              type="text"
              placeholder="Enter a name for this deck"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSaveEncounterDeck()}
            />
            <div className="modal-actions">
              <button className="btn-primary" onClick={handleSaveEncounterDeck} disabled={loading || !saveName.trim()}>
                Save
              </button>
              <button className="btn-secondary" onClick={() => setShowSaveModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Encounter Deck Modal */}
      {showLoadModal && (
        <div className="modal-overlay" onClick={() => setShowLoadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Load Saved Encounter Deck</h3>
            <div className="saved-decks-list">
              {savedDecks.length === 0 ? (
                <p>No saved encounter decks found</p>
              ) : (
                savedDecks.map((deck, index) => (
                  <div
                    key={index}
                    className="saved-deck-item"
                    onClick={() => handleLoadEncounterDeck(deck.names[0])}
                  >
                    <div className="saved-deck-names">
                      {deck.names.map((name, i) => (
                        <span key={i} className="saved-deck-name-badge">
                          {name}
                        </span>
                      ))}
                    </div>
                    <div className="saved-deck-modules">
                      Modules: {deck.modules.join(', ')}
                    </div>
                    <div className="saved-deck-date">
                      Saved: {new Date(deck.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowLoadModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameCreation;