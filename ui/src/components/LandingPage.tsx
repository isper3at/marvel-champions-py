/**
 * Landing page - Player enters name and chooses to join or host
 */

import React, { useState } from 'react';
import '../styles/LandingPage.css';

interface LandingPageProps {
  onHost: (playerName: string) => void;
  onJoin: (playerName: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onHost, onJoin }) => {
  const [playerName, setPlayerName] = useState<string>('');
  const [mode, setMode] = useState<'select' | 'host' | 'join'>('select');

  const handleHostClick = () => {
    if (playerName.trim()) {
      setMode('host');
    }
  };

  const handleJoinClick = () => {
    if (playerName.trim()) {
      setMode('join');
    }
  };

  const handleConfirmHost = () => {
    onHost(playerName);
  };

  const handleConfirmJoin = () => {
    onJoin(playerName);
  };

  const handleBack = () => {
    setMode('select');
  };

  return (
    <div className="landing-page">
      <div className="landing-container">
        <h1>Marvel Champions</h1>
        
        {mode === 'select' ? (
          <div className="landing-content">
            <div className="name-input-group">
              <label htmlFor="player-name">Enter Your Name</label>
              <input
                id="player-name"
                type="text"
                placeholder="Hero Name"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && playerName.trim()) {
                    setMode('host');
                  }
                }}
                autoFocus
              />
            </div>

            <div className="button-group">
              <button
                className="btn btn-primary"
                onClick={handleHostClick}
                disabled={!playerName.trim()}
              >
                Host Game
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleJoinClick}
                disabled={!playerName.trim()}
              >
                Join Game
              </button>
            </div>
          </div>
        ) : (
          <div className="landing-content">
            <div className="mode-header">
              <h2>Welcome, {playerName}!</h2>
              <p>{mode === 'host' ? 'Create a new game' : 'Join an existing game'}</p>
            </div>
            <button className="btn btn-back" onClick={handleBack}>
              ← Back
            </button>
            {mode === 'host' && (
              <button className="btn btn-primary" onClick={handleConfirmHost}>
                Proceed to Host
              </button>
            )}
            {mode === 'join' && (
              <button className="btn btn-primary" onClick={handleConfirmJoin}>
                Find Games
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};