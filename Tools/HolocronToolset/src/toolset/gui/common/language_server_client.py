"""NSS Language Server Client.

A client for communicating with the NSS Language Server subprocess.
Handles process management, message passing, and result caching.

This client is designed to be non-blocking and safe to use from the UI thread.
Analysis requests are sent asynchronously and results are retrieved via callbacks
or by polling.

Usage:
    client = LanguageServerClient(is_tsl=False)
    client.start()
    
    # Request analysis (non-blocking)
    request_id = client.request_analysis(text, filepath)
    
    # Check for results (non-blocking)
    result = client.get_result(request_id)
    if result is not None:
        process_result(result)
    
    # Or use callback
    client.request_analysis(text, filepath, callback=process_result)
    
    # Shutdown when done
    client.stop()
"""
from __future__ import annotations

import multiprocessing
import threading
import time

from dataclasses import dataclass
from queue import Empty
from typing import TYPE_CHECKING, Any, Callable

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from pathlib import Path

    from pykotor.common.script import ScriptConstant, ScriptFunction


@dataclass
class AnalysisResult:
    """Result of a document analysis."""
    diagnostics: list[dict[str, Any]]
    symbols: list[dict[str, Any]]
    parse_successful: bool
    request_id: int
    timestamp: float


@dataclass
class PendingRequest:
    """A pending request waiting for a response."""
    request_id: int
    method: str
    callback: Callable[[Any], None] | None
    timestamp: float


