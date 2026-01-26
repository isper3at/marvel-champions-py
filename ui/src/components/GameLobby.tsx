/**
 * Game Lobby component - Waiting room with player management
 */

import React, { useState, useEffect } from 'react';
import { lobbyAPI, deckAPI } from '../utils/lobbyAPI';
import { Deck } from '../types';
import '../styles/GameLobby.css';

interface GameLobbyProps {
  mode: 'host' | 'join';
  playerName: string;
  onStartGame: (gameId: string, playerName: string) => void;
  onBack: () => void;
}

interface LobbyPlayer {
  name: string;
  is_host: boolean;
  is_ready: boolean;
  deck?: Deck;
}

interface LobbyGame {
  id: string;
  name: string;
  host: string;
  players: LobbyPlayer[];
  status: string;
}

export const GameLobby: React.FC<GameLobbyProps> = ({
  mode,
  playerName,
  onStartGame,
  onBack,
}) => {
  const [lobbies, setLobbies] = useState<LobbyGame[]>([]);
  const [currentLobby, setCurrentLobby] = useState<LobbyGame | null>(null);
  const [availableDecks, setAvailableDecks] = useState<Deck[]>([]);
  const [selectedDeck, setSelectedDeck] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [gameName, setGameName] = useState('');
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  // Load available decks
  useEffect(() => {
    const loadDecks = async () => {
      try {
        const decks = await deckAPI.listDecks();
        setAvailableDecks(Array.isArray(decks) ? decks : []);
      } catch (err) {
        console.error('Failed to load decks:', err);
        setError('Failed to load decks');
      }
    };
    loadDecks();
  }, []);

  // Load lobbies if in join mode
  useEffect(() => {
    if (mode === 'join' && !currentLobby) {
      loadLobbies();
    }
  }, [mode, currentLobby]);

  // Poll for lobby updates
  useEffect(() => {
    if (currentLobby && pollInterval === null) {
      const interval = setInterval(async () => {
        try {
          const updated = await lobbyAPI.getLobby(currentLobby.id);
          setCurrentLobby(updated);
        } catch (err) {
          console.error('Failed to update lobby:', err);
        }
      }, 2000);
      setPollInterval(interval);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      }
    };
  }, [currentLobby, pollInterval]);

  const loadLobbies = async () => {
    setLoading(true);
    try {
      const data = await lobbyAPI.listLobbies();
      setLobbies(Array.isArray(data) ? data : []);
      setError('');
    } catch (err) {
      console.error('Failed to load lobbies:', err);
      setError('Failed to load lobbies');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLobby = async () => {
    if (!gameName.trim()) {
      setError('Please enter a game name');
      return;
    }

    setLoading(true);
    try {
      const lobby = await lobbyAPI.createLobby(gameName, playerName);
      setCurrentLobby(lobby);
      setError('');
    } catch (err) {
      console.error('Failed to create lobby:', err);
      setError('Failed to create lobby');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinLobby = async (lobbyId: string) => {
    setLoading(true);
    try {
      const lobby = await lobbyAPI.joinLobby(lobbyId, playerName);
      setCurrentLobby(lobby);
      setError('');
    } catch (err) {
      console.error('Failed to join lobby:', err);
      setError('Failed to join lobby');
    } finally {
      setLoading(false);
    }
  };

  const handleChooseDeck = async (deckId: string) => {
    if (!currentLobby) return;

    setLoading(true);
    try {
      const updated = await lobbyAPI.chooseDeck(currentLobby.id, playerName, deckId);
      setCurrentLobby(updated);
      setSelectedDeck(deckId);
      setError('');
    } catch (err) {
      console.error('Failed to choose deck:', err);
      setError('Failed to choose deck');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleReady = async () => {
    if (!currentLobby) return;

    setLoading(true);
    try {
      const updated = await lobbyAPI.toggleReady(currentLobby.id, playerName);
      setCurrentLobby(updated);
      setError('');
    } catch (err) {
      console.error('Failed to toggle ready:', err);
      setError('Failed to toggle ready');
    } finally {
      setLoading(false);
    }
  };

  const handleStartGame = async () => {
    if (!currentLobby) return;

    setLoading(true);
    try {
      const game = await lobbyAPI.startGame(currentLobby.id, playerName);
      onStartGame(game.id, playerName);
    } catch (err) {
      console.error('Failed to start game:', err);
      setError('Failed to start game');
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveLobby = async () => {
    if (!currentLobby) return;

    setLoading(true);
    try {
      await lobbyAPI.leaveLobby(currentLobby.id, playerName);
      setCurrentLobby(null);
      setSelectedDeck('');
      setLobbies([]);
      setError('');
    } catch (err) {
      console.error('Failed to leave lobby:', err);
      setError('Failed to leave lobby');
    } finally {
      setLoading(false);
    }
  };

  const currentPlayer = currentLobby?.players.find((p) => p.name === playerName);
  const isHost = currentPlayer?.is_host || false;
  const isReady = currentPlayer?.is_ready || false;
  const allPlayersReady = currentLobby?.players.every((p) => p.is_ready) || false;

  return (
    <div className="game-lobby">
      {!currentLobby ? (
        mode === 'host' ? (
          // Host creation mode
          <div className="lobby-card">
            <h2>Create a New Game</h2>
            <div className="input-group">
              <label htmlFor="game-name">Game Name</label>
              <input
                id="game-name"
                type="text"
                placeholder="Enter game name"
                value={gameName}
                onChange={(e) => setGameName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleCreateLobby()}
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="button-group">
              <button className="btn btn-primary" onClick={handleCreateLobby} disabled={loading}>
                {loading ? 'Creating...' : 'Create Game'}
              </button>
              <button className="btn btn-back" onClick={onBack} disabled={loading}>
                Back
              </button>
            </div>
          </div>
        ) : (
          // Join mode - list lobbies
          <div className="lobby-card">
            <h2>Available Games</h2>
            {error && <div className="error-message">{error}</div>}
            {loading ? (
              <div className="loading">Loading lobbies...</div>
            ) : lobbies.length === 0 ? (
              <div className="empty-state">
                <p>No games available</p>
                <button className="btn btn-secondary" onClick={loadLobbies}>
                  Refresh
                </button>
              </div>
            ) : (
              <div className="lobbies-list">
                {lobbies.map((lobby) => (
                  <div key={lobby.id} className="lobby-item">
                    <div className="lobby-info">
                      <h3>{lobby.name}</h3>
                      <p>
                        Host: {lobby.host} • Players: {lobby.players.length}
                      </p>
                    </div>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleJoinLobby(lobby.id)}
                      disabled={loading}
                    >
                      Join
                    </button>
                  </div>
                ))}
              </div>
            )}
            <button className="btn btn-back" onClick={onBack} disabled={loading}>
              Back
            </button>
          </div>
        )
      ) : (
        // Lobby waiting room
        <div className="lobby-card">
          <div className="lobby-header">
            <h2>{currentLobby.name}</h2>
            <p>Host: {currentLobby.host}</p>
          </div>

          {error && <div className="error-message">{error}</div>}

          {/* Players List */}
          <div className="section">
            <h3>Players ({currentLobby.players.length})</h3>
            <div className="players-list">
              {currentLobby.players.map((player) => (
                <div key={player.name} className="player-item">
                  <div className="player-info">
                    <span className="player-name">
                      {player.name}
                      {player.is_host && <span className="badge">HOST</span>}
                    </span>
                    <span className={`status ${player.is_ready ? 'ready' : 'not-ready'}`}>
                      {player.is_ready ? '✓ Ready' : 'Not Ready'}
                    </span>
                  </div>
                  {player.deck && <p className="deck-name">{player.deck.name}</p>}
                </div>
              ))}
            </div>
          </div>

          {/* Current Player - Deck Selection */}
          {playerName === currentPlayer?.name && (
            <div className="section">
              <h3>Choose Your Deck</h3>
              <select
                value={selectedDeck}
                onChange={(e) => handleChooseDeck(e.target.value)}
                disabled={loading}
              >
                <option value="">Select a deck...</option>
                {availableDecks.map((deck) => (
                  <option key={deck.id} value={deck.id}>
                    {deck.name}
                  </option>
                ))}
              </select>

              <button
                className={`btn ${isReady ? 'btn-ready' : 'btn-primary'}`}
                onClick={handleToggleReady}
                disabled={loading || !selectedDeck}
              >
                {isReady ? '✓ Ready' : 'Mark as Ready'}
              </button>
            </div>
          )}

          {/* Host Controls */}
          {isHost && (
            <div className="section host-section">
              <h3>Game Controls</h3>
              <button
                className="btn btn-primary"
                onClick={handleStartGame}
                disabled={loading || !allPlayersReady}
              >
                Start Game
              </button>
              <p className="help-text">
                {!allPlayersReady ? 'Waiting for all players to ready up...' : 'All players ready!'}
              </p>
            </div>
          )}

          {/* Leave Button */}
          <button className="btn btn-secondary" onClick={handleLeaveLobby} disabled={loading}>
            Leave Game
          </button>
        </div>
      )}
    </div>
  );
};