"""
main.py — Entry point, all screens, and the main game loop.

Run:  python main.py

Dependencies:
    pip install pygame psycopg2-binary
    (psycopg2 is optional — game runs offline if DB is unavailable)
"""

import pygame
import sys
import json
import os
import random

# ── Bootstrap pygame before any local import that creates fonts ───────────────
pygame.init()

from config import (
    CELL, COLS, ROWS, PANEL_H, WIDTH, HEIGHT,
    BASE_FPS, BASE_MOVE, FOOD_PER_LEVEL, POWERUP_DURATION,
    BG_COLOR, PANEL_COLOR, WALL_COLOR, TEXT_COLOR, MUTED,
    GOLD, RED, ACCENT, GREEN_LT, GREEN_DK,
    PU_SPEED_COL, PU_SLOW_COL, PU_SHIELD_COL,
    cell_to_px,
)
from game import (
    Snake, NormalFood, BonusFood, PoisonFood, PowerUp,
    generate_obstacles, draw_obstacles,
    draw_field, draw_hud,
    PU_KINDS,
)
import db

# ── Settings file ─────────────────────────────────────────────────────────────
SETTINGS_FILE    = "settings.json"
DEFAULT_SETTINGS = {
    "snake_color": [50, 220, 50],   # RGB list
    "grid":        True,
    "sound":       True,
}

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(s: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)


# ── Pygame globals ────────────────────────────────────────────────────────────
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake — TSIS 4")
clock  = pygame.time.Clock()

font_large  = pygame.font.SysFont("Consolas", 40, bold=True)
font_medium = pygame.font.SysFont("Consolas", 24, bold=True)
font_small  = pygame.font.SysFont("Consolas", 18)
font_tiny   = pygame.font.SysFont("Consolas", 13)


# ─────────────────────────────────────────────────────────────────────────────
#  Generic UI helpers
# ─────────────────────────────────────────────────────────────────────────────
BG_MENU  = ( 12,  12,  22)
PANEL_UI = ( 28,  28,  48)
BTN_COL  = ( 50,  90, 180)
BTN_HOV  = ( 80, 130, 220)