class LanguageServerClient:
    """Client for the NSS Language Server.
    
    Manages the language server subprocess and handles communication.
    All public methods are thread-safe and non-blocking.
    """
    
    def __init__(
        self,
        is_tsl: bool = False,
        functions: list[ScriptFunction] | None = None,
        constants: list[ScriptConstant] | None = None,
        library: dict[str, bytes] | None = None,
    ):
        """Initialize the language server client.
        
        Args:
            is_tsl: Whether this is for TSL (K2) or K1
            functions: Built-in script functions (loaded automatically if None)
            constants: Built-in script constants (loaded automatically if None)
            library: Script library (loaded automatically if None)
        """
        self.is_tsl = is_tsl
        self.functions = functions
        self.constants = constants
        self.library = library
        
        self._process: multiprocessing.Process | None = None
        self._request_queue: multiprocessing.Queue | None = None
        self._response_queue: multiprocessing.Queue | None = None
        
        self._next_request_id = 1
        self._pending_requests: dict[int, PendingRequest] = {}
        self._results: dict[int, Any] = {}
        self._lock = threading.Lock()
        
        self._response_thread: threading.Thread | None = None
        self._running = False
        
        # Cache for avoiding redundant analysis
        self._last_analysis_text: str = ""
        self._last_analysis_result: AnalysisResult | None = None
        self._last_analysis_time: float = 0.0
    
    @property
    def is_running(self) -> bool:
        """Check if the language server is running."""
        return self._running and self._process is not None and self._process.is_alive()
    
    def start(self, timeout: float = 10.0) -> bool:
        """Start the language server subprocess.
        
        Args:
            timeout: Maximum time to wait for server to become ready
            
        Returns:
            True if server started successfully, False otherwise
        """
        if self.is_running:
            return True
        
        try:
            # Create queues
            self._request_queue = multiprocessing.Queue()
            self._response_queue = multiprocessing.Queue()
            
            # Start server process
            from pykotor.resource.formats.ncs.compiler.language_server import NSSLanguageServer
            
            self._process = multiprocessing.Process(
                target=NSSLanguageServer.run_server,
                args=(
                    self._request_queue,
                    self._response_queue,
                    self.is_tsl,
                    self.functions,
                    self.constants,
                    self.library,
                ),
                daemon=True,
            )
            self._process.start()
            
            # Wait for ready signal
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = self._response_queue.get(timeout=0.5)
                    if response.get('result', {}).get('status') == 'ready':
                        self._running = True
                        
                        # Start response handler thread
                        self._response_thread = threading.Thread(
                            target=self._handle_responses,
                            daemon=True,
                        )
                        self._response_thread.start()
                        
                        RobustLogger().debug("Language server started successfully")
                        return True
                except Empty:
                    if not self._process.is_alive():
                        RobustLogger().error("Language server process died during startup")
                        return False
            
            RobustLogger().error("Language server startup timed out")
            self.stop()
            return False
            
        except Exception as e:
            RobustLogger().error(f"Failed to start language server: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop the language server subprocess."""
        self._running = False
        
        # Send shutdown request
        if self._request_queue is not None:
            try:
                self._request_queue.put({'id': -1, 'method': 'shutdown', 'params': {}})
            except Exception:
                pass
            
            # Also send None to signal thread to stop
            try:
                self._request_queue.put(None)
            except Exception:
                pass
        
        # Wait for response thread
        if self._response_thread is not None and self._response_thread.is_alive():
            self._response_thread.join(timeout=2.0)
        
        # Terminate process
        if self._process is not None:
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=2.0)
                if self._process.is_alive():
                    self._process.kill()
            self._process = None
        
        # Clean up queues
        self._request_queue = None
        self._response_queue = None
        
        # Clear pending requests
        with self._lock:
            self._pending_requests.clear()
            self._results.clear()
    
    def _handle_responses(self):
        """Background thread to handle responses from the server."""
        while self._running:
            try:
                if self._response_queue is None:
                    break
                    
                response = self._response_queue.get(timeout=0.1)
                if response is None:
                    break
                
                request_id = response.get('id')
                
                with self._lock:
                    # Check if there's a pending request
                    pending = self._pending_requests.pop(request_id, None)
                    
                    if pending is not None:
                        # Store result
                        if response.get('error'):
                            self._results[request_id] = {'error': response['error']}
                        else:
                            self._results[request_id] = response.get('result')
                        
                        # Call callback if provided
                        if pending.callback is not None:
                            try:
                                pending.callback(self._results[request_id])
                            except Exception as e:
                                RobustLogger().error(f"Callback error: {e}")
                    else:
                        # Unsolicited response (e.g., ready signal)
                        pass
                        
            except Empty:
                continue
            except Exception as e:
                if self._running:
                    RobustLogger().error(f"Response handler error: {e}")
                break
    
    def _send_request(
        self,
        method: str,
        params: dict[str, Any],
        callback: Callable[[Any], None] | None = None,
    ) -> int:
        """Send a request to the server.
        
        Args:
            method: Method name
            params: Method parameters
            callback: Optional callback for the result
            
        Returns:
            Request ID
        """
        if not self.is_running:
            # Try to start server
            if not self.start():
                return -1
        
        with self._lock:
            request_id = self._next_request_id
            self._next_request_id += 1
            
            # Track pending request
            self._pending_requests[request_id] = PendingRequest(
                request_id=request_id,
                method=method,
                callback=callback,
                timestamp=time.time(),
            )
        
        # Send request
        request = {
            'id': request_id,
            'method': method,
            'params': params,
        }
        
        try:
            assert self._request_queue is not None
            self._request_queue.put(request)
        except Exception as e:
            RobustLogger().error(f"Failed to send request: {e}")
            with self._lock:
                self._pending_requests.pop(request_id, None)
            return -1
        
        return request_id
    
    def request_analysis(
        self,
        text: str,
        filepath: str | Path | None = None,
        callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> int:
        """Request document analysis.
        
        Args:
            text: Document text to analyze
            filepath: Optional file path for context
            callback: Optional callback for the result
            
        Returns:
            Request ID (or -1 on failure)
        """
        # Check cache first
        if text == self._last_analysis_text and self._last_analysis_result is not None:
            # Return cached result immediately
            if callback is not None:
                callback({
                    'diagnostics': self._last_analysis_result.diagnostics,
                    'symbols': self._last_analysis_result.symbols,
                    'parse_successful': self._last_analysis_result.parse_successful,
                })
            return self._last_analysis_result.request_id
        
        return self._send_request(
            method='analyze',
            params={
                'text': text,
                'filepath': str(filepath) if filepath else None,
            },
            callback=self._wrap_analysis_callback(text, callback),
        )
    
    def _wrap_analysis_callback(
        self,
        text: str,
        original_callback: Callable[[dict[str, Any]], None] | None,
    ) -> Callable[[dict[str, Any]], None]:
        """Wrap callback to update cache."""
        def wrapped(result: dict[str, Any]):
            # Update cache
            if isinstance(result, dict) and 'diagnostics' in result:
                self._last_analysis_text = text
                self._last_analysis_result = AnalysisResult(
                    diagnostics=result.get('diagnostics', []),
                    symbols=result.get('symbols', []),
                    parse_successful=result.get('parse_successful', False),
                    request_id=0,  # Will be updated
                    timestamp=time.time(),
                )
            
            # Call original callback
            if original_callback is not None:
                original_callback(result)
        
        return wrapped
    
    def request_completions(
        self,
        text: str,
        line: int,
        character: int,
        callback: Callable[[list[dict[str, Any]]], None] | None = None,
    ) -> int:
        """Request completion suggestions.
        
        Args:
            text: Document text
            line: 0-indexed line number
            character: 0-indexed character position
            callback: Optional callback for the result
            
        Returns:
            Request ID (or -1 on failure)
        """
        return self._send_request(
            method='completions',
            params={
                'text': text,
                'line': line,
                'character': character,
            },
            callback=callback,
        )
    
    def request_hover(
        self,
        text: str,
        line: int,
        character: int,
        callback: Callable[[dict[str, Any] | None], None] | None = None,
    ) -> int:
        """Request hover information.
        
        Args:
            text: Document text
            line: 0-indexed line number
            character: 0-indexed character position
            callback: Optional callback for the result
            
        Returns:
            Request ID (or -1 on failure)
        """
        return self._send_request(
            method='hover',
            params={
                'text': text,
                'line': line,
                'character': character,
            },
            callback=callback,
        )
    
    def get_result(self, request_id: int) -> Any | None:
        """Get the result of a request if available.
        
        This is a non-blocking method that returns immediately.
        
        Args:
            request_id: The request ID returned by a request method
            
        Returns:
            The result if available, None if still pending
        """
        with self._lock:
            return self._results.pop(request_id, None)
    
    def wait_for_result(self, request_id: int, timeout: float = 5.0) -> Any | None:
        """Wait for a result with timeout.
        
        This blocks until the result is available or timeout is reached.
        
        Args:
            request_id: The request ID
            timeout: Maximum time to wait
            
        Returns:
            The result or None if timed out
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.get_result(request_id)
            if result is not None:
                return result
            time.sleep(0.01)  # 10ms polling
        return None
    
    def update_config(
        self,
        is_tsl: bool | None = None,
        functions: list[ScriptFunction] | None = None,
        constants: list[ScriptConstant] | None = None,
        library: dict[str, bytes] | None = None,
    ):
        """Update server configuration.
        
        Args:
            is_tsl: Whether this is for TSL (K2) or K1
            functions: Built-in script functions
            constants: Built-in script constants
            library: Script library
        """
        # Update local config
        if is_tsl is not None:
            self.is_tsl = is_tsl
        if functions is not None:
            self.functions = functions
        if constants is not None:
            self.constants = constants
        if library is not None:
            self.library = library
        
        # Clear cache
        self._last_analysis_text = ""
        self._last_analysis_result = None
        
        # Send update to server if running
        if self.is_running:
            params: dict[str, Any] = {}
            if is_tsl is not None:
                params['is_tsl'] = is_tsl
            # Note: We don't send functions/constants/library because they're large
            # and the server should reload them based on is_tsl
            
            if params:
                self._send_request('update_config', params)
    
    def invalidate_cache(self):
        """Invalidate the analysis cache."""
        self._last_analysis_text = ""
        self._last_analysis_result = None
    
    def cleanup_old_requests(self, max_age: float = 30.0):
        """Clean up old pending requests that may have been lost.
        
        Args:
            max_age: Maximum age in seconds for pending requests
        """
        current_time = time.time()
        with self._lock:
            expired = [
                rid for rid, req in self._pending_requests.items()
                if current_time - req.timestamp > max_age
            ]
            for rid in expired:
                self._pending_requests.pop(rid, None)

