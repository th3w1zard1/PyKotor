"""Data module for HoloPazaak.

This module provides opponent profiles and game configuration data.
"""
from holopazaak.data.opponents import (
    OPPONENTS,
    OpponentDifficulty,
    OpponentPhrases,
    OpponentProfile,
    get_all_opponent_ids,
    get_opponent,
    get_opponents_by_difficulty,
    get_random_opponent,
)

__all__ = [
    "OPPONENTS",
    "OpponentDifficulty",
    "OpponentPhrases",
    "OpponentProfile",
    "get_opponent",
    "get_opponents_by_difficulty",
    "get_all_opponent_ids",
    "get_random_opponent",
]

