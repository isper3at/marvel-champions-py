/**
 * Landing page - Player enters name and chooses to join or host
 * Updated to navigate to GameCreation view
 */

import React, { useState } from 'react';
import '../styles/LandingPage.css';

interface LandingPageProps {
  onHost: (playerName: string) => void;
  onJoin: (playerName: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onHost, onJoin }) => {
  const [playerName, setPlayerName] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleHostClick = () => {
    if (!playerName.trim()) {
      setError('Please enter your name');
      return;
    }
    setError('');
    onHost(playerName.trim());
  };

  const handleJoinClick = () => {
    if (!playerName.trim()) {
      setError('Please enter your name');
      return;
    }
    setError('');
    onJoin(playerName.trim());
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && playerName.trim()) {
      handleHostClick();
    }
  };

  return (
    <div className="landing-page">
      <div className="landing-container">
        <h1>Marvel Champions</h1>
        
        <div className="landing-content">
          <div className="name-input-group">
            <label htmlFor="player-name">Enter Your Name</label>
            <input
              id="player-name"
              type="text"
              placeholder="Player Name"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyPress={handleKeyPress}
              autoFocus
            />
            {error && <span className="input-error">{error}</span>}
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
      </div>
    </div>
  );
};

export default LandingPage;