def _draw_bg():
    screen.fill(BG_MENU)
    for x in range(0, WIDTH, 40):
        pygame.draw.line(screen, (20, 20, 36), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(screen, (20, 20, 36), (0, y), (WIDTH, y))


class Button:
    H = 42

    def __init__(self, label, x, y, w, color=BTN_COL):
        self.rect  = pygame.Rect(x, y, w, self.H)
        self.label = label
        self.base  = color
        self.hov   = tuple(min(255, c + 40) for c in color)

    def draw(self):
        mp  = pygame.mouse.get_pos()
        col = self.hov if self.rect.collidepoint(mp) else self.base
        pygame.draw.rect(screen, col,  self.rect, border_radius=8)
        pygame.draw.rect(screen, (200, 200, 220), self.rect, 1, border_radius=8)
        lbl = font_medium.render(self.label, True, TEXT_COLOR)
        screen.blit(lbl, (self.rect.centerx - lbl.get_width()//2,
                          self.rect.centery - lbl.get_height()//2))

    def clicked(self, ev):
        return ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and \
               self.rect.collidepoint(ev.pos)


def _title(text, y=50, color=ACCENT):
    lbl = font_large.render(text, True, color)
    screen.blit(lbl, (WIDTH//2 - lbl.get_width()//2, y))

def _sub(text, y, color=MUTED):
    lbl = font_small.render(text, True, color)
    screen.blit(lbl, (WIDTH//2 - lbl.get_width()//2, y))


# ─────────────────────────────────────────────────────────────────────────────
#  Screen: Name entry
# ─────────────────────────────────────────────────────────────────────────────
def screen_name_entry() -> str:
    name = ""
    box  = pygame.Rect(WIDTH//2 - 100, 240, 200, 38)
    while True:
        _draw_bg()
        _title("SNAKE", 80)
        _sub("Enter your username", 170)
        pygame.draw.rect(screen, PANEL_UI, box, border_radius=6)
        pygame.draw.rect(screen, ACCENT,   box, 2, border_radius=6)
        cur = font_medium.render(name + "|", True, TEXT_COLOR)
        screen.blit(cur, (box.x + 8, box.y + 7))
        _sub("Press Enter to confirm", 300)
        pygame.display.flip()
        clock.tick(BASE_FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN and name.strip():
                    return name.strip()[:20]
                elif ev.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif ev.unicode and ev.unicode.isprintable() and len(name) < 20:
                    name += ev.unicode


# ─────────────────────────────────────────────────────────────────────────────
#  Screen: Main menu
# ─────────────────────────────────────────────────────────────────────────────
def screen_main_menu(username: str, settings: dict) -> str:
    """Returns 'play' | 'leaderboard' | 'settings' | 'quit'."""
    W = 200; cx = WIDTH//2 - W//2
    btns = [
        Button("▶  Play",        cx, 190, W),
        Button("🏆 Leaderboard", cx, 246, W, (50,120,50)),
        Button("⚙  Settings",   cx, 302, W, (80,80,150)),
        Button("✕  Quit",       cx, 358, W, (140,40,40)),
    ]
    while True:
        _draw_bg()
        _title("SNAKE", 80)
        _sub(f"Hello, {username}!", 142, GOLD)
        for btn in btns: btn.draw()
        _sub("Arrow keys / WASD to move", HEIGHT - 28)
        pygame.display.flip()
        clock.tick(BASE_FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btns[0].clicked(ev): return "play"
            if btns[1].clicked(ev): return "leaderboard"
            if btns[2].clicked(ev): return "settings"
            if btns[3].clicked(ev): pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                return "play"


# ─────────────────────────────────────────────────────────────────────────────
#  Screen: Settings
# ─────────────────────────────────────────────────────────────────────────────
_COLOR_OPTIONS = [
    ("Green",  [50, 220, 50]),
    ("Blue",   [30, 100, 220]),
    ("Red",    [220, 50, 50]),
    ("Orange", [255, 140, 0]),
    ("Purple", [160, 32, 240]),
]

def screen_settings(settings: dict) -> dict:
    s   = dict(settings)
    W   = 220; cx = WIDTH//2 - W//2
    col_idx = next(
        (i for i, (_, c) in enumerate(_COLOR_OPTIONS) if c == s["snake_color"]), 0)

    while True:
        s_col = tuple(_COLOR_OPTIONS[col_idx][1])
        grid_col = (50,180,50) if s["grid"]  else (140,40,40)
        snd_col  = (50,180,50) if s["sound"] else (140,40,40)

        grid_btn  = Button(f"Grid:  {'ON' if s['grid']  else 'OFF'}", cx, 150, W, grid_col)
        snd_btn   = Button(f"Sound: {'ON' if s['sound'] else 'OFF'}", cx, 206, W, snd_col)
        col_btn   = Button(f"Color: {_COLOR_OPTIONS[col_idx][0]}", cx, 262, W, s_col)
        back_btn  = Button("✓ Save & Back", cx, 340, W, (70,70,120))

        _draw_bg()
        _title("SETTINGS", 70)
        # Snake preview
        px = WIDTH//2 - CELL; py = 118
        pygame.draw.rect(screen, s_col, (px, py, CELL*2, CELL), border_radius=4)

        for btn in [grid_btn, snd_btn, col_btn, back_btn]: btn.draw()
        _sub("Changes applied on Save", HEIGHT - 28)
        pygame.display.flip()
        clock.tick(BASE_FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if grid_btn.clicked(ev):  s["grid"]  = not s["grid"]
            if snd_btn.clicked(ev):   s["sound"] = not s["sound"]
            if col_btn.clicked(ev):
                col_idx = (col_idx + 1) % len(_COLOR_OPTIONS)
                s["snake_color"] = _COLOR_OPTIONS[col_idx][1]
            if back_btn.clicked(ev):
                save_settings(s)
                return s
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                save_settings(s)
                return s


# ─────────────────────────────────────────────────────────────────────────────
#  Screen: Leaderboard
# ─────────────────────────────────────────────────────────────────────────────
def screen_leaderboard():
    entries = db.top10()
    back    = Button("← Back", WIDTH//2 - 70, HEIGHT - 58, 140, (70,70,100))

    while True:
        _draw_bg()
        _title("TOP 10", 30)

        hdr = font_tiny.render(
            f"{'#':<3} {'Name':<16} {'Score':>6}  {'Lv':>3}  {'Date'}", True, ACCENT)
        screen.blit(hdr, (14, 88))
        pygame.draw.line(screen, ACCENT, (14, 108), (WIDTH - 14, 108), 1)

        if not entries:
            _sub("No scores yet — play a run!", 200, MUTED)
            _sub("(DB may be offline)", 228, MUTED)
        else:
            for i, e in enumerate(entries):
                row_col = GOLD if i == 0 else (TEXT_COLOR if i < 3 else MUTED)
                txt = f"{e['rank']:<3} {e['username']:<16} {e['score']:>6}  {e['level']:>3}  {e['date']}"
                lbl = font_tiny.render(txt, True, row_col)
                screen.blit(lbl, (14, 116 + i * 26))

        back.draw()
        pygame.display.flip()
        clock.tick(BASE_FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if back.clicked(ev): return
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return


# ─────────────────────────────────────────────────────────────────────────────
#  Screen: Game Over
# ─────────────────────────────────────────────────────────────────────────────
def screen_game_over(username, score, level, pb) -> str:
    """Returns 'retry' | 'menu'."""
    W  = 210; cx = WIDTH//2 - W//2
    r_btn = Button("↺  Retry",    cx, 370, W, (50,150,50))
    m_btn = Button("⌂  Main Menu",cx, 424, W, (80,80,150))

    while True:
        _draw_bg()
        go = font_large.render("GAME OVER", True, RED)
        screen.blit(go, (WIDTH//2 - go.get_width()//2, 70))

        pygame.draw.rect(screen, PANEL_UI, (30, 130, WIDTH-60, 210), border_radius=10)
        pygame.draw.rect(screen, ACCENT,   (30, 130, WIDTH-60, 210), 1, border_radius=10)

        rows = [
            (f"Player : {username}",   TEXT_COLOR),
            (f"Score  : {score}",      GOLD),
            (f"Level  : {level}",      ACCENT),
            (f"Best   : {pb}",         (0, 220, 180)),
        ]
        for i, (txt, col) in enumerate(rows):
            lbl = font_medium.render(txt, True, col)
            screen.blit(lbl, (50, 148 + i*42))

        r_btn.draw(); m_btn.draw()
        pygame.display.flip()
        clock.tick(BASE_FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if r_btn.clicked(ev): return "retry"
            if m_btn.clicked(ev): return "menu"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:      return "retry"
                if ev.key == pygame.K_ESCAPE: return "menu"


# ─────────────────────────────────────────────────────────────────────────────
#  Main game loop
# ─────────────────────────────────────────────────────────────────────────────
def play_game(username: str, settings: dict) -> None:
    head_col = tuple(settings["snake_color"])
    # Derive a darker body color
    body_col = tuple(max(0, c - 60) for c in head_col)

    pb = db.personal_best(username)

    snake       = Snake(color_head=head_col, color_body=body_col)
    normal_food = NormalFood()
    bonus_food  = BonusFood()
    poison_food = PoisonFood()
    obstacles   : set = set()
    powerup     : PowerUp | None = None

    score       = 0
    level       = 1
    food_eaten  = 0
    move_delay  = BASE_MOVE
    frame_count = 0
    show_grid   = settings.get("grid", True)

    # Place starting food
    occ = snake.occupied()
    normal_food.respawn(occ)
    bonus_food.respawn(occ | {normal_food.pos})
    poison_food.respawn(occ | {normal_food.pos, bonus_food.pos})

    # Power-up state
    active_pu    : str | None = None   # kind string
    pu_end_ms    : int = 0             # when effect expires
    pu_spawn_at  : int = 0             # for periodic spawning
    PU_SPAWN_INT = 10_000              # spawn a new PU every 10 s

    # Speed modifiers from power-ups
    base_move_delay = BASE_MOVE

    while True:
        clock.tick(BASE_FPS)
        frame_count += 1
        now = pygame.time.get_ticks()

        # ── Events ────────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP,    pygame.K_w): snake.set_direction( 0,-1)
                if ev.key in (pygame.K_DOWN,  pygame.K_s): snake.set_direction( 0, 1)
                if ev.key in (pygame.K_LEFT,  pygame.K_a): snake.set_direction(-1, 0)
                if ev.key in (pygame.K_RIGHT, pygame.K_d): snake.set_direction( 1, 0)
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # ── Expire active power-up ────────────────────────────────────────────
        if active_pu and now > pu_end_ms:
            move_delay = base_move_delay   # restore speed
            active_pu  = None

        # ── Spawn new power-up periodically ──────────────────────────────────
        if powerup is None and now - pu_spawn_at > PU_SPAWN_INT:
            pu_spawn_at = now
            if random.random() < 0.7:
                occ_now = snake.occupied() | {normal_food.pos, bonus_food.pos,
                                              poison_food.pos} | obstacles
                powerup = PowerUp(occ_now)

        # ── Expire field power-up ─────────────────────────────────────────────
        if powerup and powerup.is_expired():
            powerup = None

        # ── Snake step ────────────────────────────────────────────────────────
        if frame_count % move_delay == 0:
            alive = snake.step(obstacles)
            if not alive:
                _end(username, score, level, pb, settings)
                return

            head = snake.body[0]
            occ  = snake.occupied() | obstacles

            # Eat normal food
            if head == normal_food.pos:
                snake.grow()
                score      += 10 * level
                food_eaten += 1
                normal_food.respawn(occ | {bonus_food.pos, poison_food.pos})
                _level_up_check()

            # Eat bonus food (if still alive on field)
            if head == bonus_food.pos and bonus_food.tick():
                snake.grow()
                score      += 30 * level
                food_eaten += 1
                bonus_food.respawn(occ | {normal_food.pos, poison_food.pos})
                _level_up_check()

            # Eat poison food
            if head == poison_food.pos:
                survived = snake.shrink(2)
                if not survived:
                    _end(username, score, level, pb, settings)
                    return
                score = max(0, score - 5)
                poison_food.respawn(occ | {normal_food.pos, bonus_food.pos})

            # Collect power-up
            if powerup and head == powerup.pos:
                _activate_powerup(powerup.kind)
                powerup = None

        # ── Bonus food timeout ────────────────────────────────────────────────
        if not bonus_food.tick():
            bonus_food.respawn(
                snake.occupied() | {normal_food.pos, poison_food.pos} | obstacles)

        # ── Draw ──────────────────────────────────────────────────────────────
        draw_field(screen, show_grid)
        draw_obstacles(screen, obstacles)
        normal_food.draw(screen)
        bonus_food.draw(screen)
        poison_food.draw(screen)
        if powerup:
            powerup.draw(screen)
        snake.draw(screen)
        draw_hud(screen, score, level, pb, active_pu, pu_end_ms)
        pygame.display.flip()

        # ── Inner helpers (closures) ──────────────────────────────────────────
        def _level_up_check():
            nonlocal food_eaten, level, base_move_delay, move_delay, obstacles
            if food_eaten >= FOOD_PER_LEVEL:
                food_eaten      = 0
                level          += 1
                base_move_delay = max(2, base_move_delay - 1)
                move_delay      = base_move_delay
                # Obstacles from level 3
                if level >= 3:
                    obstacles = generate_obstacles(level, snake.body)

        def _activate_powerup(kind: str):
            nonlocal active_pu, pu_end_ms, move_delay
            active_pu = kind
            pu_end_ms = pygame.time.get_ticks() + POWERUP_DURATION
            if kind == "speed":
                move_delay = max(1, base_move_delay - 3)
            elif kind == "slow":
                move_delay = base_move_delay + 4
            elif kind == "shield":
                snake.shield_active = True


def _end(username: str, score: int, level: int, pb: int, settings: dict):
    """Save to DB then show game-over screen."""
    db.save_session(username, score, level)
    new_pb = db.personal_best(username) or max(pb, score)
    result = screen_game_over(username, score, level, new_pb)
    if result == "retry":
        play_game(username, settings)


# ─────────────────────────────────────────────────────────────────────────────
#  App entry
# ─────────────────────────────────────────────────────────────────────────────
def app():
    db.ensure_schema()          # create tables if needed (no-op if DB offline)
    settings = load_settings()
    username = screen_name_entry()

    while True:
        action = screen_main_menu(username, settings)
        if action == "play":
            play_game(username, settings)
        elif action == "leaderboard":
            screen_leaderboard()
        elif action == "settings":
            settings = screen_settings(settings)
        elif action == "quit":
            pygame.quit(); sys.exit()


if __name__ == "__main__":
    app()