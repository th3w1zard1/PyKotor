"""HoloPazaak - The Ultimate Pazaak Implementation.

HoloPazaak is a comprehensive Pazaak game implementation combining the best
features from multiple open-source Pazaak projects:

- pazaak-eggborne: Character system, AI strategies, card flip animations
- vue-pazaak: Game state management, turn logic
- pazaak-iron-ginger: Opponent profiles, difficulty levels
- Java_Pazaak: Special card effects, AI decision making
- PazaakApp: Card helper functions, round resolution
- GetLucky33: Additional game rules and variants

Features:
- All standard Pazaak card types (Plus, Minus, Flip, Double, Tiebreaker)
- Multiple AI difficulty levels (Novice, Easy, Normal, Hard, Expert, Master)
- Character-based opponents with unique personalities and phrases
- Multiplayer support via WebSocket networking
- Beautiful PyQt6-based UI with theme support
- Sound effects and animations

Usage:
    # Run as module
    python -m holopazaak
    
    # Or import and use programmatically
    from holopazaak import PazaakGame, Player, AIPlayer
    from holopazaak.data import get_opponent
    
    player = Player("Hero")
    opponent = AIPlayer(get_opponent("hk47"))
    game = PazaakGame(player, opponent)
    game.start_game()

Version: 1.0.0
License: LGPL-2.1-only
"""
from __future__ import annotations

__version__ = "1.0.0"
__author__ = "PyKotor Team"

# Core exports
from holopazaak.game import (
    Card,
    CardType,
    Player,
    PlayerState,
    PazaakGame,
    GamePhase,
    RoundResult,
)
from holopazaak.ai import AIPlayer
from holopazaak.data import get_opponent, OPPONENTS

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Core game
    "Card",
    "CardType",
    "Player",
    "PlayerState",
    "PazaakGame",
    "GamePhase",
    "RoundResult",
    # AI
    "AIPlayer",
    # Data
    "get_opponent",
    "OPPONENTS",
]

