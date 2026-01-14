/**
 * Main App component
 */

import React, { useState } from 'react';
import { GameBoard } from './components/GameBoard';
import { GameLobby } from './components/GameLobby';
import './styles/index.css';

type ViewState = 'lobby' | 'game';

export const App: React.FC = () => {
  const [viewState, setViewState] = useState<ViewState>('lobby');
  const [gameId, setGameId] = useState<string>('');
  const [playerName, setPlayerName] = useState<string>('');

  const handleStartGame = (id: string, name: string) => {
    setGameId(id);
    setPlayerName(name);
    setViewState('game');
  };

  return (
    <div className="app">
      {viewState === 'lobby' ? (
        <GameLobby onStartGame={handleStartGame} />
      ) : (
        <GameBoard gameId={gameId} playerName={playerName} />
      )}
    </div>
  );
};

export default App;
