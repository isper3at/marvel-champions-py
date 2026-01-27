import React, { useState } from 'react';

interface GameSetupProps {
  playerName: string;
  onCreateGame: (gameId: string) => void;
  onBack: () => void;
}

interface DeckCard {
  code: string;
  name: string;
  quantity: number;
  type_code?: string;
  faction_code?: string;
  cost?: number;
}

interface EncounterDeck {
  id: string;
  name: string;
  cards: DeckCard[];
  villain_cards: DeckCard[];
  main_scheme_cards: DeckCard[];
  scenario_cards: DeckCard[];
}

interface PlayerDeck {
  id: string;
  name: string;
  cards: DeckCard[];
}

const GameSetup: React.FC<GameSetupProps> = ({ playerName, onCreateGame, onBack }) => {
  const [gameName, setGameName] = useState('');
  const [moduleNames, setModuleNames] = useState<string[]>(['']);
  const [encounterDeck, setEncounterDeck] = useState<EncounterDeck | null>(null);
  const [deckCode, setDeckCode] = useState('');
  const [playerDeck, setPlayerDeck] = useState<PlayerDeck | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addModuleInput = () => {
    setModuleNames([...moduleNames, '']);
  };

  const updateModule = (index: number, value: string) => {
    const updated = [...moduleNames];
    updated[index] = value;
    setModuleNames(updated);
  };

  const removeModule = (index: number) => {
    setModuleNames(moduleNames.filter((_, i) => i !== index));
  };

  const buildEncounterDeck = async () => {
    const validModules = moduleNames.filter(m => m.trim());
    if (validModules.length === 0) {
      setError('Please enter at least one module name');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/encounter/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_names: validModules })
      });

      if (!response.ok) throw new Error('Failed to build encounter deck');

      const data = await response.json();
      setEncounterDeck(data.encounter_deck);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to build encounter deck');
    } finally {
      setLoading(false);
    }
  };

  const loadDeck = async () => {
    if (!deckCode.trim()) {
      setError('Please enter a deck code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/decks/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deck_id: deckCode })
      });

      if (!response.ok) throw new Error('Failed to load deck');

      const data = await response.json();
      setPlayerDeck(data.deck);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load deck');
    } finally {
      setLoading(false);
    }
  };

  const createGame = async () => {
    if (!gameName.trim()) {
      setError('Please enter a game name');
      return;
    }
    if (!encounterDeck) {
      setError('Please build an encounter deck first');
      return;
    }
    if (!playerDeck) {
      setError('Please load your player deck first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/lobby', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: gameName,
          username: playerName,
          encounter_deck_id: encounterDeck.id,
          deck_id: playerDeck.id
        })
      });

      if (!response.ok) throw new Error('Failed to create game');

      const data = await response.json();
      onCreateGame(data.lobby.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create game');
    } finally {
      setLoading(false);
    }
  };

  const groupCardsByType = (cards: DeckCard[]) => {
    const groups: { [key: string]: DeckCard[] } = {};
    cards.forEach(card => {
      const type = card.type_code || 'other';
      if (!groups[type]) groups[type] = [];
      groups[type].push(card);
    });
    return groups;
  };

  const renderDeckList = (deck: EncounterDeck | PlayerDeck | null, title: string) => {
    if (!deck) return null;

    const isEncounter = 'villain_cards' in deck;
    const allCards = isEncounter 
      ? [...deck.cards, ...deck.villain_cards, ...deck.main_scheme_cards, ...deck.scenario_cards]
      : deck.cards;

    const grouped = groupCardsByType(allCards);
    const totalCards = allCards.reduce((sum, card) => sum + card.quantity, 0);

    return (
      <div className="deck-display">
        <div className="deck-header">
          <h3>{title}</h3>
          <div className="deck-meta">
            <span className="card-count">{totalCards} cards</span>
          </div>
        </div>

        <div className="deck-content">
          {Object.entries(grouped).map(([type, cards]) => (
            <div key={type} className="card-type-section">
              <h5 className="type-header">
                <span className="icon">{getTypeIcon(type)}</span>
                {formatTypeName(type)} ({cards.reduce((sum, c) => sum + c.quantity, 0)})
              </h5>
              <div className="card-list">
                {cards.map(card => (
                  <div key={card.code} className="card-entry">
                    <span className="quantity">{card.quantity}x</span>
                    <span className="card-name">{card.name}</span>
                    {card.cost !== undefined && (
                      <span className="card-cost">[{card.cost}]</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const getTypeIcon = (type: string) => {
    const icons: { [key: string]: string } = {
      'ally': '👥',
      'event': '⚡',
      'support': '🛡️',
      'upgrade': '⬆️',
      'resource': '💎',
      'villain': '👹',
      'main_scheme': '📜',
      'minion': '👤',
      'treachery': '💀',
      'attachment': '📎',
      'side_scheme': '📋'
    };
    return icons[type] || '🃏';
  };

  const formatTypeName = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="game-setup">
      <div className="setup-container">
        <div className="setup-header">
          <h1>Game Setup</h1>
          <p>Host: {playerName}</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="setup-grid">
          {/* Left Panel - Configuration */}
          <div className="config-panel">
            <section className="setup-section">
              <label htmlFor="game-name">Game Name</label>
              <input
                id="game-name"
                type="text"
                placeholder="Enter game name"
                value={gameName}
                onChange={(e) => setGameName(e.target.value)}
              />
            </section>

            <section className="setup-section">
              <h3>Encounter Modules</h3>
              {moduleNames.map((module, index) => (
                <div key={index} className="module-input-group">
                  <input
                    type="text"
                    placeholder="Module name (e.g., 'Kree Fanatic')"
                    value={module}
                    onChange={(e) => updateModule(index, e.target.value)}
                  />
                  {moduleNames.length > 1 && (
                    <button
                      className="btn-remove"
                      onClick={() => removeModule(index)}
                      type="button"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
              <div className="button-group">
                <button className="btn btn-secondary" onClick={addModuleInput}>
                  + Add Module
                </button>
                <button 
                  className="btn btn-primary" 
                  onClick={buildEncounterDeck}
                  disabled={loading || !moduleNames.some(m => m.trim())}
                >
                  {loading ? 'Building...' : 'Build Encounter Deck'}
                </button>
              </div>
            </section>

            <section className="setup-section">
              <h3>Player Deck</h3>
              <div className="deck-input-group">
                <input
                  type="text"
                  placeholder="Enter deck code or ID"
                  value={deckCode}
                  onChange={(e) => setDeckCode(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && loadDeck()}
                />
                <button 
                  className="btn btn-primary" 
                  onClick={loadDeck}
                  disabled={loading || !deckCode.trim()}
                >
                  {loading ? 'Loading...' : 'Load Deck'}
                </button>
              </div>
            </section>

            <div className="action-buttons">
              <button className="btn btn-back" onClick={onBack}>
                ← Back
              </button>
              <button
                className="btn btn-success"
                onClick={createGame}
                disabled={loading || !gameName || !encounterDeck || !playerDeck}
              >
                Create Game
              </button>
            </div>
          </div>

          {/* Right Panel - Deck Previews */}
          <div className="preview-panel">
            {encounterDeck && renderDeckList(encounterDeck, 'Encounter Deck')}
            {playerDeck && renderDeckList(playerDeck, 'Player Deck')}
            
            {!encounterDeck && !playerDeck && (
              <div className="preview-placeholder">
                <p>Deck previews will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .game-setup {
          min-height: 100vh;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          padding: 40px 20px;
          color: #ffffff;
        }

        .setup-container {
          max-width: 1400px;
          margin: 0 auto;
        }

        .setup-header {
          text-align: center;
          margin-bottom: 40px;
        }

        .setup-header h1 {
          color: #ffd700;
          font-size: 36px;
          margin-bottom: 8px;
        }

        .setup-header p {
          color: rgba(255, 255, 255, 0.7);
        }

        .error-message {
          background: rgba(255, 59, 48, 0.2);
          border: 1px solid rgba(255, 59, 48, 0.5);
          color: #ff6b6b;
          padding: 12px 16px;
          border-radius: 6px;
          margin-bottom: 20px;
        }

        .setup-grid {
          display: grid;
          grid-template-columns: 500px 1fr;
          gap: 30px;
        }

        .config-panel {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 30px;
        }

        .setup-section {
          margin-bottom: 30px;
        }

        .setup-section h3 {
          color: #ffd700;
          margin-bottom: 16px;
          font-size: 18px;
        }

        .setup-section label {
          display: block;
          color: rgba(255, 255, 255, 0.8);
          margin-bottom: 8px;
          font-size: 14px;
          font-weight: 500;
        }

        .setup-section input[type="text"] {
          width: 100%;
          padding: 12px 16px;
          border: 2px solid rgba(255, 255, 255, 0.2);
          border-radius: 6px;
          background: rgba(255, 255, 255, 0.1);
          color: #ffffff;
          font-size: 16px;
          transition: all 0.3s ease;
        }

        .setup-section input:focus {
          outline: none;
          border-color: #ffd700;
          background: rgba(255, 255, 255, 0.15);
        }

        .module-input-group {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }

        .module-input-group input {
          flex: 1;
        }

        .btn-remove {
          padding: 8px 16px;
          background: rgba(255, 59, 48, 0.2);
          border: 1px solid rgba(255, 59, 48, 0.5);
          color: #ff6b6b;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .btn-remove:hover {
          background: rgba(255, 59, 48, 0.3);
        }

        .deck-input-group {
          display: flex;
          gap: 12px;
        }

        .deck-input-group input {
          flex: 1;
        }

        .button-group {
          display: flex;
          gap: 12px;
          margin-top: 16px;
        }

        .btn {
          padding: 12px 24px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-primary {
          background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
          color: #1a1a2e;
          flex: 1;
        }

        .btn-primary:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(255, 215, 0, 0.4);
        }

        .btn-secondary {
          background: rgba(255, 255, 255, 0.1);
          color: #ffffff;
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .btn-secondary:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.15);
        }

        .btn-success {
          background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
          color: #ffffff;
          width: 100%;
        }

        .btn-success:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(76, 175, 80, 0.4);
        }

        .btn-back {
          background: rgba(255, 255, 255, 0.1);
          color: #ffffff;
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .action-buttons {
          display: flex;
          gap: 12px;
          margin-top: 30px;
        }

        .action-buttons .btn-back {
          flex: 0 0 auto;
        }

        .action-buttons .btn-success {
          flex: 1;
        }

        .preview-panel {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .preview-placeholder {
          background: rgba(255, 255, 255, 0.03);
          border: 2px dashed rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 60px;
          text-align: center;
          color: rgba(255, 255, 255, 0.4);
        }

        /* MarvelCDB-style Deck Display */
        .deck-display {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          overflow: hidden;
        }

        .deck-header {
          background: rgba(255, 215, 0, 0.1);
          border-bottom: 1px solid rgba(255, 215, 0, 0.3);
          padding: 20px;
        }

        .deck-header h3 {
          color: #ffd700;
          font-size: 20px;
          margin: 0 0 8px 0;
        }

        .deck-meta {
          display: flex;
          gap: 16px;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.7);
        }

        .card-count {
          font-weight: 600;
        }

        .deck-content {
          padding: 20px;
        }

        .card-type-section {
          margin-bottom: 20px;
        }

        .card-type-section:last-child {
          margin-bottom: 0;
        }

        .type-header {
          color: #ffd700;
          font-size: 14px;
          font-weight: bold;
          text-transform: uppercase;
          margin: 0 0 12px 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .type-header .icon {
          font-size: 16px;
        }

        .card-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .card-entry {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 4px 8px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 4px;
          font-size: 13px;
          transition: background 0.2s ease;
        }

        .card-entry:hover {
          background: rgba(255, 255, 255, 0.08);
        }

        .quantity {
          color: rgba(255, 255, 255, 0.6);
          font-weight: 600;
          min-width: 25px;
        }

        .card-name {
          flex: 1;
          color: rgba(255, 255, 255, 0.9);
        }

        .card-cost {
          color: #ffd700;
          font-weight: 600;
          font-size: 12px;
        }

        @media (max-width: 1200px) {
          .setup-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default GameSetup;