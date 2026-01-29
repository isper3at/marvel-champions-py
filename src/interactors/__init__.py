# Card Interactors
from .card import (
    ImportCardInteractor,
    GetCardInteractor,
    SearchCardsInteractor,
    GetCardImageInteractor,
)

# Deck Interactors
from .deck import (
    ImportDeckInteractor,
    GetDeckInteractor,
    UpdateDeckInteractor,
    DeleteDeckInteractor,
    ListDecksInteractor,
)

# Lobby Interactors
from .lobby import (
    CreateLobbyInteractor,
    JoinLobbyInteractor,
    LeaveLobbyInteractor,
    ChooseDeckInteractor,
    ToggleReadyInteractor,
    StartGameInteractor,
    BuildEncounterDeckInteractor,
    ListLobbiesInteractor,
    DeleteLobbyInteractor,
)

# Game Interactors
from .game import (
    CreateGameInteractor,
    GetGameInteractor,
    ListGamesInteractor,
    DrawCardInteractor,
    ShuffleDiscardInteractor,
    PlayCardInteractor,
    MoveCardInteractor,
    ToggleCardExhaustionInteractor,
    AddCounterInteractor,
    SaveGameInteractor,
    DeleteGameInteractor,
)

# Keep legacy monoliths for backward compatibility (deprecate later)
from .card_interactor import CardInteractor
from .deck_interactor import DeckInteractor
from .game_interactor import GameInteractor
from .lobby_interactor import LobbyInteractor

__all__ = [
    # Card
    'ImportCardInteractor',
    'GetCardInteractor',
    'SearchCardsInteractor',
    'GetCardImageInteractor',
    # Deck
    'ImportDeckInteractor',
    'GetDeckInteractor',
    'UpdateDeckInteractor',
    'DeleteDeckInteractor',
    'ListDecksInteractor',
    # Lobby
    'CreateLobbyInteractor',
    'JoinLobbyInteractor',
    'LeaveLobbyInteractor',
    'ChooseDeckInteractor',
    'ToggleReadyInteractor',
    'StartGameInteractor',
    'BuildEncounterDeckInteractor',
    'ListLobbiesInteractor',
    'DeleteLobbyInteractor',
    # Game
    'CreateGameInteractor',
    'GetGameInteractor',
    'ListGamesInteractor',
    'DrawCardInteractor',
    'ShuffleDiscardInteractor',
    'PlayCardInteractor',
    'MoveCardInteractor',
    'ToggleCardExhaustionInteractor',
    'AddCounterInteractor',
    'SaveGameInteractor',
    'DeleteGameInteractor',
    # Legacy (deprecated)
    'CardInteractor',
    'DeckInteractor',
    'GameInteractor',
    'LobbyInteractor',
]
