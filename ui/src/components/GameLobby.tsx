/**
 * GameLobby component - Lobby system for creating and joining games
 * 
 * Flow:
 * 1. Show list of available lobbies or create new lobby form
 * 2. Enter lobby - show players, deck selection, ready status
 * 3. Host sets encounter deck and starts game when all ready
 */

import React, { useState, useEffect } from 'react';
import { lobbyAPI, gameAPI } from '../utils/api';
import '../styles/GameLobby.css';

interface Lobby {
  id: string;
  name: string;
  host: string;
  player_count: number;
  players: string[];
  has_encounter: boolean;
  all_ready: boolean;
}

interface LobbyPlayer {
  username: string;
  deck_id: string | null;
  is_ready: boolean;
  is_host: boolean;
}

interface LobbyDetails {
  id: string;
  name: string;
  status: string;
  host: string;
  players: LobbyPlayer[];
  encounter_deck_id: string | null;
  all_ready: boolean;
  can_start: boolean;
}

interface Deck {
  id: string;
  name: string;
  total_cards: number;
}

interface GameLobbyProps {
  onStartGame: (gameId: string, playerName: string) => void;
}

type ViewState = 'list' | 'create' | 'lobby';

export const GameLobby: React.FC<GameLobbyProps> = ({ onStartGame }) => {
  const [viewState, setViewState] = useState<ViewState>('list');
  const [username, setUsername] = useState<string>('');
  const [lobbies, setLobbies] = useState<Lobby[]>([]);
  const [currentLobby, setCurrentLobby] = useState<LobbyDetails | null>(null);
  const [availableDecks, setAvailableDecks] = useState<Deck[]>([]);
  const [encounterDecks, setEncounterDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form states
  const [newLobbyName, setNewLobbyName] = useState('');

  // Load lobbies list
  useEffect(() => {
    if (viewState === 'list') {
      loadLobbies();
      const interval = setInterval(loadLobbies, 3000); // Poll every 3s
      return () => clearInterval(interval);
    }
  }, [viewState]);

  // Load lobby details when in lobby
  useEffect(() => {
    if (viewState === 'lobby' && currentLobby) {
      loadLobbyDetails();
      const interval = setInterval(loadLobbyDetails, 2000); // Poll every 2s
      return () => clearInterval(interval);
    }
  }, [viewState, currentLobby?.id]);

  // Load decks once
  useEffect(() => {
    loadDecks();
  }, []);

  const loadLobbies = async () => {
    try {
      const data = await lobbyAPI.listLobbies();
      setLobbies(data.lobbies);
    } catch (err) {
      console.error('Failed to load lobbies:', err);
    }
  };

  const loadLobbyDetails = async () => {
    if (!currentLobby) return;
    
    try {
      const details = await lobbyAPI.getLobby(currentLobby.id);
      setCurrentLobby(details);
      
      // Check if game started
      if (details.status === 'in_progress') {
        onStartGame(details.id, username);
      }
    } catch (err) {
      console.error('Failed to load lobby details:', err);
      setError('Lobby not found or deleted');
      setViewState('list');
    }
  };

  const loadDecks = async () => {
    try {
      const data = await deckAPI.listDecks();
      // Separate player and encounter decks (you may need to add deck type to API)
      // For now, assume all decks can be used as player decks
      // and encounter decks have "Encounter" in the name (simple heuristic)
      const playerDecks = data.decks.filter((d: Deck) => !d.name.toLowerCase().includes('encounter'));
      const encounterDecks = data.decks.filter((d: Deck) => d.name.toLowerCase().includes('encounter'));
      
      setAvailableDecks(playerDecks);
      setEncounterDecks(encounterDecks);
    } catch (err) {
      console.error('Failed to load decks:', err);
    }
  };

  const handleCreateLobby = async () => {
    if (!newLobbyName.trim() || !username.trim()) {
      setError('Please enter both lobby name and username');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await lobbyAPI.createLobby(newLobbyName, username);
      setCurrentLobby(response.lobby);
      setViewState('lobby');
      setNewLobbyName('');
    } catch (err: any) {
      setError(err.message || 'Failed to create lobby');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinLobby = async (lobbyId: string) => {
    if (!username.trim()) {
      setError('Please enter your username');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await lobbyAPI.joinLobby(lobbyId, username);
      const details = await lobbyAPI.getLobby(lobbyId);
      setCurrentLobby(details);
      setViewState('lobby');
    } catch (err: any) {
      setError(err.message || 'Failed to join lobby');
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveLobby = async () => {
    if (!currentLobby) return;

    try {
      await lobbyAPI.leaveLobby(currentLobby.id, username);
      setCurrentLobby(null);
      setViewState('list');
    } catch (err: any) {
      setError(err.message || 'Failed to leave lobby');
    }
  };

  const handleChooseDeck = async (deckId: string) => {
    if (!currentLobby) return;

    try {
      await lobbyAPI.chooseDeck(currentLobby.id, username, deckId);
      await loadLobbyDetails();
    } catch (err: any) {
      setError(err.message || 'Failed to choose deck');
    }
  };

  const handleSetEncounterDeck = async (deckId: string) => {
    if (!currentLobby) return;

    try {
      await lobbyAPI.setEncounterDeck(currentLobby.id, username, deckId);
      await loadLobbyDetails();
    } catch (err: any) {
      setError(err.message || 'Failed to set encounter deck');
    }
  };

  const handleToggleReady = async () => {
    if (!currentLobby) return;

    try {
      await lobbyAPI.toggleReady(currentLobby.id, username);
      await loadLobbyDetails();
    } catch (err: any) {
      setError(err.message || 'Failed to toggle ready');
    }
  };

  const handleStartGame = async () => {
    if (!currentLobby) return;

    try {
      const response = await lobbyAPI.startGame(currentLobby.id, username);
      onStartGame(response.game_id, username);
    } catch (err: any) {
      setError(err.message || 'Failed to start game');
    }
  };

  // ========================================================================
  // RENDER: Lobby List View
  // ========================================================================
  
  if (viewState === 'list') {
    return (
      <div className="game-lobby">
        <div className="lobby-header">
          <h1>Marvel Champions - Lobbies</h1>
          <div className="username-input">
            <input
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input"
            />
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="lobby-actions">
          <button
            onClick={() => setViewState('create')}
            disabled={!username.trim()}
            className="btn btn-primary"
          >
            Create New Lobby
          </button>
        </div>

        <div className="lobbies-list">
          <h2>Available Lobbies</h2>
          {lobbies.length === 0 ? (
            <p className="empty-state">No lobbies available. Create one to get started!</p>
          ) : (
            <div className="lobby-cards">
              {lobbies.map((lobby) => (
                <div key={lobby.id} className="lobby-card">
                  <div className="lobby-card-header">
                    <h3>{lobby.name}</h3>
                    <span className="player-count">{lobby.player_count} player(s)</span>
                  </div>
                  <div className="lobby-card-body">
                    <div className="lobby-info">
                      <span className="label">Host:</span>
                      <span>{lobby.host}</span>
                    </div>
                    <div className="lobby-info">
                      <span className="label">Players:</span>
                      <span>{lobby.players.join(', ')}</span>
                    </div>
                    <div className="lobby-status">
                      {lobby.has_encounter && <span className="badge badge-success">Encounter Set</span>}
                      {lobby.all_ready && <span className="badge badge-info">All Ready</span>}
                    </div>
                  </div>
                  <div className="lobby-card-actions">
                    <button
                      onClick={() => handleJoinLobby(lobby.id)}
                      disabled={!username.trim() || loading}
                      className="btn btn-secondary"
                    >
                      Join Lobby
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ========================================================================
  // RENDER: Create Lobby View
  // ========================================================================
  
  if (viewState === 'create') {
    return (
      <div className="game-lobby">
        <div className="lobby-header">
          <h1>Create New Lobby</h1>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="create-form">
          <div className="form-group">
            <label>Lobby Name</label>
            <input
              type="text"
              placeholder="Enter lobby name"
              value={newLobbyName}
              onChange={(e) => setNewLobbyName(e.target.value)}
              className="input"
            />
          </div>

          <div className="form-group">
            <label>Your Username</label>
            <input
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input"
            />
          </div>

          <div className="form-actions">
            <button
              onClick={() => setViewState('list')}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateLobby}
              disabled={loading || !newLobbyName.trim() || !username.trim()}
              className="btn btn-primary"
            >
              {loading ? 'Creating...' : 'Create Lobby'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ========================================================================
  // RENDER: Lobby Details View
  // ========================================================================
  
  if (viewState === 'lobby' && currentLobby) {
    const currentPlayer = currentLobby.players.find((p) => p.username === username);
    const isHost = currentPlayer?.is_host || false;

    return (
      <div className="game-lobby">
        <div className="lobby-header">
          <h1>{currentLobby.name}</h1>
          <button onClick={handleLeaveLobby} className="btn btn-danger">
            Leave Lobby
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="lobby-content">
          {/* Players Section */}
          <div className="lobby-section">
            <h2>Players</h2>
            <div className="players-list">
              {currentLobby.players.map((player) => (
                <div key={player.username} className="player-item">
                  <div className="player-info">
                    <span className="player-name">
                      {player.username}
                      {player.is_host && <span className="badge badge-primary">Host</span>}
                    </span>
                    {player.deck_id && (
                      <span className="deck-selected">
                        Deck: {availableDecks.find((d) => d.id === player.deck_id)?.name || 'Unknown'}
                      </span>
                    )}
                  </div>
                  <div className="player-status">
                    {player.is_ready ? (
                      <span className="badge badge-success">Ready</span>
                    ) : (
                      <span className="badge badge-warning">Not Ready</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Deck Selection Section */}
          <div className="lobby-section">
            <h2>Your Deck</h2>
            {currentPlayer?.deck_id ? (
              <div className="selected-deck">
                <p>
                  Selected: {availableDecks.find((d) => d.id === currentPlayer.deck_id)?.name}
                </p>
                <select
                  onChange={(e) => handleChooseDeck(e.target.value)}
                  value={currentPlayer.deck_id}
                  className="select"
                >
                  {availableDecks.map((deck) => (
                    <option key={deck.id} value={deck.id}>
                      {deck.name} ({deck.total_cards} cards)
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="deck-selection">
                <select
                  onChange={(e) => handleChooseDeck(e.target.value)}
                  defaultValue=""
                  className="select"
                >
                  <option value="" disabled>
                    Choose your deck...
                  </option>
                  {availableDecks.map((deck) => (
                    <option key={deck.id} value={deck.id}>
                      {deck.name} ({deck.total_cards} cards)
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Encounter Deck Section (Host Only) */}
          {isHost && (
            <div className="lobby-section">
              <h2>Encounter Deck</h2>
              {currentLobby.encounter_deck_id ? (
                <div className="selected-encounter">
                  <p>
                    Selected: {encounterDecks.find((d) => d.id === currentLobby.encounter_deck_id)?.name}
                  </p>
                  <select
                    onChange={(e) => handleSetEncounterDeck(e.target.value)}
                    value={currentLobby.encounter_deck_id}
                    className="select"
                  >
                    {encounterDecks.map((deck) => (
                      <option key={deck.id} value={deck.id}>
                        {deck.name}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="encounter-selection">
                  <select
                    onChange={(e) => handleSetEncounterDeck(e.target.value)}
                    defaultValue=""
                    className="select"
                  >
                    <option value="" disabled>
                      Choose encounter deck...
                    </option>
                    {encounterDecks.map((deck) => (
                      <option key={deck.id} value={deck.id}>
                        {deck.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          )}

          {/* Actions Section */}
          <div className="lobby-actions-bottom">
            {currentPlayer && (
              <button
                onClick={handleToggleReady}
                disabled={!currentPlayer.deck_id}
                className={`btn ${currentPlayer.is_ready ? 'btn-warning' : 'btn-success'}`}
              >
                {currentPlayer.is_ready ? 'Not Ready' : 'Ready Up'}
              </button>
            )}

            {isHost && (
              <button
                onClick={handleStartGame}
                disabled={!currentLobby.can_start}
                className="btn btn-primary"
                title={
                  !currentLobby.can_start
                    ? 'All players must be ready and encounter deck must be set'
                    : 'Start the game'
                }
              >
                Start Game
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
};
