"""
player.py - Music Player Logic
Manages playlist, playback state, and track information.
"""

import os
import pygame


class MusicPlayer:
    """Handles playlist management and audio playback via pygame.mixer."""

    SUPPORTED = (".mp3", ".wav", ".ogg", ".flac")

    def __init__(self, music_dir: str = "music"):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self.music_dir    = music_dir
        self.playlist     = []          # list of file paths
        self.current_idx  = 0          # index of current track
        self.is_playing   = False
        self.is_paused    = False
        self.volume       = 0.7        # 0.0 – 1.0

        pygame.mixer.music.set_volume(self.volume)
        self._load_playlist()

    # ── Playlist ──────────────────────────────────────────────────

    def _load_playlist(self):
        """Scan music_dir for supported audio files."""
        if not os.path.isdir(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)

        self.playlist = sorted([
            os.path.join(self.music_dir, f)
            for f in os.listdir(self.music_dir)
            if f.lower().endswith(self.SUPPORTED)
        ])

    def has_tracks(self) -> bool:
        return len(self.playlist) > 0

    # ── Playback controls ─────────────────────────────────────────

    def play(self):
        """Play the current track from the beginning."""
        if not self.has_tracks():
            return
        pygame.mixer.music.load(self.playlist[self.current_idx])
        pygame.mixer.music.play()
        self.is_playing = True
        self.is_paused  = False

    def stop(self):
        """Stop playback completely."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused  = False

    def pause_resume(self):
        """Toggle between paused and playing."""
        if not self.is_playing:
            self.play()
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self.is_paused = True

    def next_track(self):
        """Advance to the next track (wraps around)."""
        if not self.has_tracks():
            return
        self.current_idx = (self.current_idx + 1) % len(self.playlist)
        if self.is_playing:
            self.play()

    def prev_track(self):
        """Go back to the previous track (wraps around)."""
        if not self.has_tracks():
            return
        self.current_idx = (self.current_idx - 1) % len(self.playlist)
        if self.is_playing:
            self.play()

    # ── Volume ────────────────────────────────────────────────────

    def volume_up(self):
        self.volume = min(1.0, self.volume + 0.1)
        pygame.mixer.music.set_volume(self.volume)

    def volume_down(self):
        self.volume = max(0.0, self.volume - 0.1)
        pygame.mixer.music.set_volume(self.volume)

    # ── Info ──────────────────────────────────────────────────────

    def get_track_name(self) -> str:
        """Return just the filename (without extension) of the current track."""
        if not self.has_tracks():
            return "No tracks found"
        path = self.playlist[self.current_idx]
        return os.path.splitext(os.path.basename(path))[0]

    def get_position_sec(self) -> float:
        """Return playback position in seconds."""
        if self.is_playing:
            return pygame.mixer.music.get_pos() / 1000.0
        return 0.0

    def get_status(self) -> str:
        if not self.has_tracks():
            return "No tracks"
        if self.is_paused:
            return "⏸ PAUSED"
        if self.is_playing:
            return "▶ PLAYING"
        return "⏹ STOPPED"

    def get_volume_bar(self) -> str:
        """Visual volume bar  ████░░░░░░  (10 segments)."""
        filled = round(self.volume * 10)
        return "█" * filled + "░" * (10 - filled)

    def check_track_ended(self):
        """Auto-advance to next track when current one finishes."""
        if self.is_playing and not self.is_paused:
            if not pygame.mixer.music.get_busy():
                self.next_track()