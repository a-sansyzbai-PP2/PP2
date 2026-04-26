"""
ui.py — All non-gameplay screens drawn purely with Pygame.
Screens: MainMenu, NameEntry, Settings, Leaderboard, GameOver.
Each function returns a dict describing what to do next.
"""

import pygame
import sys
from racer import (
    screen, clock, font_large, font_medium, font_small, font_tiny,
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    WHITE, BLACK, GRAY, RED, YELLOW, GREEN, BLUE, ORANGE, PURPLE,
    CAR_COLOR_MAP,
)
from persistence import load_leaderboard, load_settings, save_settings

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = ( 15,  15,  25)
PANEL    = ( 30,  30,  48)
ACCENT   = ( 72, 144, 240)
MUTED    = (100, 100, 120)
NITRO_C  = (  0, 240, 180)


# ── Generic helpers ───────────────────────────────────────────────────────────
def _draw_bg(surface):
    surface.fill(BG)
    # subtle grid lines
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(surface, (25, 25, 40), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(surface, (25, 25, 40), (0, y), (SCREEN_WIDTH, y))


class Button:
    H = 42

    def __init__(self, label, x, y, w, color=ACCENT):
        self.rect  = pygame.Rect(x, y, w, self.H)
        self.label = label
        self.base  = color
        self.hover_col = tuple(min(255, c + 40) for c in color)

    def draw(self, surface):
        mp    = pygame.mouse.get_pos()
        color = self.hover_col if self.rect.collidepoint(mp) else self.base
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.rect, 1, border_radius=8)
        lbl = font_medium.render(self.label, True, WHITE)
        surface.blit(lbl, (self.rect.centerx - lbl.get_width() // 2,
                           self.rect.centery - lbl.get_height() // 2))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


def _title(surface, text, y=60):
    lbl = font_large.render(text, True, ACCENT)
    surface.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, y))


def _subtitle(surface, text, y, color=MUTED):
    lbl = font_small.render(text, True, color)
    surface.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, y))


