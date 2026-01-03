"""Sound system for HoloPazaak.

This module provides sound effects for game events, inspired by the
audio elements from the original KOTOR Pazaak implementation.

The sound system is designed to be optional - if PyQt6 multimedia
is not available or sound files are missing, the game continues silently.

References:
- KOTOR Pazaak uses ambient cantina music and card sound effects
- pazaak-eggborne has sound effect triggers in game events
"""
from __future__ import annotations

import logging
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)


class SoundEffect(Enum):
    """Available sound effects."""
    # Card sounds
    CARD_DEAL = auto()      # Card dealt from main deck
    CARD_PLAY = auto()      # Card played from hand
    CARD_FLIP = auto()      # Flip card toggled
    
    # Game events
    TURN_START = auto()     # Player's turn begins
    STAND = auto()          # Player stands
    BUST = auto()           # Player busts (over 20)
    WIN_ROUND = auto()      # Round won
    LOSE_ROUND = auto()     # Round lost
    TIE_ROUND = auto()      # Round tied
    WIN_GAME = auto()       # Match won
    LOSE_GAME = auto()      # Match lost
    
    # UI sounds
    BUTTON_CLICK = auto()   # Button clicked
    MENU_OPEN = auto()      # Menu/dialog opened
    MENU_CLOSE = auto()     # Menu/dialog closed
    
    # Ambient
    CANTINA_MUSIC = auto()  # Background music


