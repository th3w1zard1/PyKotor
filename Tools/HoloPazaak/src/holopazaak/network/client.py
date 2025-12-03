"""WebSocket client for Pazaak multiplayer.

This module implements the client-side multiplayer functionality.
Based on PazaakApp's client implementation.

Reference: vendor/PazaakApp/src/services/websocket.js
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketClientProtocol = Any  # type: ignore[misc]

from holopazaak.network.protocol import (
    GameMessage,
    MessageType,
    create_message,
    parse_message,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PazaakClient:
    """WebSocket client for multiplayer Pazaak.
    
    Handles:
    - Connection to the server
    - Message sending/receiving
    - Event dispatching to handlers
    
    Usage:
        client = PazaakClient("ws://localhost:8765")
        client.on_message(MessageType.GAME_START, handle_game_start)
        await client.connect()
        await client.host_game("PlayerName")
    """
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket: WebSocketClientProtocol | None = None
        self.player_id: str | None = None
        self.game_id: str | None = None
        
        # Message handlers by type
        self._handlers: dict[MessageType, list[Callable[[GameMessage], None]]] = {
            mt: [] for mt in MessageType
        }
        
        # Connection state
        self._connected = False
        self._receive_task: asyncio.Task | None = None
    
    @property
    def connected(self) -> bool:
        """Check if connected to server."""
        return self._connected and self.websocket is not None
    
    def on_message(self, msg_type: MessageType, handler: Callable[[GameMessage], None]):
        """Register a handler for a message type.
        
        Args:
            msg_type: The message type to handle
            handler: Callback function receiving the message
        """
        self._handlers[msg_type].append(handler)
    
    def off_message(self, msg_type: MessageType, handler: Callable[[GameMessage], None]):
        """Unregister a handler for a message type."""
        if handler in self._handlers[msg_type]:
            self._handlers[msg_type].remove(handler)
    
    async def connect(self) -> bool:
        """Connect to the server.
        
        Returns:
            True if connection successful
        """
        if not HAS_WEBSOCKETS:
            logger.error("websockets package not installed")
            return False
        
        try:
            self.websocket = await websockets.connect(self.server_url)
            self._connected = True
            
            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            logger.info(f"Connected to {self.server_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the server."""
        self._connected = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        logger.info("Disconnected from server")
    
    async def _receive_loop(self):
        """Loop receiving messages from server."""
        if not self.websocket:
            return
        
        try:
            async for raw_message in self.websocket:
                msg = parse_message(raw_message)
                if msg:
                    self._dispatch(msg)
                    
                    # Handle special messages
                    if msg.msg_type == MessageType.CONNECT:
                        self.player_id = msg.data.get("player_id")
                        logger.info(f"Assigned player ID: {self.player_id}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
        finally:
            self._connected = False
    
    def _dispatch(self, msg: GameMessage):
        """Dispatch a message to handlers."""
        for handler in self._handlers[msg.msg_type]:
            try:
                handler(msg)
            except Exception as e:
                logger.error(f"Handler error for {msg.msg_type}: {e}")
    
    async def send(self, msg: GameMessage):
        """Send a message to the server."""
        if not self.connected or not self.websocket:
            logger.warning("Not connected, cannot send message")
            return
        
        try:
            await self.websocket.send(msg.to_json())
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    # High-level API methods
    
    async def host_game(self, player_name: str = "Player"):
        """Host a new game."""
        await self.send(create_message(
            MessageType.HOST_GAME,
            player_id=self.player_id,
            player_name=player_name,
        ))
    
    async def join_game(self, game_id: str, player_name: str = "Player"):
        """Join an existing game."""
        await self.send(create_message(
            MessageType.JOIN_GAME,
            player_id=self.player_id,
            game_id=game_id,
            player_name=player_name,
        ))
    
    async def leave_game(self):
        """Leave the current game."""
        await self.send(create_message(
            MessageType.LEAVE_GAME,
            player_id=self.player_id,
            game_id=self.game_id,
        ))
        self.game_id = None
    
    async def list_games(self):
        """Request list of available games."""
        await self.send(create_message(
            MessageType.GAME_LIST,
            player_id=self.player_id,
        ))
    
    async def play_card(self, card_index: int, flip_to_minus: bool = False):
        """Play a card from hand."""
        await self.send(create_message(
            MessageType.CARD_PLAYED,
            player_id=self.player_id,
            game_id=self.game_id,
            card_index=card_index,
            flip_to_minus=flip_to_minus,
        ))
    
    async def stand(self):
        """Stand with current score."""
        await self.send(create_message(
            MessageType.STAND,
            player_id=self.player_id,
            game_id=self.game_id,
        ))
    
    async def end_turn(self):
        """End the current turn."""
        await self.send(create_message(
            MessageType.END_TURN,
            player_id=self.player_id,
            game_id=self.game_id,
        ))
    
    async def send_chat(self, message: str):
        """Send a chat message."""
        await self.send(create_message(
            MessageType.CHAT_MESSAGE,
            player_id=self.player_id,
            game_id=self.game_id,
            message=message,
        ))
    
    async def ping(self):
        """Ping the server."""
        await self.send(create_message(MessageType.PING))
