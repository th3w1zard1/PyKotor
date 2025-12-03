from __future__ import annotations

import os
import subprocess
import sys
import textwrap

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from loggerplus import RobustLogger

from utility.system.os_helper import is_frozen, requires_admin

if TYPE_CHECKING:
    from logging import Logger


class UpdateStrategy(Enum):  # pragma: no cover
    """Enum representing the update strategies available."""

    OVERWRITE = "overwrite"  # Overwrites the binary in place
    RENAME = "rename"  # Renames the binary.  Only available for Windows single file bundled executables


class RestartStrategy(Enum):
    DEFAULT = "default"
    BATCH = "batch"
    JOIN = "join"


class Restarter:
    """Handles restarting and updating applications across Windows, macOS, and Linux.
    
    This class implements industry-standard update patterns:
    - On Windows: Uses a detached PowerShell 2.0 script that waits for the old process
      to exit before copying files and launching the new version
    - On macOS/Linux: Uses os.execl for in-place process replacement, or a detached
      shell script for overwrite operations
    """

    def __init__(
        self,
        current_app: os.PathLike | str,
        updated_app: os.PathLike | str,
        *,
        filename: str | None = None,
        update_strategy: UpdateStrategy = UpdateStrategy.RENAME,
        restart_strategy: RestartStrategy = RestartStrategy.DEFAULT,
        exithook: Callable | None = None,
        logger: Logger | None = None,
    ):
        self.log = logger or RobustLogger()
        self.current_app: Path = Path(current_app)
        self.log.debug("Current App: %s resolved to %s", current_app, self.current_app)
        if is_frozen() and not self.current_app.exists():
            raise ValueError(f"Bad path to current_app provided to Restarter: '{self.current_app}'")

        self.filename: str = self.current_app.name if filename is None else filename
        self.u_strategy: UpdateStrategy = update_strategy
        self.r_strategy: RestartStrategy = restart_strategy
        self.exithook = exithook
        self.updated_app: Path = Path(updated_app)
        self.log.debug("Update path: %s", self.updated_app)
        if not self.updated_app.exists():
            self.updated_app = self.updated_app.joinpath(self.updated_app.name)
        if not self.updated_app.exists():
            raise FileNotFoundError(f"Updated app not found at: {self.updated_app}")

    def process(self):
        """Main entry point for the restart/update process."""
        self.log.info("Restarter.process() called")
        if os.name == "nt":
            if self.current_app == self.updated_app:
                self.log.info(
                    "Current app and updated app path are exactly the same, "
                    "performing simple restart. path: %s",
                    self.current_app,
                )
                self._win_simple_restart()
            elif self.u_strategy == UpdateStrategy.OVERWRITE:
                self._win_overwrite()
            else:
                self._win_rename_restart()
        else:
            # macOS and Linux
            if self.u_strategy == UpdateStrategy.OVERWRITE:
                self._unix_overwrite()
            else:
                self._unix_join()

    def _win_simple_restart(self):
        """Simple restart without file operations - just launch the app and exit."""
        self.log.debug("Starting simple restart for app at '%s'...", self.current_app)
        self._launch_detached_process_windows(self.current_app)
        self._exit_application()

    def _win_rename_restart(self):
        """Windows restart using the rename strategy (for single-file executables)."""
        self.log.debug("Starting rename-restart for app at '%s'...", self.current_app)
        self._launch_detached_process_windows(self.current_app)
        self._exit_application()

    def _win_overwrite(self):
        """Windows overwrite strategy using a detached PowerShell 2.0 script.
        
        This creates a PowerShell script that:
        1. Waits for the current process to fully exit (by PID)
        2. Copies/moves files with retry logic for locked files
        3. Launches the new application
        4. Cleans up the temporary script
        """
        self.log.info("Calling _win_overwrite for updated app '%s'", self.updated_app)
        
        is_folder = self.updated_app.is_dir()
        if is_folder:
            needs_admin = requires_admin(self.updated_app) or requires_admin(self.current_app.parent)
        else:
            needs_admin = requires_admin(self.current_app.parent)
        
        self.log.debug("Admin required to update: %s", needs_admin)
        
        # Create the PowerShell update script
        script_content = self._create_windows_update_script(
            source_path=self.updated_app,
            dest_path=self.current_app if not is_folder else self.current_app.parent,
            is_folder=is_folder,
            current_pid=os.getpid(),
            launch_app=self.current_app,
        )
        
        # Write script to a temporary file that persists after we exit
        # Using a fixed location in temp so it survives our process exit
        import tempfile
        script_dir = Path(tempfile.gettempdir()) / "holotoolset_update"
        script_dir.mkdir(parents=True, exist_ok=True)
        script_path = script_dir / f"update_{os.getpid()}.ps1"
        
        self.log.debug("Writing update script to: %s", script_path)
        script_path.write_text(script_content, encoding="utf-8")
        
        # Launch the PowerShell script as a fully detached process
        self._launch_powershell_script_detached(script_path, needs_admin)
        
        # Exit the application to release file locks
        self._exit_application()

    def _create_windows_update_script(
        self,
        source_path: Path,
        dest_path: Path,
        is_folder: bool,
        current_pid: int,
        launch_app: Path,
    ) -> str:
        """Create a PowerShell 2.0 compatible update script.
        
        This script:
        1. Waits for the parent process to exit
        2. Copies files with retry logic
        3. Launches the new application
        4. Cleans up itself
        """
        # Escape paths for PowerShell (handle special characters)
        source_escaped = str(source_path).replace("'", "''")
        dest_escaped = str(dest_path).replace("'", "''")
        launch_escaped = str(launch_app).replace("'", "''")
        
        # PowerShell 2.0 compatible script
        # Note: Using older syntax for PS 2.0 compatibility:
        # - No -NoNewWindow (use -WindowStyle Hidden)
        # - No advanced parameter attributes
        # - Using Write-Host instead of Write-Output for immediate display
        script = textwrap.dedent(f"""\
            # PowerShell 2.0 compatible update script
            # Auto-generated by Holocron Toolset updater
            
            $ErrorActionPreference = 'Stop'
            $parentPid = {current_pid}
            $sourcePath = '{source_escaped}'
            $destPath = '{dest_escaped}'
            $launchApp = '{launch_escaped}'
            $isFolder = ${str(is_folder).lower()}
            $maxRetries = 30
            $retryDelaySeconds = 1
            $scriptPath = $MyInvocation.MyCommand.Path
            
            # Function to write log messages
            function Write-Log {{
                param([string]$Message)
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                Write-Host "[$timestamp] $Message"
            }}
            
            # Wait for the parent process to exit
            Write-Log "Waiting for process $parentPid to exit..."
            $waitCount = 0
            $maxWait = 60  # Maximum 60 seconds to wait
            
            while ($waitCount -lt $maxWait) {{
                $proc = $null
                try {{
                    $proc = Get-Process -Id $parentPid -ErrorAction SilentlyContinue
                }} catch {{
                    # Process not found, which is what we want
                    $proc = $null
                }}
                
                if ($proc -eq $null) {{
                    Write-Log "Process $parentPid has exited."
                    break
                }}
                
                $waitCount++
                Start-Sleep -Seconds 1
            }}
            
            if ($waitCount -ge $maxWait) {{
                Write-Log "WARNING: Timeout waiting for process $parentPid. Proceeding anyway..."
            }}
            
            # Additional delay to ensure file handles are released
            Write-Log "Waiting for file handles to be released..."
            Start-Sleep -Seconds 2
            
            # Copy/Move files with retry logic
            Write-Log "Starting file copy operation..."
            $success = $false
            $retryCount = 0
            
            while ((-not $success) -and ($retryCount -lt $maxRetries)) {{
                try {{
                    if ($isFolder) {{
                        # For folder updates, copy contents recursively
                        Write-Log "Copying folder contents from '$sourcePath' to '$destPath'..."
                        
                        # Remove old files first (with retry)
                        if (Test-Path $destPath) {{
                            # Use robocopy for reliable folder sync on Windows
                            $robocopyPath = Join-Path $env:SystemRoot "System32\\robocopy.exe"
                            if (Test-Path $robocopyPath) {{
                                Write-Log "Using robocopy for folder update..."
                                $robocopyArgs = @(
                                    $sourcePath,
                                    $destPath,
                                    "/E",      # Copy subdirectories including empty ones
                                    "/MOVE",   # Move files (delete from source)
                                    "/PURGE",  # Delete dest files that no longer exist in source
                                    "/R:3",    # Retry 3 times
                                    "/W:1",    # Wait 1 second between retries
                                    "/NFL",    # No file list
                                    "/NDL",    # No directory list
                                    "/NJH",    # No job header
                                    "/NJS"     # No job summary
                                )
                                $robocopyResult = & $robocopyPath $robocopyArgs
                                # Robocopy returns various exit codes, 0-7 are success
                                if ($LASTEXITCODE -le 7) {{
                                    $success = $true
                                    Write-Log "Robocopy completed successfully."
                                }} else {{
                                    throw "Robocopy failed with exit code $LASTEXITCODE"
                                }}
                            }} else {{
                                # Fallback to PowerShell copy
                                Write-Log "Robocopy not found, using PowerShell copy..."
                                Copy-Item -Path "$sourcePath\\*" -Destination $destPath -Recurse -Force
                                $success = $true
                            }}
                        }} else {{
                            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
                            $success = $true
                        }}
                    }} else {{
                        # For single file updates
                        Write-Log "Copying file from '$sourcePath' to '$destPath'..."
                        Copy-Item -Path $sourcePath -Destination $destPath -Force
                        $success = $true
                    }}
                    
                    Write-Log "File copy completed successfully."
                }} catch {{
                    $retryCount++
                    Write-Log "Copy attempt $retryCount failed: $($_.Exception.Message)"
                    
                    if ($retryCount -lt $maxRetries) {{
                        Write-Log "Retrying in $retryDelaySeconds second(s)..."
                        Start-Sleep -Seconds $retryDelaySeconds
                    }}
                }}
            }}
            
            if (-not $success) {{
                Write-Log "ERROR: Failed to copy files after $maxRetries attempts."
                Write-Log "Press any key to exit..."
                $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null
                exit 1
            }}
            
            # Launch the updated application
            Write-Log "Launching updated application: $launchApp"
            try {{
                Start-Process -FilePath $launchApp -WindowStyle Normal
                Write-Log "Application launched successfully."
            }} catch {{
                Write-Log "ERROR: Failed to launch application: $($_.Exception.Message)"
            }}
            
            # Clean up source folder if it still exists and is different from dest
            if ($isFolder -and (Test-Path $sourcePath) -and ($sourcePath -ne $destPath)) {{
                try {{
                    Write-Log "Cleaning up source folder..."
                    Remove-Item -Path $sourcePath -Recurse -Force -ErrorAction SilentlyContinue
                }} catch {{
                    Write-Log "Warning: Could not clean up source folder: $($_.Exception.Message)"
                }}
            }}
            
            # Self-delete the script
            Write-Log "Update complete. Cleaning up..."
            Start-Sleep -Seconds 1
            
            if ($scriptPath -ne $null -and (Test-Path $scriptPath)) {{
                try {{
                    Remove-Item -Path $scriptPath -Force -ErrorAction SilentlyContinue
                }} catch {{
                    # Ignore cleanup errors
                }}
            }}
            
            exit 0
        """)
        
        return script

    def _launch_powershell_script_detached(self, script_path: Path, needs_admin: bool):
        """Launch a PowerShell script as a fully detached process.
        
        Uses PowerShell 2.0 compatible syntax and proper process detachment
        so the script continues running after the parent exits.
        """
        self.log.info("Launching PowerShell update script: %s (admin=%s)", script_path, needs_admin)
        
        # Build the PowerShell command
        # Using -ExecutionPolicy Bypass to ensure script runs
        # Using -WindowStyle Hidden to hide the console window
        ps_args = [
            "PowerShell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden",
            "-File", str(script_path),
        ]
        
        if needs_admin:
            # For admin, we need to use Start-Process with -Verb RunAs
            # This will show a UAC prompt
            inner_command = (
                f"Start-Process PowerShell.exe "
                f"-ArgumentList '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"{script_path}\"' "
                f"-Verb RunAs -WindowStyle Hidden"
            )
            ps_args = [
                "PowerShell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-Command", inner_command,
            ]
        
        # Launch as fully detached process
        # DETACHED_PROCESS: The new process does not inherit the console
        # CREATE_NEW_PROCESS_GROUP: The new process is the root of a new process group
        # CREATE_NO_WINDOW: The process is a console application running without a console window
        try:
            # On Windows, use creationflags for proper detachment
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.Popen(
                ps_args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=(
                    subprocess.DETACHED_PROCESS
                    | subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.CREATE_NO_WINDOW
                ),
                startupinfo=startupinfo,
            )
            self.log.debug("PowerShell update script launched successfully.")
        except Exception:
            self.log.exception("Failed to launch PowerShell update script")
            raise

    def _launch_detached_process_windows(self, app_path: Path):
        """Launch a Windows application as a detached process."""
        self.log.debug("Launching detached process: %s", app_path)
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 1  # SW_SHOWNORMAL = 1
            
            subprocess.Popen(
                [str(app_path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=(
                    subprocess.DETACHED_PROCESS
                    | subprocess.CREATE_NEW_PROCESS_GROUP
                ),
                startupinfo=startupinfo,
            )
            self.log.debug("Application launched successfully.")
        except Exception:
            self.log.exception("Failed to launch application")
            raise

    def _unix_join(self):
        """Unix/macOS restart using os.execl for in-place process replacement."""
        assert os.name == "posix"
        
        self.log.debug("Setting executable permissions on %s", self.current_app)
        try:
            # Set executable permissions (rwxr-xr-x)
            os.chmod(str(self.current_app), 0o755)
        except OSError:
            self.log.warning("Could not set executable permissions", exc_info=True)
        
        # Call exithook before exec (since exec replaces the process)
        if self.exithook is not None:
            self.exithook(False)  # noqa: FBT003
        
        self.log.info("Replacing current process with new app '%s'", self.current_app)
        os.execl(str(self.current_app), self.filename, *sys.argv[1:])  # noqa: S606

    def _unix_overwrite(self):
        """Unix/macOS overwrite strategy using a detached shell script.
        
        Creates a shell script that:
        1. Waits for the current process to exit
        2. Copies files
        3. Launches the new application
        4. Cleans up
        """
        self.log.info("Calling _unix_overwrite for updated app '%s'", self.updated_app)
        
        is_folder = self.updated_app.is_dir()
        current_pid = os.getpid()
        
        # Create the shell update script
        script_content = self._create_unix_update_script(
            source_path=self.updated_app,
            dest_path=self.current_app if not is_folder else self.current_app.parent,
            is_folder=is_folder,
            current_pid=current_pid,
            launch_app=self.current_app,
        )
        
        # Write script to a temporary file
        import tempfile
        script_dir = Path(tempfile.gettempdir()) / "holotoolset_update"
        script_dir.mkdir(parents=True, exist_ok=True)
        script_path = script_dir / f"update_{current_pid}.sh"
        
        self.log.debug("Writing update script to: %s", script_path)
        script_path.write_text(script_content, encoding="utf-8")
        os.chmod(script_path, 0o755)
        
        # Launch the shell script as a fully detached process
        self._launch_shell_script_detached(script_path)
        
        # Exit the application
        self._exit_application()

    def _create_unix_update_script(
        self,
        source_path: Path,
        dest_path: Path,
        is_folder: bool,
        current_pid: int,
        launch_app: Path,
    ) -> str:
        """Create a POSIX shell update script for macOS/Linux."""
        script = textwrap.dedent(f"""\
            #!/bin/bash
            # Auto-generated by Holocron Toolset updater
            
            PARENT_PID={current_pid}
            SOURCE_PATH='{source_path}'
            DEST_PATH='{dest_path}'
            LAUNCH_APP='{launch_app}'
            IS_FOLDER={'true' if is_folder else 'false'}
            MAX_RETRIES=30
            SCRIPT_PATH="$0"
            
            log() {{
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
            }}
            
            # Wait for parent process to exit
            log "Waiting for process $PARENT_PID to exit..."
            WAIT_COUNT=0
            MAX_WAIT=60
            
            while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
                if ! kill -0 $PARENT_PID 2>/dev/null; then
                    log "Process $PARENT_PID has exited."
                    break
                fi
                WAIT_COUNT=$((WAIT_COUNT + 1))
                sleep 1
            done
            
            if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
                log "WARNING: Timeout waiting for process $PARENT_PID. Proceeding anyway..."
            fi
            
            # Additional delay for file handles
            log "Waiting for file handles to be released..."
            sleep 2
            
            # Copy files with retry
            log "Starting file copy operation..."
            SUCCESS=false
            RETRY_COUNT=0
            
            while [ "$SUCCESS" = "false" ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                if [ "$IS_FOLDER" = "true" ]; then
                    log "Copying folder from '$SOURCE_PATH' to '$DEST_PATH'..."
                    if rsync -av --delete "$SOURCE_PATH/" "$DEST_PATH/" 2>/dev/null || \\
                       cp -Rf "$SOURCE_PATH"/* "$DEST_PATH/" 2>/dev/null; then
                        SUCCESS=true
                    fi
                else
                    log "Copying file from '$SOURCE_PATH' to '$DEST_PATH'..."
                    if cp -f "$SOURCE_PATH" "$DEST_PATH" 2>/dev/null; then
                        SUCCESS=true
                    fi
                fi
                
                if [ "$SUCCESS" = "false" ]; then
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                    log "Copy attempt $RETRY_COUNT failed. Retrying..."
                    sleep 1
                fi
            done
            
            if [ "$SUCCESS" = "false" ]; then
                log "ERROR: Failed to copy files after $MAX_RETRIES attempts."
                exit 1
            fi
            
            log "File copy completed successfully."
            
            # Set executable permissions
            chmod +x "$LAUNCH_APP" 2>/dev/null
            
            # Launch the updated application
            log "Launching updated application: $LAUNCH_APP"
            if [[ "$OSTYPE" == "darwin"* ]] && [[ "$LAUNCH_APP" == *.app ]]; then
                # macOS .app bundle
                open "$LAUNCH_APP" &
            else
                "$LAUNCH_APP" &
            fi
            
            # Clean up source if different from dest
            if [ "$IS_FOLDER" = "true" ] && [ "$SOURCE_PATH" != "$DEST_PATH" ]; then
                log "Cleaning up source folder..."
                rm -rf "$SOURCE_PATH" 2>/dev/null
            fi
            
            # Self-delete
            log "Update complete. Cleaning up..."
            sleep 1
            rm -f "$SCRIPT_PATH" 2>/dev/null
            
            exit 0
        """)
        
        return script

    def _launch_shell_script_detached(self, script_path: Path):
        """Launch a shell script as a fully detached process on Unix/macOS."""
        self.log.info("Launching shell update script: %s", script_path)
        
        try:
            # Use nohup and redirect all output to detach properly
            subprocess.Popen(
                ["nohup", str(script_path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
            )
            self.log.debug("Shell update script launched successfully.")
        except Exception:
            self.log.exception("Failed to launch shell update script")
            raise

    def _exit_application(self):
        """Exit the application cleanly, calling the exit hook if provided."""
        self.log.info("Exiting application (pid=%s)...", os.getpid())
        
        if self.exithook is not None:
            try:
                self.exithook(True)  # noqa: FBT003
            except SystemExit:
                # Expected - exithook called sys.exit
                raise
            except Exception:
                self.log.exception("Error in exit hook")
        
        # If exithook didn't exit, do it ourselves
        sys.exit(0)

    @staticmethod
    def win_get_system32_dir() -> Path:
        """Get the Windows System32 directory path."""
        import ctypes
        try:
            ctypes.windll.kernel32.GetSystemDirectoryW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
            ctypes.windll.kernel32.GetSystemDirectoryW.restype = ctypes.c_uint
            buffer = ctypes.create_unicode_buffer(260)
            ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
            return Path(buffer.value)
        except Exception:  # noqa: BLE001
            RobustLogger().warning(
                "Error accessing system directory via GetSystemDirectoryW. Attempting fallback.",
                exc_info=True,
            )
            buffer = ctypes.create_unicode_buffer(260)
            ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer))
            return Path(buffer.value).joinpath("system32")
