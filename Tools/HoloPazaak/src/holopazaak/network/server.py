"""WebSocket server for Pazaak multiplayer.

This module implements the server-side multiplayer functionality.
Based on PazaakApp's server implementation.

Reference: vendor/PazaakApp/server/server.js

Usage:
    python -m holopazaak.network.server --port 8765
    
Or:
    holopazaak-server --port 8765
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketServerProtocol = Any  # type: ignore[misc]

from holopazaak.network.protocol import (
    GameMessage,
    MessageType,
    create_message,
    msg_error,
    parse_message,
)

if TYPE_CHECKING:
    from collections.abc import Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ConnectedPlayer:
    """A connected player."""
    player_id: str
    name: str
    websocket: WebSocketServerProtocol
    game_id: str | None = None


@dataclass
class GameRoom:
    """A multiplayer game room."""
    game_id: str
    host_id: str
    players: list[str] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    is_started: bool = False
    is_finished: bool = False


class PazaakServer:
    """WebSocket server for Pazaak multiplayer games.
    
    Handles:
    - Player connections and disconnections
    - Game room creation and joining
    - Game state synchronization
    - Action relay between players
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        
        # Connected players by websocket
        self.players: dict[WebSocketServerProtocol, ConnectedPlayer] = {}
        # Players by ID
        self.players_by_id: dict[str, ConnectedPlayer] = {}
        # Game rooms
        self.games: dict[str, GameRoom] = {}
    
    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle a new WebSocket connection."""
        player_id = str(uuid.uuid4())[:8]
        player = ConnectedPlayer(
            player_id=player_id,
            name=f"Player_{player_id}",
            websocket=websocket,
        )
        
        self.players[websocket] = player
        self.players_by_id[player_id] = player
        
        logger.info(f"Player connected: {player_id}")
        
        # Send welcome message
        await self._send(websocket, create_message(
            MessageType.CONNECT,
            player_id=player_id,
            success=True,
        ))
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._handle_disconnect(websocket)
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, raw_message: str):
        """Handle an incoming message."""
        msg = parse_message(raw_message)
        if not msg:
            await self._send(websocket, msg_error("Invalid message format"))
            return
        
        player = self.players.get(websocket)
        if not player:
            await self._send(websocket, msg_error("Not connected"))
            return
        
        # Update player ID from message if provided
        if msg.player_id:
            player.player_id = msg.player_id
        
        handlers = {
            MessageType.PING: self._handle_ping,
            MessageType.HOST_GAME: self._handle_host_game,
            MessageType.JOIN_GAME: self._handle_join_game,
            MessageType.LEAVE_GAME: self._handle_leave_game,
            MessageType.GAME_LIST: self._handle_game_list,
            MessageType.CARD_PLAYED: self._handle_card_played,
            MessageType.STAND: self._handle_stand,
            MessageType.END_TURN: self._handle_end_turn,
            MessageType.CHAT_MESSAGE: self._handle_chat,
        }
        
        handler = handlers.get(msg.msg_type)
        if handler:
            await handler(player, msg)
        else:
            await self._send(websocket, msg_error(f"Unknown message type: {msg.msg_type}"))
    
    async def _handle_disconnect(self, websocket: WebSocketServerProtocol):
        """Handle player disconnection."""
        player = self.players.pop(websocket, None)
        if not player:
            return
        
        self.players_by_id.pop(player.player_id, None)
        logger.info(f"Player disconnected: {player.player_id}")
        
        # Remove from game if in one
        if player.game_id:
            game = self.games.get(player.game_id)
            if game:
                if player.player_id in game.players:
                    game.players.remove(player.player_id)
                
                # Notify other players
                await self._broadcast_to_game(
                    game.game_id,
                    create_message(
                        MessageType.PLAYER_LEFT,
                        player_id=player.player_id,
                        game_id=game.game_id,
                    ),
                    exclude=player.player_id,
                )
                
                # Clean up empty games
                if not game.players:
                    del self.games[game.game_id]
    
    async def _handle_ping(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle ping message."""
        await self._send(player.websocket, create_message(MessageType.PONG))
    
    async def _handle_host_game(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle game hosting."""
        game_id = str(uuid.uuid4())[:8]
        game = GameRoom(
            game_id=game_id,
            host_id=player.player_id,
            players=[player.player_id],
        )
        
        self.games[game_id] = game
        player.game_id = game_id
        player.name = msg.data.get("player_name", player.name)
        
        logger.info(f"Game created: {game_id} by {player.name}")
        
        await self._send(player.websocket, create_message(
            MessageType.HOST_GAME,
            game_id=game_id,
            success=True,
        ))
    
    async def _handle_join_game(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle joining a game."""
        game_id = msg.game_id or msg.data.get("game_id")
        game = self.games.get(game_id)
        
        if not game:
            await self._send(player.websocket, msg_error("Game not found"))
            return
        
        if len(game.players) >= 2:
            await self._send(player.websocket, msg_error("Game is full"))
            return
        
        if game.is_started:
            await self._send(player.websocket, msg_error("Game already started"))
            return
        
        player.game_id = game_id
        player.name = msg.data.get("player_name", player.name)
        game.players.append(player.player_id)
        
        logger.info(f"Player {player.name} joined game {game_id}")
        
        # Notify all players
        await self._broadcast_to_game(
            game_id,
            create_message(
                MessageType.PLAYER_JOINED,
                game_id=game_id,
                player_id=player.player_id,
                player_name=player.name,
            ),
        )
        
        # If 2 players, start the game
        if len(game.players) == 2:
            game.is_started = True
            await self._broadcast_to_game(
                game_id,
                create_message(
                    MessageType.GAME_START,
                    game_id=game_id,
                    players=game.players,
                ),
            )
    
    async def _handle_leave_game(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle leaving a game."""
        if not player.game_id:
            return
        
        game = self.games.get(player.game_id)
        if not game:
            return
        
        game.players.remove(player.player_id)
        
        await self._broadcast_to_game(
            game.game_id,
            create_message(
                MessageType.PLAYER_LEFT,
                player_id=player.player_id,
                game_id=game.game_id,
            ),
            exclude=player.player_id,
        )
        
        player.game_id = None
        
        # Clean up empty games
        if not game.players:
            del self.games[game.game_id]
    
    async def _handle_game_list(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle game list request."""
        available_games = [
            {
                "game_id": game.game_id,
                "host_name": self.players_by_id.get(game.host_id, ConnectedPlayer("", "Unknown", None)).name,
                "player_count": len(game.players),
                "is_started": game.is_started,
            }
            for game in self.games.values()
            if not game.is_started and len(game.players) < 2
        ]
        
        await self._send(player.websocket, create_message(
            MessageType.GAME_LIST,
            games=available_games,
        ))
    
    async def _handle_card_played(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle card played action."""
        if not player.game_id:
            return
        
        # Relay to other player
        await self._broadcast_to_game(
            player.game_id,
            create_message(
                MessageType.CARD_PLAYED,
                player_id=player.player_id,
                game_id=player.game_id,
                card_index=msg.data.get("card_index"),
                flip_to_minus=msg.data.get("flip_to_minus", False),
            ),
            exclude=player.player_id,
        )
    
    async def _handle_stand(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle stand action."""
        if not player.game_id:
            return
        
        await self._broadcast_to_game(
            player.game_id,
            create_message(
                MessageType.STAND,
                player_id=player.player_id,
                game_id=player.game_id,
            ),
            exclude=player.player_id,
        )
    
    async def _handle_end_turn(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle end turn action."""
        if not player.game_id:
            return
        
        await self._broadcast_to_game(
            player.game_id,
            create_message(
                MessageType.END_TURN,
                player_id=player.player_id,
                game_id=player.game_id,
            ),
            exclude=player.player_id,
        )
    
    async def _handle_chat(self, player: ConnectedPlayer, msg: GameMessage):
        """Handle chat message."""
        if not player.game_id:
            return
        
        await self._broadcast_to_game(
            player.game_id,
            create_message(
                MessageType.CHAT_MESSAGE,
                player_id=player.player_id,
                player_name=player.name,
                game_id=player.game_id,
                message=msg.data.get("message", ""),
            ),
        )
    
    async def _send(self, websocket: WebSocketServerProtocol, msg: GameMessage):
        """Send a message to a websocket."""
        try:
            await websocket.send(msg.to_json())
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def _broadcast_to_game(
        self,
        game_id: str,
        msg: GameMessage,
        exclude: str | None = None,
    ):
        """Broadcast a message to all players in a game."""
        game = self.games.get(game_id)
        if not game:
            return
        
        for player_id in game.players:
            if player_id == exclude:
                continue
            player = self.players_by_id.get(player_id)
            if player:
                await self._send(player.websocket, msg)
    
    async def start(self):
        """Start the server."""
        if not HAS_WEBSOCKETS:
            logger.error("websockets package not installed. Install with: pip install websockets")
            return
        
        logger.info(f"Starting Pazaak server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_connection, self.host, self.port):
            logger.info(f"Server running at ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever


def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="Pazaak Multiplayer Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    args = parser.parse_args()
    
    server = PazaakServer(host=args.host, port=args.port)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped")


if __name__ == "__main__":
    main()