# ── Main Menu ─────────────────────────────────────────────────────────────────
def main_menu(settings: dict) -> dict:
    """Returns {'action': 'play'|'quit'|'leaderboard'|'settings'}"""
    W = 200
    cx = SCREEN_WIDTH // 2 - W // 2
    btns = [
        Button("▶  Play",        cx, 200, W),
        Button("🏆  Leaderboard", cx, 258, W, (60, 120, 60)),
        Button("⚙  Settings",    cx, 316, W, (80,  80, 140)),
        Button("✕  Quit",        cx, 374, W, (140, 40, 40)),
    ]

    while True:
        _draw_bg(screen)
        _title(screen, "RACER", 90)
        _subtitle(screen, "TSIS 3 Edition", 138, NITRO_C)

        # Mini car decoration
        pygame.draw.rect(screen, CAR_COLOR_MAP.get(settings.get("car_color","blue"), BLUE),
                         (SCREEN_WIDTH//2 - 20, 158, 40, 30), border_radius=6)

        for btn in btns:
            btn.draw(screen)

        _subtitle(screen, "Arrow keys to drive", SCREEN_HEIGHT - 30)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if btns[0].clicked(event): return {"action": "play"}
            if btns[1].clicked(event): return {"action": "leaderboard"}
            if btns[2].clicked(event): return {"action": "settings"}
            if btns[3].clicked(event): pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return {"action": "play"}


# ── Name Entry ────────────────────────────────────────────────────────────────
def name_entry() -> str:
    """Prompt the player for their name; return the name string."""
    name = ""
    input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 280, 200, 40)

    while True:
        _draw_bg(screen)
        _title(screen, "ENTER NAME", 120)
        _subtitle(screen, "Type your name, then press Enter", 180)

        pygame.draw.rect(screen, PANEL, input_rect, border_radius=6)
        pygame.draw.rect(screen, ACCENT, input_rect, 2, border_radius=6)
        txt = font_medium.render(name + "|", True, WHITE)
        screen.blit(txt, (input_rect.x + 8, input_rect.y + 8))

        _subtitle(screen, "Press Enter to confirm", 340, MUTED)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip():
                    return name.strip()[:16]
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode and event.unicode.isprintable() and len(name) < 16:
                    name += event.unicode


# ── Settings ──────────────────────────────────────────────────────────────────
def settings_screen(settings: dict) -> dict:
    """Mutates and saves settings in place; returns updated settings dict."""
    s = dict(settings)

    colors      = ["blue", "red", "green", "orange", "purple"]
    difficulties= ["easy", "normal", "hard"]

    W = 220
    cx = SCREEN_WIDTH // 2 - W // 2

    while True:
        _draw_bg(screen)
        _title(screen, "SETTINGS", 60)

        # Sound toggle
        sound_col = GREEN if s["sound"] else (140, 40, 40)
        snd_btn   = Button(f"Sound: {'ON' if s['sound'] else 'OFF'}", cx, 140, W, sound_col)

        # Car color cycle
        car_btn   = Button(f"Car: {s['car_color'].capitalize()}", cx, 200, W,
                           CAR_COLOR_MAP.get(s["car_color"], BLUE))

        # Difficulty cycle
        diff_col  = {
            "easy":   (50, 180, 50),
            "normal": (80, 80, 180),
            "hard":   (200, 40, 40),
        }[s["difficulty"]]
        diff_btn  = Button(f"Difficulty: {s['difficulty'].capitalize()}", cx, 260, W, diff_col)

        back_btn  = Button("← Back", cx, 360, W, (80, 80, 80))

        # Preview car swatch
        swx = SCREEN_WIDTH // 2 - 22
        pygame.draw.rect(screen, CAR_COLOR_MAP.get(s["car_color"], BLUE),
                         (swx, 310, 44, 34), border_radius=6)

        for btn in [snd_btn, car_btn, diff_btn, back_btn]:
            btn.draw(screen)

        _subtitle(screen, "Changes saved automatically", SCREEN_HEIGHT - 30)
        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if snd_btn.clicked(event):
                s["sound"] = not s["sound"]
            if car_btn.clicked(event):
                idx = colors.index(s["car_color"])
                s["car_color"] = colors[(idx + 1) % len(colors)]
            if diff_btn.clicked(event):
                idx = difficulties.index(s["difficulty"])
                s["difficulty"] = difficulties[(idx + 1) % len(difficulties)]
            if back_btn.clicked(event):
                save_settings(s)
                return s
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                save_settings(s)
                return s


# ── Leaderboard ───────────────────────────────────────────────────────────────
def leaderboard_screen() -> None:
    entries = load_leaderboard()
    back    = Button("← Back", SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT - 60, 140, (80, 80, 80))

    while True:
        _draw_bg(screen)
        _title(screen, "TOP 10", 30)

        # Header
        hdr = font_tiny.render(
            f"{'#':<3} {'Name':<14} {'Score':>6}  {'Dist':>5}  {'Coins':>5}",
            True, ACCENT)
        screen.blit(hdr, (20, 90))
        pygame.draw.line(screen, ACCENT, (20, 110), (SCREEN_WIDTH - 20, 110), 1)

        if not entries:
            _subtitle(screen, "No scores yet — play a run!", 200, MUTED)
        else:
            for i, e in enumerate(entries):
                row_col = YELLOW if i == 0 else (WHITE if i < 3 else GRAY)
                row = font_small.render(
                    f"{i+1:<3} {e['name']:<14} {e['score']:>6}  {e['distance']:>5}m  {e['coins']:>4}$",
                    True, row_col)
                screen.blit(row, (20, 118 + i * 28))

        back.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if back.clicked(event):
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return


# ── Game Over ─────────────────────────────────────────────────────────────────
def game_over_screen(name: str, score: int, distance: int, coins: int) -> str:
    """
    Show game-over screen.
    Returns 'retry' or 'menu'.
    """
    W   = 200
    cx  = SCREEN_WIDTH // 2 - W // 2
    retry_btn = Button("↺  Retry",    cx, 380, W, (50, 160, 50))
    menu_btn  = Button("⌂  Main Menu",cx, 434, W, (80, 80, 140))

    while True:
        _draw_bg(screen)

        # Big GAME OVER
        go = font_large.render("GAME OVER", True, RED)
        screen.blit(go, (SCREEN_WIDTH // 2 - go.get_width() // 2, 80))

        # Stats panel
        pygame.draw.rect(screen, PANEL, (40, 140, SCREEN_WIDTH - 80, 210), border_radius=10)
        pygame.draw.rect(screen, ACCENT, (40, 140, SCREEN_WIDTH - 80, 210), 1, border_radius=10)

        lines = [
            (f"Player :  {name}",          WHITE),
            (f"Score  :  {score}",          YELLOW),
            (f"Distance: {distance} m",     (0, 220, 220)),
            (f"Coins  :  {coins}",          YELLOW),
        ]
        for i, (txt, col) in enumerate(lines):
            lbl = font_medium.render(txt, True, col)
            screen.blit(lbl, (60, 158 + i * 40))

        retry_btn.draw(screen)
        menu_btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if retry_btn.clicked(event): return "retry"
            if menu_btn.clicked(event):  return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:      return "retry"
                if event.key == pygame.K_ESCAPE: return "menu"