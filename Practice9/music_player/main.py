"""
main.py - Music Player with Keyboard Controls
A Pygame-based music player that supports MP3/WAV/OGG files.

Keyboard controls:
  P   – Play / Resume
  S   – Stop
  N   – Next track
  B   – Previous (Back) track
  ↑   – Volume up
  ↓   – Volume down
  Q   – Quit
  ESC – Quit

Place your audio files inside the  music/  folder.
"""

import pygame
import sys
import os
import math
from player import MusicPlayer

# ── Window ───────────────────────────────────────────────────────
WIDTH, HEIGHT = 700, 480
FPS           = 30
TITLE         = "🎵 Pygame Music Player"

# ── Colour palette ───────────────────────────────────────────────
BG          = ( 18,  18,  30)   # near-black background
PANEL       = ( 30,  30,  50)   # card background
ACCENT      = ( 90, 160, 255)   # blue accent
ACCENT2     = (255, 100, 150)   # pink accent
WHITE       = (255, 255, 255)
LIGHT_GRAY  = (180, 180, 200)
DARK_GRAY   = ( 80,  80, 100)
GREEN       = ( 80, 220, 120)
RED         = (220,  80,  80)
YELLOW      = (255, 210,  60)


def draw_rounded_rect(surface, rect, color, radius=18):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_progress_bar(surface, x, y, w, h, fraction, bg_color, fill_color, radius=6):
    """Draw a rounded progress bar."""
    draw_rounded_rect(surface, (x, y, w, h), bg_color, radius)
    if fraction > 0:
        fill_w = max(radius * 2, int(w * fraction))
        draw_rounded_rect(surface, (x, y, fill_w, h), fill_color, radius)


def draw_visualiser(surface, x, y, w, h, tick, is_playing):
    """Animated sound-wave bars (decoration only)."""
    bars    = 24
    bar_w   = (w - bars + 1) // bars
    spacing = 1
    for i in range(bars):
        if is_playing:
            # Each bar oscillates at a different phase
            phase  = tick * 0.08 + i * 0.4
            height = int(abs(math.sin(phase)) * (h - 10)) + 6
        else:
            height = 6
        bx = x + i * (bar_w + spacing)
        by = y + h - height
        color_val = 90 + int(165 * i / bars)
        bar_color = (color_val, 100, 255 - color_val // 2)
        pygame.draw.rect(surface, bar_color, (bx, by, bar_w, height), border_radius=3)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # ── Fonts ────────────────────────────────────────────────────
    font_title  = pygame.font.SysFont("Arial", 28, bold=True)
    font_track  = pygame.font.SysFont("Arial", 22, bold=True)
    font_status = pygame.font.SysFont("Arial", 18)
    font_small  = pygame.font.SysFont("Arial", 15)
    font_key    = pygame.font.SysFont("Consolas", 15)

    # ── Music player ─────────────────────────────────────────────
    player = MusicPlayer(music_dir="music")

    tick = 0   # frame counter for animation

    # Key-binding help text
    key_help = [
        ("[P]", "Play/Resume"),
        ("[S]", "Stop"),
        ("[N]", "Next track"),
        ("[B]", "Previous"),
        ("[↑↓]", "Volume"),
        ("[Q/ESC]", "Quit"),
    ]

    running = True
    while running:
        tick += 1

        # ── Events ───────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_p:
                    player.pause_resume()
                elif event.key == pygame.K_s:
                    player.stop()
                elif event.key == pygame.K_n:
                    player.next_track()
                elif event.key == pygame.K_b:
                    player.prev_track()
                elif event.key == pygame.K_UP:
                    player.volume_up()
                elif event.key == pygame.K_DOWN:
                    player.volume_down()

        # Auto-advance when a track finishes
        player.check_track_ended()

        # ── Draw background ───────────────────────────────────
        screen.fill(BG)

        # ── Title bar ─────────────────────────────────────────
        title_surf = font_title.render("♫ Pygame Music Player", True, ACCENT)
        screen.blit(title_surf, (30, 22))

        # ── Main panel ────────────────────────────────────────
        panel_rect = (20, 65, WIDTH - 40, 250)
        draw_rounded_rect(screen, panel_rect, PANEL, 20)

        if player.has_tracks():
            # Track index badge
            badge_txt = f"{player.current_idx + 1} / {len(player.playlist)}"
            badge_s   = font_small.render(badge_txt, True, DARK_GRAY)
            screen.blit(badge_s, (WIDTH - 40 - badge_s.get_width(), 80))

            # Track name
            name_surf = font_track.render(player.get_track_name(), True, WHITE)
            screen.blit(name_surf, (40, 85))

            # Status  (▶ PLAYING / ⏸ PAUSED / ⏹ STOPPED)
            status     = player.get_status()
            stat_color = GREEN if "PLAYING" in status else (YELLOW if "PAUSED" in status else RED)
            stat_surf  = font_status.render(status, True, stat_color)
            screen.blit(stat_surf, (40, 120))

            # Progress bar (time-based, max display 5 minutes)
            pos_sec  = player.get_position_sec()
            max_sec  = 300.0   # 5-minute cap for display
            fraction = min(1.0, pos_sec / max_sec)
            draw_progress_bar(screen, 40, 158, WIDTH - 100, 14, fraction,
                              DARK_GRAY, ACCENT, radius=7)

            pos_label = font_small.render(f"{int(pos_sec)//60:02d}:{int(pos_sec)%60:02d}", True, LIGHT_GRAY)
            screen.blit(pos_label, (40, 178))

            # Volume bar
            vol_lbl = font_small.render(f"Vol: {player.get_volume_bar()} {int(player.volume*100):3d}%",
                                        True, LIGHT_GRAY)
            screen.blit(vol_lbl, (40, 200))

            # Animated visualiser
            draw_visualiser(screen, 40, 225, WIDTH - 100, 60, tick,
                            player.is_playing and not player.is_paused)

        else:
            msg = font_status.render("No audio files found in  music/  folder.", True, RED)
            screen.blit(msg, (40, 120))
            hint = font_small.render("Add .mp3 / .wav / .ogg files and restart.", True, LIGHT_GRAY)
            screen.blit(hint, (40, 150))

        # ── Keyboard help panel ───────────────────────────────
        help_rect = (20, 330, WIDTH - 40, 110)
        draw_rounded_rect(screen, help_rect, PANEL, 16)

        hdr = font_small.render("KEYBOARD CONTROLS", True, DARK_GRAY)
        screen.blit(hdr, (36, 338))

        col_w   = (WIDTH - 80) // 3
        entries = list(zip(key_help[::2], key_help[1::2]))   # 2 per row × 3 cols
        for col_i, pair in enumerate(entries):
            for row_i, (key, desc) in enumerate(pair):
                kx = 36 + col_i * col_w
                ky = 358 + row_i * 26
                ks = font_key.render(key, True, ACCENT2)
                ds = font_key.render(f" {desc}", True, LIGHT_GRAY)
                screen.blit(ks, (kx, ky))
                screen.blit(ds, (kx + ks.get_width(), ky))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()