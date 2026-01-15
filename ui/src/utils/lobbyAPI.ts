/**
 * API utility functions for lobby operations
 * Add these to your existing ui/src/utils/api.ts file
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

class LobbyAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Create a new lobby
   */
  async createLobby(name: string, username: string) {
    const response = await axios.post(`${API_BASE_URL}/api/lobby`, {
      name,
      username,
    });
    return response.data;
  }

  /**
   * List all available lobbies
   */
  async listLobbies() {
    const response = await axios.get(`${API_BASE_URL}/api/lobby`);
    return response.data;
  }

  /**
   * Get details for a specific lobby
   */
  async getLobby(lobbyId: string) {
    const response = await axios.get(`${API_BASE_URL}/api/lobby/${lobbyId}`);
    return response.data;
  }

  /**
   * Join an existing lobby
   */
  async joinLobby(lobbyId: string, username: string) {
    const response = await axios.post(`${API_BASE_URL}/api/lobby/${lobbyId}/join`, {
      username,
    });
    return response.data;
  }

  /**
   * Leave a lobby
   */
  async leaveLobby(lobbyId: string, username: string) {
    const response = await axios.post(`${API_BASE_URL}/api/lobby/${lobbyId}/leave`, {
      username,
    });
    return response.data;
  }

  /**
   * Choose a deck for your character
   */
  async chooseDeck(lobbyId: string, username: string, deckId: string) {
    const response = await axios.put(`${API_BASE_URL}/api/lobby/${lobbyId}/deck`, {
      username,
      deck_id: deckId,
    });
    return response.data;
  }

  /**
   * Set the encounter deck (host only)
   */
  async setEncounterDeck(lobbyId: string, username: string, encounterDeckId: string) {
    const response = await axios.put(`${API_BASE_URL}/api/lobby/${lobbyId}/encounter`, {
      username,
      encounter_deck_id: encounterDeckId,
    });
    return response.data;
  }

  /**
   * Toggle ready status
   */
  async toggleReady(lobbyId: string, username: string) {
    const response = await axios.post(`${API_BASE_URL}/api/lobby/${lobbyId}/ready`, {
      username,
    });
    return response.data;
  }

  /**
   * Start the game (host only)
   */
  async startGame(lobbyId: string, username: string) {
    const response = await axios.post(`${API_BASE_URL}/api/lobby/${lobbyId}/start`, {
      username,
    });
    return response.data;
  }

  /**
   * Delete a lobby (host only)
   */
  async deleteLobby(lobbyId: string, username: string) {
    const response = await axios.delete(`${API_BASE_URL}/api/lobby/${lobbyId}`, {
      data: { username },
    });
    return response.data;
  }
};

export const deckAPI = {
  /**
   * List all decks
   */
  async listDecks() {
    const response = await axios.get(`${API_BASE_URL}/api/decks`);
    return response.data;
  },

  /**
   * Get a specific deck
   */
  async getDeck(deckId: string) {
    const response = await axios.get(`${API_BASE_URL}/api/decks/${deckId}`);
    return response.data;
  },
};

export const gameAPI = {
  /**
   * Get game state
   */
  async getGame(gameId: string) {
    const response = await axios.get(`${API_BASE_URL}/api/games/${gameId}`);
    return response.data;
  },

  /**
   * Draw a card
   */
  async drawCard(gameId: string, playerName: string) {
    const response = await axios.post(`${API_BASE_URL}/api/games/${gameId}/draw`, {
      player_name: playerName,
    });
    return response.data;
  },

  /**
   * Play a card to the table
   */
  async playCard(gameId: string, playerName: string, cardCode: string, zone: string) {
    const response = await axios.post(`${API_BASE_URL}/api/games/${gameId}/play`, {
      player_name: playerName,
      card_code: cardCode,
      x: 400, // Default position
      y: 300,
    });
    return response.data;
  },

  /**
   * Draw encounter card
   */
  async drawEncounterCard(gameId: string) {
    // This endpoint may need to be added to your backend
    const response = await axios.post(`${API_BASE_URL}/api/games/${gameId}/encounter/draw`);
    return response.data;
  },

  /**
   * Shuffle encounter discard
   */
  async shuffleEncounterDiscard(gameId: string) {
    // This endpoint may need to be added to your backend
    const response = await axios.post(`${API_BASE_URL}/api/games/${gameId}/encounter/shuffle`);
    return response.data;
  },
};

export const lobbyAPI = new LobbyAPI();
