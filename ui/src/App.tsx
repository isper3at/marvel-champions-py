/**
 * Main App component
 * Updated to include GameCreation flow
 */

import React, { useState } from 'react';
import { GameBoard } from './components/GameBoard';
import { GameLobby } from './components/GameLobby';
import { GameCreation } from './components/GameCreation';
import { LandingPage } from './components/LandingPage';
import { lobbyAPI } from './utils/lobbyAPI';
import './styles/index.css';

type ViewState = 'landing' | 'lobby' | 'creation' | 'game';

export const App: React.FC = () => {
  const [viewState, setViewState] = useState<ViewState>('landing');
  const [gameId, setGameId] = useState<string>('');
  const [lobbyId, setLobbyId] = useState<string>('');
  const [playerName, setPlayerName] = useState<string>('');
  const [isHost, setIsHost] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  /**
   * Handle hosting a new game
   * Creates a lobby and navigates to GameCreation
   */
  const handleHost = async (name: string) => {
    setPlayerName(name);
    setIsHost(true);
    setError('');
    
    try {
      // Create a new lobby
      const response = await lobbyAPI.createLobby(`${name}'s Game`, name);
      setLobbyId(response.lobby.id);
      setViewState('creation');
    } catch (err) {
      console.error('Failed to create lobby:', err);
      setError('Failed to create game. Please try again.');
      // Stay on landing page to show error
    }
  };

  /**
   * Handle joining an existing game
   * Shows lobby list for selection
   */
  const handleJoin = (name: string) => {
    setPlayerName(name);
    setIsHost(false);
    setViewState('lobby');
  };

  /**
   * Handle joining a specific lobby from the lobby list
   * Navigates to GameCreation
   */
  const handleJoinLobby = async (selectedLobbyId: string) => {
    setError('');
    
    try {
      await lobbyAPI.joinLobby(selectedLobbyId, playerName);
      setLobbyId(selectedLobbyId);
      setViewState('creation');
    } catch (err) {
      console.error('Failed to join lobby:', err);
      setError('Failed to join game. It may have already started.');
    }
  };

  /**
   * Handle starting the game from GameCreation
   * Transitions to active game board
   */
  const handleStartGame = (startedGameId: string) => {
    setGameId(startedGameId);
    setViewState('game');
  };

  /**
   * Handle leaving GameCreation back to landing
   */
  const handleLeaveLobby = () => {
    setLobbyId('');
    setGameId('');
    setViewState('landing');
  };

  /**
   * Handle going back from lobby list to landing
   */
  const handleBackToLanding = () => {
    setViewState('landing');
    setPlayerName('');
    setGameId('');
    setLobbyId('');
    setError('');
  };

  return (
    <div className="app">
      {/* Landing Page - Enter name and choose host/join */}
      {viewState === 'landing' && (
        <LandingPage onHost={handleHost} onJoin={handleJoin} />
      )}

      {/* Lobby List - Browse and join existing games */}
      {viewState === 'lobby' && (
        <GameLobby
          playerName={playerName}
          onJoinLobby={handleJoinLobby}
          onBack={handleBackToLanding}
          error={error}
        />
      )}

      {/* Game Creation - Configure and ready up */}
      {viewState === 'creation' && (
        <GameCreation
          lobbyId={lobbyId}
          playerName={playerName}
          isHost={isHost}
          onStartGame={handleStartGame}
          onLeave={handleLeaveLobby}
        />
      )}

      {/* Game Board - Active game */}
      {viewState === 'game' && (
        <GameBoard gameId={gameId} playerName={playerName} />
      )}

      {/* Global error display (if needed at app level) */}
      {error && viewState === 'landing' && (
        <div className="app-error-banner">
          <span className="error-icon">⚠</span>
          {error}
          <button className="error-dismiss" onClick={() => setError('')}>
            ✕
          </button>
        </div>
      )}
    </div>
  );
};

export default App;