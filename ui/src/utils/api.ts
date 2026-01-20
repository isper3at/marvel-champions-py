/**
 * API client for Marvel Champions backend
 */

import axios, { AxiosInstance } from 'axios';
import {
  GameState,
  Card,
  Deck,
  Position,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class GameAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Games
  async listGames(): Promise<GameState[]> {
    const response = await this.client.get('/games');
    // Backend returns { games: [...], count: ... }, extract the games array
    return response.data.games || [];
  }

  async getGame(gameId: string): Promise<GameState> {
    const response = await this.client.get(`/games/${gameId}`);
    return response.data;
  }

  async deleteGame(gameId: string): Promise<void> {
    await this.client.delete(`/games/${gameId}`);
  }

  // Game Actions
  async drawCard(gameId: string, playerName: string): Promise<void> {
    await this.client.post(
      `/games/${gameId}/draw`,
      { player_name: playerName }
    );
  }

  async playCard(
    gameId: string,
    playerName: string,
    cardCode: string,
    zone: string
  ): Promise<void> {
    await this.client.post(
      `/games/${gameId}/play`,
      {
        player_name: playerName,
        card_code: cardCode,
        zone,
      }
    );
  }

  async moveCard(
    gameId: string,
    playerName: string,
    cardId: string,
    sourceZone: string,
    targetZone: string,
    position?: Position
  ): Promise<void> {
    await this.client.post(
      `/games/${gameId}/move`,
      {
        player_name: playerName,
        card_id: cardId,
        source_zone: sourceZone,
        target_zone: targetZone,
        position,
      }
    );
  }

  async rotateCard(
    gameId: string,
    playerName: string,
    cardId: string
  ): Promise<void> {
    await this.client.post(
      `/games/${gameId}/rotate`,
      {
        player_name: playerName,
        card_id: cardId,
      }
    );
  }

  async updateCardCounter(
    gameId: string,
    playerName: string,
    cardId: string,
    counterValue: number
  ): Promise<void> {
    await this.client.post(
      `/games/${gameId}/counter`,
      {
        player_name: playerName,
        card_id: cardId,
        counter: counterValue,
      }
    );
  }

  async drawEncounterCard(gameId: string): Promise<void> {
    await this.client.post(
      `/games/${gameId}/draw`,
      { zone: 'encounter' }
    );
  }

  async shuffleEncounterDiscard(gameId: string): Promise<void> {
    const response = await this.client.post(
      `/games/${gameId}/shuffle`,
      { zone: 'encounter_discard' }
    );
    return response.data;
  }

  // Decks
  async getDeck(deckId: string): Promise<Deck> {
    const response = await this.client.get(`/decks/${deckId}`);
    return response.data;
  }

  async getDeckCards(deckId: string): Promise<Card[]> {
    const response = await this.client.get(`/decks/${deckId}/cards`);
    return response.data.cards || [];
  }

  // Cards
  async getCard(cardCode: string): Promise<Card> {
    const response = await this.client.get(`/cards/${cardCode}`);
    return response.data;
  }

  async searchCards(query: string): Promise<Card[]> {
    const response = await this.client.get('/cards/search', {
      params: { q: query },
    });
    return response.data.results || [];
  }

  async getCardImage(cardCode: string): Promise<string> {
    return `${API_BASE_URL}/cards/${cardCode}/image`;
  }
}

export const gameAPI = new GameAPI();
