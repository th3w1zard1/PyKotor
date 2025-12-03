"""Network module for HoloPazaak multiplayer.

This module provides WebSocket-based multiplayer networking.
"""
from holopazaak.network.protocol import (
    CardPayload,
    GameMessage,
    GameStatePayload,
    MessageType,
    create_message,
    msg_error,
    parse_message,
)
from holopazaak.network.server import PazaakServer
from holopazaak.network.client import PazaakClient

__all__ = [
    # Protocol
    "MessageType",
    "GameMessage",
    "GameStatePayload",
    "CardPayload",
    "create_message",
    "parse_message",
    "msg_error",
    # Server
    "PazaakServer",
    # Client
    "PazaakClient",
]