class SoundManager:
    """Manager for game sounds and music.
    
    This class handles loading and playing sound effects. It uses
    Qt's multimedia capabilities when available, but gracefully
    falls back to silent operation if not.
    
    Usage:
        sound_manager = SoundManager()
        sound_manager.play(SoundEffect.CARD_DEAL)
    """
    
    # Default sound file mappings
    SOUND_FILES = {
        SoundEffect.CARD_DEAL: "card_deal.wav",
        SoundEffect.CARD_PLAY: "card_play.wav",
        SoundEffect.CARD_FLIP: "card_flip.wav",
        SoundEffect.TURN_START: "turn_start.wav",
        SoundEffect.STAND: "stand.wav",
        SoundEffect.BUST: "bust.wav",
        SoundEffect.WIN_ROUND: "win_round.wav",
        SoundEffect.LOSE_ROUND: "lose_round.wav",
        SoundEffect.TIE_ROUND: "tie_round.wav",
        SoundEffect.WIN_GAME: "win_game.wav",
        SoundEffect.LOSE_GAME: "lose_game.wav",
        SoundEffect.BUTTON_CLICK: "button_click.wav",
        SoundEffect.MENU_OPEN: "menu_open.wav",
        SoundEffect.MENU_CLOSE: "menu_close.wav",
        SoundEffect.CANTINA_MUSIC: "cantina_music.mp3",
    }
    
    def __init__(self, sounds_dir: Path | str | None = None):
        """Initialize the sound manager.
        
        Args:
            sounds_dir: Directory containing sound files. If None,
                       uses a default relative to this module.
        """
        self._enabled = True
        self._volume = 0.7  # 0.0 to 1.0
        self._music_volume = 0.5
        self._sounds_dir = Path(sounds_dir) if sounds_dir else self._get_default_sounds_dir()
        self._sound_cache: dict = {}
        self._music_player = None
        self._qt_available = False
        
        self._init_qt_audio()
    
    def _get_default_sounds_dir(self) -> Path:
        """Get the default sounds directory."""
        # Relative to this module
        module_dir = Path(__file__).parent
        return module_dir / "assets" / "sounds"
    
    def _init_qt_audio(self):
        """Initialize Qt audio system if available."""
        try:
            # Try to import Qt multimedia
            from qtpy.QtCore import QUrl
            from qtpy.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput
            
            self._qt_available = True
            logger.info("Qt multimedia initialized successfully")
            
            # Create media player for music
            self._music_player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._music_player.setAudioOutput(self._audio_output)
            self._audio_output.setVolume(self._music_volume)
            
        except ImportError as e:
            logger.warning(f"Qt multimedia not available: {e}")
            self._qt_available = False
        except Exception as e:
            logger.warning(f"Failed to initialize Qt audio: {e}")
            self._qt_available = False
    
    @property
    def enabled(self) -> bool:
        """Check if sound is enabled."""
        return self._enabled and self._qt_available
    
    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable sound."""
        self._enabled = value
        if not value and self._music_player:
            self._music_player.stop()
    
    @property
    def volume(self) -> float:
        """Get the sound effect volume (0.0 to 1.0)."""
        return self._volume
    
    @volume.setter
    def volume(self, value: float):
        """Set the sound effect volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, value))
    
    @property
    def music_volume(self) -> float:
        """Get the music volume (0.0 to 1.0)."""
        return self._music_volume
    
    @music_volume.setter
    def music_volume(self, value: float):
        """Set the music volume (0.0 to 1.0)."""
        self._music_volume = max(0.0, min(1.0, value))
        if self._qt_available and hasattr(self, '_audio_output'):
            self._audio_output.setVolume(self._music_volume)
    
    def play(self, effect: SoundEffect):
        """Play a sound effect.
        
        Args:
            effect: The sound effect to play
        """
        if not self.enabled:
            return
        
        if effect == SoundEffect.CANTINA_MUSIC:
            self._play_music(effect)
            return
        
        self._play_effect(effect)
    
    def _play_effect(self, effect: SoundEffect):
        """Play a short sound effect."""
        if not self._qt_available:
            return
        
        try:
            from qtpy.QtCore import QUrl
            from qtpy.QtMultimedia import QSoundEffect
            
            # Get or create sound effect
            if effect not in self._sound_cache:
                sound_file = self.SOUND_FILES.get(effect)
                if not sound_file:
                    return
                
                sound_path = self._sounds_dir / sound_file
                if not sound_path.exists():
                    logger.debug(f"Sound file not found: {sound_path}")
                    return
                
                sound = QSoundEffect()
                sound.setSource(QUrl.fromLocalFile(str(sound_path)))
                sound.setVolume(self._volume)
                self._sound_cache[effect] = sound
            
            sound = self._sound_cache[effect]
            sound.setVolume(self._volume)
            sound.play()
            
        except Exception as e:
            logger.debug(f"Failed to play sound effect {effect}: {e}")
    
    def _play_music(self, effect: SoundEffect):
        """Play background music."""
        if not self._qt_available or not self._music_player:
            return
        
        try:
            from qtpy.QtCore import QUrl
            
            sound_file = self.SOUND_FILES.get(effect)
            if not sound_file:
                return
            
            sound_path = self._sounds_dir / sound_file
            if not sound_path.exists():
                logger.debug(f"Music file not found: {sound_path}")
                return
            
            self._music_player.setSource(QUrl.fromLocalFile(str(sound_path)))
            self._music_player.setLoops(-1)  # Loop indefinitely
            self._music_player.play()
            
        except Exception as e:
            logger.debug(f"Failed to play music: {e}")
    
    def stop_music(self):
        """Stop background music."""
        if self._music_player:
            self._music_player.stop()
    
    def pause_music(self):
        """Pause background music."""
        if self._music_player:
            self._music_player.pause()
    
    def resume_music(self):
        """Resume background music."""
        if self._music_player:
            self._music_player.play()
    
    def cleanup(self):
        """Clean up audio resources."""
        self.stop_music()
        self._sound_cache.clear()


# Global sound manager instance
_sound_manager: SoundManager | None = None


def get_sound_manager() -> SoundManager:
    """Get the global sound manager instance."""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager


def play_sound(effect: SoundEffect):
    """Play a sound effect using the global sound manager."""
    get_sound_manager().play(effect)

