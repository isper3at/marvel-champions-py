/**
 * Game Lobby component - Browse available lobbies
 * Simplified to just show lobby list for joining
 */

import React, { useState, useEffect } from 'react';
import { lobbyAPI } from '../utils/lobbyAPI';
import '../styles/GameLobby.css';

interface GameLobbyProps {
  playerName: string;
  onJoinLobby: (lobbyId: string) => void;
  onBack: () => void;
  error?: string;
}

interface LobbyListItem {
  id: string;
  name: string;
  host: string;
  player_count: number;
  players: string[];
  has_encounter: boolean;
  all_ready: boolean;
}

export const GameLobby: React.FC<GameLobbyProps> = ({
  playerName,
  onJoinLobby,
  onBack,
  error: externalError,
}) => {
  const [lobbies, setLobbies] = useState<LobbyListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadLobbies();
    // Auto-refresh every 3 seconds
    const interval = setInterval(() => {
      loadLobbies(true);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const loadLobbies = async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    
    setError('');

    try {
      const response = await lobbyAPI.listLobbies();
      setLobbies(response.lobbies || []);
    } catch (err) {
      console.error('Failed to load lobbies:', err);
      setError('Failed to load available games');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleJoin = (lobbyId: string) => {
    onJoinLobby(lobbyId);
  };

  const handleRefresh = () => {
    loadLobbies();
  };

  if (loading) {
    return (
      <div className="game-lobby">
        <div className="lobby-card">
          <div className="loading">Loading available games...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="game-lobby">
      <div className="lobby-card">
        <div className="lobby-header">
          <h2>Available Games</h2>
          <p>Welcome, {playerName}</p>
        </div>

        {(error || externalError) && (
          <div className="error-message">{error || externalError}</div>
        )}

        {lobbies.length === 0 ? (
          <div className="empty-state">
            <p>No games available right now</p>
            <p className="empty-hint">Be the first to host a game!</p>
            <button className="btn btn-secondary" onClick={handleRefresh} disabled={refreshing}>
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        ) : (
          <>
            <div className="lobbies-list">
              {lobbies.map((lobby) => (
                <div key={lobby.id} className="lobby-item">
                  <div className="lobby-info">
                    <h3>{lobby.name}</h3>
                    <div className="lobby-meta">
                      <span className="lobby-host">Host: {lobby.host}</span>
                      <span className="lobby-players">
                        {lobby.player_count} {lobby.player_count === 1 ? 'player' : 'players'}
                      </span>
                    </div>
                    {lobby.players.length > 0 && (
                      <div className="lobby-player-list">
                        {lobby.players.join(', ')}
                      </div>
                    )}
                  </div>
                  <div className="lobby-actions">
                    <button
                      className="btn btn-primary"
                      onClick={() => handleJoin(lobby.id)}
                    >
                      Join
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="lobby-footer">
              <button
                className="btn btn-secondary btn-refresh"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                {refreshing ? 'Refreshing...' : '🔄 Refresh'}
              </button>
            </div>
          </>
        )}

        <button className="btn btn-back" onClick={onBack}>
          ← Back to Start
        </button>
      </div>
    </div>
  );
};

export default GameLobby;