"""Network protocol for Pazaak multiplayer.

This module defines the message format and types for client-server
communication in multiplayer Pazaak games.

Based on WebSocket messaging patterns from PazaakApp.

Reference: vendor/PazaakApp/server/server.js
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any


class MessageType(Enum):
    """Types of messages in the protocol."""
    # Connection
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Game management
    HOST_GAME = "host_game"
    JOIN_GAME = "join_game"
    LEAVE_GAME = "leave_game"
    GAME_LIST = "game_list"
    GAME_START = "game_start"
    GAME_END = "game_end"
    
    # Player management
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PLAYER_READY = "player_ready"
    
    # Game actions
    CARD_PLAYED = "card_played"
    CARD_DRAWN = "card_drawn"
    STAND = "stand"
    END_TURN = "end_turn"
    
    # Game state
    GAME_STATE = "game_state"
    ROUND_START = "round_start"
    ROUND_END = "round_end"
    
    # Social
    CHAT_MESSAGE = "chat_message"
    EMOTE = "emote"


@dataclass
class GameMessage:
    """A network message.
    
    Attributes:
        msg_type: The type of message
        player_id: ID of the sending player (optional)
        game_id: ID of the game (optional)
        data: Additional data payload
    """
    msg_type: MessageType
    player_id: str | None = None
    game_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.msg_type.value,
            "player_id": self.player_id,
            "game_id": self.game_id,
            "data": self.data,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GameMessage | None:
        """Create from dictionary."""
        try:
            msg_type = MessageType(d.get("type", ""))
            return cls(
                msg_type=msg_type,
                player_id=d.get("player_id"),
                game_id=d.get("game_id"),
                data=d.get("data", {}),
            )
        except (ValueError, KeyError):
            return None
    
    @classmethod
    def from_json(cls, json_str: str) -> GameMessage | None:
        """Create from JSON string."""
        try:
            return cls.from_dict(json.loads(json_str))
        except json.JSONDecodeError:
            return None


def create_message(
    msg_type: MessageType,
    player_id: str | None = None,
    game_id: str | None = None,
    **kwargs,
) -> GameMessage:
    """Create a message with the given parameters."""
    return GameMessage(
        msg_type=msg_type,
        player_id=player_id,
        game_id=game_id,
        data=kwargs,
    )


def parse_message(raw: str) -> GameMessage | None:
    """Parse a raw message string."""
    return GameMessage.from_json(raw)


def msg_error(error_text: str) -> GameMessage:
    """Create an error message."""
    return create_message(MessageType.ERROR, message=error_text)


# Game state message payload structure
@dataclass
class GameStatePayload:
    """Payload for GAME_STATE messages.
    
    Contains the complete game state for synchronization.
    """
    round_number: int = 0
    turn_number: int = 0
    current_player_id: str = ""
    
    # Player 1 state
    p1_score: int = 0
    p1_sets_won: int = 0
    p1_is_standing: bool = False
    p1_is_bust: bool = False
    p1_board: list[dict] = field(default_factory=list)
    p1_hand_size: int = 0
    
    # Player 2 state  
    p2_score: int = 0
    p2_sets_won: int = 0
    p2_is_standing: bool = False
    p2_is_bust: bool = False
    p2_board: list[dict] = field(default_factory=list)
    p2_hand_size: int = 0
    
    # Round/game status
    is_round_over: bool = False
    is_game_over: bool = False
    round_winner_id: str | None = None
    game_winner_id: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "round_number": self.round_number,
            "turn_number": self.turn_number,
            "current_player_id": self.current_player_id,
            "p1_score": self.p1_score,
            "p1_sets_won": self.p1_sets_won,
            "p1_is_standing": self.p1_is_standing,
            "p1_is_bust": self.p1_is_bust,
            "p1_board": self.p1_board,
            "p1_hand_size": self.p1_hand_size,
            "p2_score": self.p2_score,
            "p2_sets_won": self.p2_sets_won,
            "p2_is_standing": self.p2_is_standing,
            "p2_is_bust": self.p2_is_bust,
            "p2_board": self.p2_board,
            "p2_hand_size": self.p2_hand_size,
            "is_round_over": self.is_round_over,
            "is_game_over": self.is_game_over,
            "round_winner_id": self.round_winner_id,
            "game_winner_id": self.game_winner_id,
        }


# Card payload for network transfer
@dataclass
class CardPayload:
    """Card data for network transfer."""
    name: str
    value: int
    card_type: str  # String enum value
    is_flipped: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "card_type": self.card_type,
            "is_flipped": self.is_flipped,
        }
