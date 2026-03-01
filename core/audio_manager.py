# =============================================================================
# AUDIO_MANAGER.PY - AUDIO MANAGER
# =============================================================================
#
# Manages all game audio: background music and sound effects (SFX).
# Centralizes playback and handles missing files gracefully.

import pygame
import os
from config.settings import MUSIC_DIR, SFX_DIR


# =============================================================================
# AUDIO MANAGER CLASS
# =============================================================================

class AudioManager:
    """
    Centralizes audio management.
    Handles music transitions (fadeout) and SFX playback.
    Doesn't crash if audio files are missing.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """
        Initialize the mixer and pre-load all SFX.
        
        Music is NOT pre-loaded. pygame.mixer.music streams from file,
        so we load on demand when playing a track. This saves memory.
        
        SFX ARE pre-loaded. pygame.mixer.Sound loads the entire file
        into memory. We do this once at startup to avoid micro-freezes
        during gameplay when playing a sound.
        
        current_music: name of currently playing music, to avoid restarting
            the same track if already playing.
        
        music_volume / sfx_volume: between 0.0 (mute) and 1.0 (max).
            Default values are reasonable. Player could change them later
            via options menu (Won't Have for now).
        
        audio_available: bool indicating if Pygame mixer initialized.
            On some machines without sound card, this may fail.
            If False, all methods do nothing (no crash).
        """
        # Check if mixer works
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.audio_available = True
        except Exception:
            print("Warning: Audio mixer not available")
            self.audio_available = False
        
        self.current_music = None
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        
        # Music paths (loaded on demand)
        self.music = {
            "menu": MUSIC_DIR / "menu.ogg",
            "exploration_campus": MUSIC_DIR / "exploration_campus.ogg",
            "exploration_outside": MUSIC_DIR / "exploration_outside.ogg",
            "combat_wild": MUSIC_DIR / "combat_wild.ogg",
            "combat_trainer": MUSIC_DIR / "combat_trainer.ogg",
            "tournament": MUSIC_DIR / "tournament.ogg",
            "victory": MUSIC_DIR / "victory.ogg",
            "defeat": MUSIC_DIR / "defeat.ogg"
        }
        
        # Pre-load SFX
        self.sfx = {}
        sfx_to_load = {
            "attack": SFX_DIR / "attack.ogg",
            "capture": SFX_DIR / "capture.ogg",
            "heal": SFX_DIR / "heal.ogg",
            "levelup": SFX_DIR / "levelup.ogg",
            "evolution": SFX_DIR / "evolution.ogg",
            "dialogue_bip": SFX_DIR / "dialogue_bip.ogg",
            "menu_select": SFX_DIR / "menu_select.ogg",
            "purchase": SFX_DIR / "purchase.ogg",
            "error": SFX_DIR / "error.ogg"
        }
        
        if self.audio_available:
            for name, path in sfx_to_load.items():
                if os.path.exists(path):
                    try:
                        self.sfx[name] = pygame.mixer.Sound(str(path))
                        self.sfx[name].set_volume(self.sfx_volume)
                    except Exception:
                        print(f"Warning: Could not load SFX: {path}")
                else:
                    print(f"Warning: SFX file not found: {path}")
    
    
    # -------------------------------------------------------------------------
    # MUSIC METHODS
    # -------------------------------------------------------------------------
    
    def play_music(self, music_key, loop=True, fadeout_ms=500):
        """
        Play background music.
        
        Args:
            music_key: key in self.music dict ("menu", "combat_wild", etc.)
            loop: True to loop, False to play once
            fadeout_ms: fadeout duration in milliseconds before changing
        """
        if not self.audio_available:
            return
        
        # Don't restart same music
        if self.current_music == music_key:
            return
        
        path = self.music.get(music_key)
        if path is None or not os.path.exists(path):
            print(f"Warning: Music not found: {music_key}")
            return
        
        try:
            # Fade out current music
            pygame.mixer.music.fadeout(fadeout_ms)
            
            # Load and play new music
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            
            self.current_music = music_key
        
        except Exception as e:
            print(f"Error playing music {music_key}: {e}")
    
    
    def stop_music(self, fadeout_ms=500):
        """Stop current music with fadeout."""
        if not self.audio_available:
            return
        
        try:
            pygame.mixer.music.fadeout(fadeout_ms)
            self.current_music = None
        except Exception:
            pass
    
    
    def set_music_volume(self, volume):
        """
        Set music volume.
        
        Args:
            volume: float between 0.0 and 1.0
        """
        self.music_volume = max(0.0, min(1.0, volume))
        if self.audio_available:
            pygame.mixer.music.set_volume(self.music_volume)
    
    
    # -------------------------------------------------------------------------
    # SFX METHODS
    # -------------------------------------------------------------------------
    
    def play_sfx(self, sfx_key):
        """
        Play a sound effect.
        
        Args:
            sfx_key: key in self.sfx dict ("attack", "heal", etc.)
        """
        if not self.audio_available:
            return
        
        sound = self.sfx.get(sfx_key)
        if sound is not None:
            try:
                sound.play()
            except Exception:
                pass
        else:
            print(f"Warning: SFX not loaded: {sfx_key}")
    
    
    def set_sfx_volume(self, volume):
        """
        Set sound effects volume.
        
        Args:
            volume: float between 0.0 and 1.0
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        if self.audio_available:
            for sound in self.sfx.values():
                sound.set_volume(self.sfx_volume)
    
    
    # -------------------------------------------------------------------------
    # UTILITY
    # -------------------------------------------------------------------------
    
    def is_music_playing(self):
        """Return True if music is currently playing."""
        if not self.audio_available:
            return False
        return pygame.mixer.music.get_busy()
    
    
    def get_current_music(self):
        """Return key of currently playing music, or None."""
        return self.current_music