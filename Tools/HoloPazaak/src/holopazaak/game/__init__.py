"""Game module for HoloPazaak.

This module provides the core game logic including cards, players,
and the game engine.
"""
from holopazaak.game.card import (
    Card,
    CardAction,
    CardType,
    apply_double_card_effect,
    apply_flip_card_effect,
    create_double_card,
    create_flip_card,
    create_flip_three_six_card,
    create_flip_two_four_card,
    create_main_deck_card,
    create_minus_card,
    create_plus_card,
    create_tiebreaker_card,
    get_all_side_deck_cards,
)
from holopazaak.game.engine import (
    GameEvent,
    GamePhase,
    PazaakGame,
    RoundResult,
)
from holopazaak.game.player import (
    Player,
    PlayerState,
    PlayerStats,
)

__all__ = [
    # Card
    "Card",
    "CardType",
    "CardAction",
    "create_main_deck_card",
    "create_plus_card",
    "create_minus_card",
    "create_flip_card",
    "create_double_card",
    "create_tiebreaker_card",
    "create_flip_two_four_card",
    "create_flip_three_six_card",
    "get_all_side_deck_cards",
    "apply_flip_card_effect",
    "apply_double_card_effect",
    # Player
    "Player",
    "PlayerState",
    "PlayerStats",
    # Engine
    "PazaakGame",
    "GamePhase",
    "RoundResult",
    "GameEvent",
]

