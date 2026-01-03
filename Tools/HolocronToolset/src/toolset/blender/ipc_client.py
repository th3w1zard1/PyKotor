"""IPC client for communicating with Blender.

This module implements a JSON-RPC 2.0 client over TCP socket for
bidirectional communication with the Blender IPC server.
"""

from __future__ import annotations

import json
import socket
import threading
import time

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from collections.abc import Sequence


class ConnectionState(Enum):
    """State of the IPC connection."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class IPCResponse:
    """Response from an IPC call."""

    success: bool
    result: Any = None
    error: str | None = None
    error_code: int | None = None


@dataclass
class IPCEvent:
    """Event received from Blender."""

    method: str
    params: dict[str, Any] = field(default_factory=dict)


class BlenderIPCClient:
    """JSON-RPC 2.0 client for Blender IPC communication.

    This client handles:
    - Connection management with automatic reconnection
    - Sending commands to Blender
    - Receiving events from Blender
    - Heartbeat/keepalive mechanism
    """

    DEFAULT_PORT = 7531
    BUFFER_SIZE = 65536
    CONNECT_TIMEOUT = 5.0
    READ_TIMEOUT = 1.0
    HEARTBEAT_INTERVAL = 5.0
    RECONNECT_DELAY = 2.0
    MAX_RECONNECT_ATTEMPTS = 5

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
        auto_reconnect: bool = True,
    ):
        """Initialize the IPC client.

        Args:
            host: Server host (default localhost)
            port: Server port (default 7531)
            auto_reconnect: Automatically reconnect on disconnection
        """
        self._host = host
        self._port = port
        self._auto_reconnect = auto_reconnect

        self._socket: socket.socket | None = None
        self._state = ConnectionState.DISCONNECTED
        self._request_id = 0
        self._lock = threading.Lock()

        # Event handling
        self._event_callbacks: dict[str, list[Callable[[IPCEvent], None]]] = {}
        self._state_callbacks: list[Callable[[ConnectionState], None]] = []

        # Background threads
        self._receiver_thread: threading.Thread | None = None
        self._heartbeat_thread: threading.Thread | None = None
        self._running = False

        # Pending requests (for async responses)
        self._pending_requests: dict[int, threading.Event] = {}
        self._responses: dict[int, IPCResponse] = {}

        self._logger = RobustLogger()

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected to Blender."""
        return self._state == ConnectionState.CONNECTED

    def connect(self, timeout: float = CONNECT_TIMEOUT) -> bool:
        """Connect to the Blender IPC server.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        if self._state == ConnectionState.CONNECTED:
            return True

        self._set_state(ConnectionState.CONNECTING)

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)
            self._socket.connect((self._host, self._port))
            self._socket.settimeout(self.READ_TIMEOUT)

            self._set_state(ConnectionState.CONNECTED)
            self._running = True

            # Start background threads
            self._receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receiver_thread.start()

            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

            self._logger.info(f"Connected to Blender IPC server at {self._host}:{self._port}")
            return True

        except (socket.error, OSError) as e:
            self._logger.warning(f"Failed to connect to Blender IPC: {e}")
            self._set_state(ConnectionState.ERROR)
            self._cleanup_socket()
            return False

    def disconnect(self):
        """Disconnect from the Blender IPC server."""
        self._running = False

        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

        self._set_state(ConnectionState.DISCONNECTED)
        self._logger.info("Disconnected from Blender IPC server")

    def send_command(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = 10.0,
    ) -> IPCResponse:
        """Send a command to Blender and wait for response.

        Args:
            method: RPC method name
            params: Method parameters
            timeout: Response timeout in seconds

        Returns:
            IPCResponse with result or error
        """
        if not self.is_connected:
            return IPCResponse(success=False, error="Not connected to Blender")

        with self._lock:
            self._request_id += 1
            request_id = self._request_id

        # Build JSON-RPC 2.0 request
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id,
        }
        if params:
            request["params"] = params

        # Setup response event
        response_event = threading.Event()
        self._pending_requests[request_id] = response_event

        try:
            # Send request
            if self._socket is None:
                return IPCResponse(success=False, error="Socket not connected")
            data = json.dumps(request) + "\n"
            self._socket.sendall(data.encode("utf-8"))

            # Wait for response
            if response_event.wait(timeout):
                response = self._responses.pop(request_id, None)
                if response:
                    return response
                return IPCResponse(success=False, error="No response received")
            else:
                return IPCResponse(success=False, error=f"Request timed out after {timeout}s")

        except (socket.error, OSError) as e:
            self._logger.error(f"Error sending command: {e}")
            self._handle_disconnection()
            return IPCResponse(success=False, error=str(e))

        finally:
            self._pending_requests.pop(request_id, None)

    def send_notification(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> bool:
        """Send a notification (no response expected).

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            True if sent successfully
        """
        if not self.is_connected:
            return False

        # Build JSON-RPC 2.0 notification (no id)
        notification: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params

        try:
            if self._socket is None:
                return False
            data = json.dumps(notification) + "\n"
            self._socket.sendall(data.encode("utf-8"))
            return True
        except (socket.error, OSError) as e:
            self._logger.error(f"Error sending notification: {e}")
            self._handle_disconnection()
            return False

    def on_event(self, event_name: str, callback: Callable[[IPCEvent], None]):
        """Register a callback for an event type.

        Args:
            event_name: Event name to listen for
            callback: Function to call when event is received
        """
        if event_name not in self._event_callbacks:
            self._event_callbacks[event_name] = []
        self._event_callbacks[event_name].append(callback)

    def off_event(self, event_name: str, callback: Callable[[IPCEvent], None]):
        """Unregister an event callback.

        Args:
            event_name: Event name
            callback: Callback to remove
        """
        if event_name in self._event_callbacks:
            try:
                self._event_callbacks[event_name].remove(callback)
            except ValueError:
                pass

    def on_state_change(self, callback: Callable[[ConnectionState], None]):
        """Register a callback for connection state changes.

        Args:
            callback: Function to call when state changes
        """
        self._state_callbacks.append(callback)

    def _set_state(self, state: ConnectionState):
        """Update connection state and notify callbacks."""
        if self._state != state:
            self._state = state
            for callback in self._state_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    self._logger.error(f"Error in state callback: {e}")

    def _receive_loop(self):
        """Background thread for receiving messages."""
        buffer = ""

        while self._running and self._socket:
            try:
                data = self._socket.recv(self.BUFFER_SIZE)
                if not data:
                    self._handle_disconnection()
                    break

                buffer += data.decode("utf-8")

                # Process complete messages (newline-delimited)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self._process_message(line)

            except socket.timeout:
                continue
            except (socket.error, OSError) as e:
                if self._running:
                    self._logger.error(f"Receive error: {e}")
                    self._handle_disconnection()
                break

    def _process_message(self, message: str):
        """Process a received JSON-RPC message."""
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            self._logger.warning(f"Invalid JSON received: {e}")
            return

        # Check if it's a response or notification
        if "id" in data and data["id"] is not None:
            # It's a response to a request
            request_id = data["id"]
            if request_id in self._pending_requests:
                if "error" in data:
                    error = data["error"]
                    response = IPCResponse(
                        success=False,
                        error=error.get("message", str(error)),
                        error_code=error.get("code"),
                    )
                else:
                    response = IPCResponse(
                        success=True,
                        result=data.get("result"),
                    )
                self._responses[request_id] = response
                self._pending_requests[request_id].set()
        else:
            # It's a notification/event from Blender
            method = data.get("method", "")
            params = data.get("params", {})
            event = IPCEvent(method=method, params=params)
            self._dispatch_event(event)

    def _dispatch_event(self, event: IPCEvent):
        """Dispatch an event to registered callbacks."""
        callbacks = self._event_callbacks.get(event.method, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Error in event callback for {event.method}: {e}")

        # Also dispatch to wildcard listeners
        for callback in self._event_callbacks.get("*", []):
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Error in wildcard event callback: {e}")

    def _heartbeat_loop(self):
        """Background thread for sending keepalive pings."""
        while self._running:
            time.sleep(self.HEARTBEAT_INTERVAL)
            if self._running and self.is_connected:
                response = self.send_command("ping", timeout=5.0)
                if not response.success:
                    self._logger.warning("Heartbeat failed")

    def _handle_disconnection(self):
        """Handle unexpected disconnection."""
        self._cleanup_socket()
        self._set_state(ConnectionState.DISCONNECTED)

        if self._auto_reconnect and self._running:
            self._attempt_reconnect()

    def _attempt_reconnect(self):
        """Attempt to reconnect to the server."""
        for attempt in range(self.MAX_RECONNECT_ATTEMPTS):
            if not self._running:
                break

            self._logger.info(f"Reconnection attempt {attempt + 1}/{self.MAX_RECONNECT_ATTEMPTS}")
            time.sleep(self.RECONNECT_DELAY)

            if self.connect():
                return

        self._logger.error("Failed to reconnect after maximum attempts")
        self._set_state(ConnectionState.ERROR)

    def _cleanup_socket(self):
        """Clean up socket resources."""
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None


# Convenience functions for common commands
class BlenderCommands:
    """High-level command wrappers for Blender operations."""

    def __init__(self, client: BlenderIPCClient):
        self._client = client

    def ping(self) -> bool:
        """Check if Blender is responsive."""
        response = self._client.send_command("ping")
        return response.success

    def get_version(self) -> str | None:
        """Get kotorblender version."""
        response = self._client.send_command("get_version")
        if response.success:
            return response.result
        return None

    def load_module(
        self,
        lyt_data: dict,
        git_data: dict,
        installation_path: str,
        module_root: str,
    ) -> bool:
        """Load a module into Blender.

        Args:
            lyt_data: Serialized LYT data
            git_data: Serialized GIT data
            installation_path: Path to KotOR installation
            module_root: Module root name (e.g., "tar_m02aa")

        Returns:
            True if loaded successfully
        """
        response = self._client.send_command(
            "load_module",
            {
                "lyt": lyt_data,
                "git": git_data,
                "installation_path": installation_path,
                "module_root": module_root,
            },
        )
        return response.success

    def unload_module(self) -> bool:
        """Unload the current module."""
        response = self._client.send_command("unload_module")
        return response.success

    def add_instance(self, instance_data: dict) -> str | None:
        """Add a GIT instance to the scene.

        Args:
            instance_data: Serialized GITInstance data

        Returns:
            Blender object name if successful, None otherwise
        """
        response = self._client.send_command("add_instance", {"instance": instance_data})
        if response.success:
            return response.result
        return None

    def remove_instance(self, object_name: str) -> bool:
        """Remove a GIT instance from the scene.

        Args:
            object_name: Blender object name

        Returns:
            True if removed successfully
        """
        response = self._client.send_command("remove_instance", {"name": object_name})
        return response.success

    def update_instance(self, object_name: str, properties: dict) -> bool:
        """Update instance properties.

        Args:
            object_name: Blender object name
            properties: Properties to update (position, rotation, etc.)

        Returns:
            True if updated successfully
        """
        response = self._client.send_command(
            "update_instance",
            {"name": object_name, "properties": properties},
        )
        return response.success

    def select_instances(self, object_names: Sequence[str]) -> bool:
        """Select instances in Blender.

        Args:
            object_names: List of Blender object names to select

        Returns:
            True if selection changed successfully
        """
        response = self._client.send_command("select_instances", {"names": list(object_names)})
        return response.success

    def get_selection(self) -> list[str]:
        """Get currently selected objects.

        Returns:
            List of selected object names
        """
        response = self._client.send_command("get_selection")
        if response.success and isinstance(response.result, list):
            return response.result
        return []

    def add_room(self, room_data: dict) -> str | None:
        """Add a room to the layout.

        Args:
            room_data: Serialized LYTRoom data

        Returns:
            Blender object name if successful
        """
        response = self._client.send_command("add_room", {"room": room_data})
        if response.success:
            return response.result
        return None

    def update_room(self, object_name: str, properties: dict) -> bool:
        """Update room properties.

        Args:
            object_name: Blender object name
            properties: Properties to update

        Returns:
            True if updated successfully
        """
        response = self._client.send_command(
            "update_room",
            {"name": object_name, "properties": properties},
        )
        return response.success

    def save_changes(self) -> dict | None:
        """Export modified data from Blender.

        Returns:
            Dictionary with modified LYT and GIT data
        """
        response = self._client.send_command("save_changes", timeout=30.0)
        if response.success:
            return response.result
        return None

    def undo(self) -> bool:
        """Trigger undo in Blender.

        Returns:
            True if undo was successful
        """
        response = self._client.send_command("undo")
        return response.success

    def redo(self) -> bool:
        """Trigger redo in Blender.

        Returns:
            True if redo was successful
        """
        response = self._client.send_command("redo")
        return response.success

    def set_visibility(self, instance_type: str, visible: bool) -> bool:
        """Set visibility of an instance type.

        Args:
            instance_type: Type name (creature, placeable, door, etc.)
            visible: Whether instances should be visible

        Returns:
            True if updated successfully
        """
        response = self._client.send_command(
            "set_visibility",
            {"instance_type": instance_type, "visible": visible},
        )
        return response.success

    def set_render_settings(
        self,
        backface_culling: bool | None = None,
        use_lightmap: bool | None = None,
        show_cursor: bool | None = None,
    ) -> bool:
        """Update render settings.

        Args:
            backface_culling: Enable/disable backface culling
            use_lightmap: Enable/disable lightmap usage
            show_cursor: Show/hide cursor

        Returns:
            True if updated successfully
        """
        params: dict[str, Any] = {}
        if backface_culling is not None:
            params["backface_culling"] = backface_culling
        if use_lightmap is not None:
            params["use_lightmap"] = use_lightmap
        if show_cursor is not None:
            params["show_cursor"] = show_cursor

        if not params:
            return True

        response = self._client.send_command("set_render_settings", params)
        return response.success

    def set_camera_view(
        self,
        x: float,
        y: float,
        z: float,
        yaw: float | None = None,
        pitch: float | None = None,
        distance: float | None = None,
    ) -> bool:
        """Set viewport camera position and orientation.

        Args:
            x, y, z: Camera position
            yaw: Camera yaw angle (radians)
            pitch: Camera pitch angle (radians)
            distance: Camera distance (for orbit mode)

        Returns:
            True if updated successfully
        """
        params: dict[str, Any] = {"position": {"x": x, "y": y, "z": z}}
        if yaw is not None:
            params["yaw"] = yaw
        if pitch is not None:
            params["pitch"] = pitch
        if distance is not None:
            params["distance"] = distance

        response = self._client.send_command("set_camera_view", params)
        return response.success

    def add_door_hook(self, door_hook_data: dict) -> str | None:
        """Add a door hook to the layout.

        Args:
            door_hook_data: Serialized LYTDoorHook data

        Returns:
            Blender object name if successful
        """
        response = self._client.send_command("add_door_hook", {"door_hook": door_hook_data})
        if response.success:
            return response.result
        return None

    def add_track(self, track_data: dict) -> str | None:
        """Add a track to the layout.

        Args:
            track_data: Serialized LYTTrack data

        Returns:
            Blender object name if successful
        """
        response = self._client.send_command("add_track", {"track": track_data})
        if response.success:
            return response.result
        return None

    def add_obstacle(self, obstacle_data: dict) -> str | None:
        """Add an obstacle to the layout.

        Args:
            obstacle_data: Serialized LYTObstacle data

        Returns:
            Blender object name if successful
        """
        response = self._client.send_command("add_obstacle", {"obstacle": obstacle_data})
        if response.success:
            return response.result
        return None

    def update_door_hook(self, object_name: str, properties: dict) -> bool:
        """Update door hook properties.

        Args:
            object_name: Blender object name
            properties: Properties to update

        Returns:
            True if updated successfully
        """
        response = self._client.send_command(
            "update_door_hook",
            {"name": object_name, "properties": properties},
        )
        return response.success

    def update_track(self, object_name: str, properties: dict) -> bool:
        """Update track properties.

        Args:
            object_name: Blender object name
            properties: Properties to update

        Returns:
            True if updated successfully
        """
        response = self._client.send_command(
            "update_track",
            {"name": object_name, "properties": properties},
        )
        return response.success

    def update_obstacle(self, object_name: str, properties: dict) -> bool:
        """Update obstacle properties.

        Args:
            object_name: Blender object name
            properties: Properties to update

        Returns:
            True if updated successfully
        """
        response = self._client.send_command(
            "update_obstacle",
            {"name": object_name, "properties": properties},
        )
        return response.success

    def remove_lyt_element(self, object_name: str, element_type: str) -> bool:
        """Remove a LYT element from the scene.

        Args:
            object_name: Blender object name
            element_type: Type of element (room, door_hook, track, obstacle)

        Returns:
            True if removed successfully
        """
        response = self._client.send_command(
            "remove_lyt_element",
            {"name": object_name, "element_type": element_type},
        )
        return response.success


# Global client instance
_global_client: BlenderIPCClient | None = None


def get_ipc_client() -> BlenderIPCClient:
    """Get or create the global IPC client instance."""
    global _global_client
    if _global_client is None:
        _global_client = BlenderIPCClient()
    return _global_client


def get_blender_commands() -> BlenderCommands:
    """Get BlenderCommands wrapper for the global client."""
    return BlenderCommands(get_ipc_client())

