/**
 * GameLobby component - Choose or create games
 */

import React, { useState, useEffect } from 'react';
import { GameState } from '../types';
import { gameAPI } from '../utils/api';
import '../styles/GameLobby.css';

interface GameLobbyProps {
  onStartGame: (gameId: string, playerName: string) => void;
}

export const GameLobby: React.FC<GameLobbyProps> = ({ onStartGame }) => {
  const [games, setGames] = useState<GameState[]>([]);
  const [selectedPlayerName, setSelectedPlayerName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGames();
    // Poll for games every 5 seconds
    const interval = setInterval(loadGames, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadGames = async () => {
    try {
      const list = await gameAPI.listGames();
      setGames(list);
      setError(null);
    } catch (err) {
      console.error('Failed to load games:', err);
      setError('Could not connect to backend. Make sure Flask server is running on localhost:5000');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGame = (game: GameState) => {
    if (!selectedPlayerName.trim()) {
      alert('Please enter a player name');
      return;
    }
    onStartGame(game.id, selectedPlayerName);
  };

  const handleCreateGame = async () => {
    if (!selectedPlayerName.trim()) {
      alert('Please enter a player name');
      return;
    }
    try {
      // Create a new game with the player as a participant
      const newGame = await gameAPI.createGame('Game by ' + selectedPlayerName, [], [selectedPlayerName]);
      setGames([...games, newGame]);
      onStartGame(newGame.id, selectedPlayerName);
    } catch (err) {
      console.error('Failed to create game:', err);
      alert('Failed to create game. Make sure backend is running.');
    }
  };

  return (
    <div className="game-lobby">
      <div className="lobby-container">
        <h1 className="lobby-title">Marvel Champions</h1>
        <p className="lobby-subtitle">Card Game</p>

        <div className="player-input-section">
          <label htmlFor="playerName">Your Name:</label>
          <input
            id="playerName"
            type="text"
            value={selectedPlayerName}
            onChange={(e) => setSelectedPlayerName(e.target.value)}
            placeholder="Enter your player name"
            maxLength={30}
          />
        </div>

        <div className="games-section">
          <h2>Available Games</h2>
          {error && <p className="error-message">{error}</p>}
          {loading ? (
            <p className="loading">Loading games...</p>
          ) : games.length === 0 ? (
            <p className="no-games">No games available. Create one to start playing!</p>
          ) : (
            <div className="games-list">
              {games.map((game) => (
                <div key={game.id} className="game-item">
                  <div className="game-info">
                    <h3 className="game-name">{game.name}</h3>
                    <p className="game-status">
                      Status: <span className={`status-${game.status}`}>{game.status}</span>
                    </p>
                    <p className="game-players">
                      Players: {game.players.length}
                    </p>
                  </div>
                  <button
                    className="join-button"
                    onClick={() => handleJoinGame(game)}
                    disabled={!selectedPlayerName.trim()}
                  >
                    Join Game
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="create-game-section">
          <button
            className="create-button"
            onClick={handleCreateGame}
            disabled={!selectedPlayerName.trim()}
          >
            ➕ Create New Game
          </button>
        </div>
      </div>
    </div>
  );
};
