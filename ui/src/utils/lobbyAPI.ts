/**
 * API utility functions for lobby operations
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

class LobbyAPI {
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

  /**
   * Save an encounter deck configuration with a name
   * This will build the encounter deck from the provided modules and save it
   * 
   * @param moduleNames - Array of module names (e.g., ["Rhino", "Kree Fanatic"])
   * @param encounterName - Name to save this encounter deck configuration as
   */
  async saveEncounterDeck(moduleNames: string[], encounterName: string) {
    const response = await axios.post(`${API_BASE_URL}/api/lobby/encounter/save`, {
      module_names: moduleNames,
      name: encounterName,
    });
    return response.data;
  }

  /**
   * List all saved encounter deck configurations
   * Returns array of saved decks with their names and metadata
   */
  async listSavedEncounterDecks() {
    const response = await axios.get(`${API_BASE_URL}/api/lobby/encounter/saved`);
    return response.data;
  }

  /**
   * Load a saved encounter deck by name
   * Returns the module names that make up this encounter deck
   * 
   * @param encounterName - Name of the saved encounter deck
   * @returns Object with success flag and modules array
   */
  async loadSavedEncounterDeck(encounterName: string) {
    const response = await axios.get(
      `${API_BASE_URL}/api/lobby/encounter/load/${encodeURIComponent(encounterName)}`
    );
    return response.data;
  }
}

export const deckAPI = {
  /**
   * List all decks
   */
  async listDecks() {
    const response = await axios.get(`${API_BASE_URL}/api/decks`);
    return response.data;
  },

  /**
   * Get a specific deck by ID
   */
  async getDeck(deckId: string) {
    const response = await axios.get(`${API_BASE_URL}/api/decks/${deckId}`);
    return response.data;
  },

  /**
   * Import a deck from MarvelCDB
   */
  async importDeck(deckId: string) {
    const response = await axios.post(`${API_BASE_URL}/api/decks/import`, {
      deck_id: deckId,
    });
    return response.data;
  },

  /**
   * Delete a deck
   */
  async deleteDeck(deckId: string) {
    const response = await axios.delete(`${API_BASE_URL}/api/decks/${deckId}`);
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
  async playCard(gameId: string, playerName: string, cardCode: string) {
    const response = await axios.post(`${API_BASE_URL}/api/games/${gameId}/play`, {
      player_name: playerName,
      card_code: cardCode,
      x: 400,
      y: 300,
    });
    return response.data;
  },

  /**
   * Draw encounter card
   */
  async drawEncounterCard(gameId: string) {
    const response = await axios.post(`${API_BASE_URL}/api/games/${gameId}/encounter/draw`);
    return response.data;
  },

  /**
   * Shuffle encounter discard
   */
  async shuffleEncounterDiscard(gameId: string) {
    const response = await axios.post(`${API_BASE_URL}/api/games/${gameId}/encounter/shuffle`);
    return response.data;
  },
};

export const lobbyAPI = new LobbyAPI();