/**
 * Main App component
 */

import React, { useState } from 'react';
import { GameBoard } from './components/GameBoard';
import { GameLobby } from './components/GameLobby';
import { LandingPage } from './components/LandingPage';
import './styles/index.css';

type ViewState = 'landing' | 'lobby' | 'game';

export const App: React.FC = () => {
  const [viewState, setViewState] = useState<ViewState>('landing');
  const [gameId, setGameId] = useState<string>('');
  const [playerName, setPlayerName] = useState<string>('');
  const [mode, setMode] = useState<'host' | 'join'>('join');

  const handleHost = (name: string) => {
    setPlayerName(name);
    setMode('host');
    setViewState('lobby');
  };

  const handleJoin = (name: string) => {
    setPlayerName(name);
    setMode('join');
    setViewState('lobby');
  };

  const handleStartGame = (id: string, name: string) => {
    setGameId(id);
    setPlayerName(name);
    setViewState('game');
  };

  const handleBackToLanding = () => {
    setViewState('landing');
    setPlayerName('');
    setGameId('');
  };

  return (
    <div className="app">
      {viewState === 'landing' && (
        <LandingPage onHost={handleHost} onJoin={handleJoin} />
      )}
      {viewState === 'lobby' && (
        <GameLobby
          mode={mode}
          playerName={playerName}
          onStartGame={handleStartGame}
          onBack={handleBackToLanding}
        />
      )}
      {viewState === 'game' && (
        <GameBoard gameId={gameId} playerName={playerName} />
      )}
    </div>
  );
};

export default App;