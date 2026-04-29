"""
game.py — All gameplay objects and drawing helpers.

Classes:  Snake, NormalFood, BonusFood, PoisonFood, PowerUp, Obstacle
Helpers:  free_cells(), draw_field(), draw_hud(), draw_powerup_hud()
"""

import pygame
import random
import math

from config import (
    CELL, COLS, ROWS, PANEL_H, WIDTH, HEIGHT,
    BASE_FPS, BASE_MOVE,
    BG_COLOR, GRID_COLOR, WALL_COLOR, PANEL_COLOR, TEXT_COLOR,
    MUTED, GOLD, RED, ACCENT, GREEN_LT, GREEN_DK, GREEN_OL,
    FOOD_NORMAL_FILL, FOOD_NORMAL_SHINE,
    FOOD_BONUS_FILL, FOOD_BONUS_SHINE,
    FOOD_POISON_FILL, FOOD_POISON_SHINE,
    PU_SPEED_COL, PU_SLOW_COL, PU_SHIELD_COL,
    OBSTACLE_COLOR, OBSTACLE_BORDER,
    POWERUP_FIELD_LIFE,
    cell_to_px,
)

# ── Fonts (created lazily so this module can be imported before pygame.init) ──
import os as _os, sys as _sys

def _find_unicode_font(bold=False):
    """Find a font that supports Cyrillic/Kazakh on Linux, macOS, and Windows."""
    candidates_linux = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]
    candidates_win = [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    candidates_mac = [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates_linux + candidates_win + candidates_mac:
        if _os.path.exists(path):
            return path
    return None  # fall back to pygame default

_fonts: dict = {}

def _font(key):
    if not _fonts:
        reg  = _find_unicode_font(bold=False)
        bold = _find_unicode_font(bold=True)
        _fonts["large"]  = pygame.font.Font(bold, 40)
        _fonts["medium"] = pygame.font.Font(bold, 24)
        _fonts["small"]  = pygame.font.Font(reg,  18)
        _fonts["tiny"]   = pygame.font.Font(reg,  13)
    return _fonts[key]


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def free_cells(occupied: set) -> list[tuple]:
    """All grid cells not in `occupied`."""
    return [
        (c, r) for c in range(COLS) for r in range(ROWS)
        if (c, r) not in occupied
    ]


def _random_free(occupied: set):
    fc = free_cells(occupied)
    return random.choice(fc) if fc else None


# ─────────────────────────────────────────────────────────────────────────────
#  Snake
# ─────────────────────────────────────────────────────────────────────────────
class Snake:
    def __init__(self, color_head=GREEN_LT, color_body=GREEN_DK):
        self.color_head   = color_head
        self.color_body   = color_body
        self.shield_active = False
        self.reset()

    def reset(self):
        cx, cy          = COLS // 2, ROWS // 2
        self.body       = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction  = (1, 0)
        self.next_dir   = (1, 0)
        self.grew       = False

    def set_direction(self, dx, dy):
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.next_dir = (dx, dy)

    def step(self, obstacles: set = frozenset()) -> bool:
        self.direction = self.next_dir
        hx, hy = self.body[0]
        new_head = (hx + self.direction[0], hy + self.direction[1])

        # Wall collision
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            if self.shield_active:
                self.shield_active = False
                return True        # shield absorbs wall hit
            return False

        # Self collision
        if new_head in self.body:
            if self.shield_active:
                self.shield_active = False
                return True
            return False

        # Obstacle collision
        if new_head in obstacles:
            if self.shield_active:
                self.shield_active = False
                return True
            return False

        self.body.insert(0, new_head)
        if self.grew:
            self.grew = False
        else:
            self.body.pop()
        return True

    def grow(self):
        self.grew = True

    def shrink(self, amount: int = 2) -> bool:
        """Remove `amount` tail segments. Returns False if snake is too short."""
        for _ in range(amount):
            if len(self.body) <= 1:
                return False
            self.body.pop()
        return True

    def occupied(self) -> set:
        return set(self.body)

    def draw(self, surface):
        shield_pulse = self.shield_active and (pygame.time.get_ticks() // 300) % 2 == 0
        for i, (col, row) in enumerate(self.body):
            px, py = cell_to_px(col, row)
            col_c  = self.color_head if i == 0 else self.color_body
            pygame.draw.rect(surface, col_c,
                             (px+1, py+1, CELL-2, CELL-2), border_radius=4)
            outline = PU_SHIELD_COL if (i == 0 and shield_pulse) else GREEN_OL
            pygame.draw.rect(surface, outline,
                             (px+1, py+1, CELL-2, CELL-2), 1, border_radius=4)
            if i == 0:
                self._draw_eyes(surface, px, py)

    def _draw_eyes(self, surface, px, py):
        offsets = {
            ( 1, 0): [(12,5),(12,13)],
            (-1, 0): [(5, 5),(5, 13)],
            (0, -1): [(5, 5),(13, 5)],
            (0,  1): [(5,13),(13,13)],
        }
        for ex, ey in offsets.get(self.direction, [(5,5),(13,5)]):
            pygame.draw.circle(surface, TEXT_COLOR, (px+ex, py+ey), 3)
            pygame.draw.circle(surface, BG_COLOR,   (px+ex, py+ey), 1)


# ─────────────────────────────────────────────────────────────────────────────
#  Food variants
# ─────────────────────────────────────────────────────────────────────────────
class _BaseFood:
    def __init__(self):
        self.pos = (0, 0)

    def respawn(self, occupied: set):
        pos = _random_free(occupied)
        if pos:
            self.pos = pos

    def draw(self, surface): ...


class NormalFood(_BaseFood):
    """Standard food: worth 1 unit."""
    value = 1

    def draw(self, surface):
        col, row = self.pos
        px, py   = cell_to_px(col, row)
        cx, cy   = px + CELL//2, py + CELL//2
        r        = CELL//2 - 2
        pygame.draw.circle(surface, FOOD_NORMAL_FILL,  (cx, cy), r)
        pygame.draw.circle(surface, FOOD_NORMAL_SHINE, (cx-3, cy-3), 4)


class BonusFood(_BaseFood):
    """
    High-value food (worth 3 units) that disappears after a timeout.
    Call .tick() every frame; returns False when expired.
    """
    value   = 3
    TIMEOUT = 5_000   # ms

    def __init__(self):
        super().__init__()
        self._spawned_at = 0

    def respawn(self, occupied: set):
        super().respawn(occupied)
        self._spawned_at = pygame.time.get_ticks()

    def tick(self) -> bool:
        """Return True while still alive."""
        return pygame.time.get_ticks() - self._spawned_at < self.TIMEOUT

    def draw(self, surface):
        col, row = self.pos
        px, py   = cell_to_px(col, row)
        cx, cy   = px + CELL//2, py + CELL//2
        r        = CELL//2 - 2
        # Blink in last second
        elapsed = pygame.time.get_ticks() - self._spawned_at
        if elapsed > self.TIMEOUT - 1000 and (elapsed // 200) % 2:
            return
        pygame.draw.circle(surface, FOOD_BONUS_FILL,  (cx, cy), r)
        pygame.draw.circle(surface, FOOD_BONUS_SHINE, (cx-3, cy-3), 4)
        star = _font("tiny").render("★", True, (255, 160, 0))
        surface.blit(star, (cx - star.get_width()//2, cy - star.get_height()//2))


class PoisonFood(_BaseFood):
    """
    Poison: shortens the snake by 2; game over if length ≤ 1.
    """
    value = -2   # negative = shrink amount

    def draw(self, surface):
        col, row = self.pos
        px, py   = cell_to_px(col, row)
        cx, cy   = px + CELL//2, py + CELL//2
        r        = CELL//2 - 2
        pygame.draw.circle(surface, FOOD_POISON_FILL,  (cx, cy), r)
        pygame.draw.circle(surface, FOOD_POISON_SHINE, (cx, cy), r, 2)
        skull = _font("tiny").render("☠", True, FOOD_POISON_SHINE)
        surface.blit(skull, (cx - skull.get_width()//2, cy - skull.get_height()//2))


# ─────────────────────────────────────────────────────────────────────────────
#  Power-ups
# ─────────────────────────────────────────────────────────────────────────────
PU_KINDS = {
    "speed":  (PU_SPEED_COL,  "⚡", "Speed+"),
    "slow":   (PU_SLOW_COL,   "❄",  "Slow"),
    "shield": (PU_SHIELD_COL, "🛡",  "Shield"),
}

class PowerUp:
    def __init__(self, occupied: set):
        self.kind = random.choice(list(PU_KINDS.keys()))
        self.color, self.icon, self.label = PU_KINDS[self.kind]
        pos = _random_free(occupied)
        self.pos = pos if pos else (0, 0)
        self._spawned_at = pygame.time.get_ticks()

    def is_expired(self) -> bool:
        return pygame.time.get_ticks() - self._spawned_at > POWERUP_FIELD_LIFE

    def draw(self, surface):
        col, row = self.pos
        px, py   = cell_to_px(col, row)
        cx, cy   = px + CELL//2, py + CELL//2
        # Pulsing ring
        t   = pygame.time.get_ticks() / 400
        r   = CELL//2 - 1 + int(math.sin(t) * 2)
        pygame.draw.circle(surface, self.color, (cx, cy), r)
        pygame.draw.circle(surface, (255,255,255), (cx, cy), r, 1)
        lbl = _font("tiny").render(self.icon, True, BG_COLOR)
        surface.blit(lbl, (cx - lbl.get_width()//2, cy - lbl.get_height()//2))


# ─────────────────────────────────────────────────────────────────────────────
#  Obstacles
# ─────────────────────────────────────────────────────────────────────────────
def generate_obstacles(level: int, snake_body: list) -> set:
    """
    Place (level - 2) * 2 obstacle blocks, none adjacent to the snake's head.
    Returns a set of (col, row) positions.
    """
    count    = (level - 2) * 2          # 2 blocks at L3, 4 at L4, etc.
    head_set = set(snake_body[:5])      # keep zone near head clear
    forbidden = set(snake_body) | head_set
    pool = [
        (c, r) for c in range(COLS) for r in range(ROWS)
        if (c, r) not in forbidden
    ]
    random.shuffle(pool)
    return set(pool[:count])


def draw_obstacles(surface, obstacles: set):
    for col, row in obstacles:
        px, py = cell_to_px(col, row)
        pygame.draw.rect(surface, OBSTACLE_COLOR,
                         (px+1, py+1, CELL-2, CELL-2), border_radius=3)
        pygame.draw.rect(surface, OBSTACLE_BORDER,
                         (px+1, py+1, CELL-2, CELL-2), 1, border_radius=3)


# ─────────────────────────────────────────────────────────────────────────────
#  Drawing helpers
# ─────────────────────────────────────────────────────────────────────────────
def draw_field(surface, show_grid: bool = True):
    pygame.draw.rect(surface, BG_COLOR, (0, PANEL_H, WIDTH, HEIGHT - PANEL_H))
    if show_grid:
        for col in range(COLS):
            for row in range(ROWS):
                px, py = cell_to_px(col, row)
                pygame.draw.rect(surface, GRID_COLOR, (px, py, CELL, CELL), 1)
    pygame.draw.rect(surface, WALL_COLOR, (0, PANEL_H, WIDTH, HEIGHT - PANEL_H), 3)


def draw_hud(surface, score: int, level: int, personal_best: int,
             active_pu: str | None, pu_end_ms: int):
    pygame.draw.rect(surface, PANEL_COLOR, (0, 0, WIDTH, PANEL_H))
    pygame.draw.line(surface, WALL_COLOR, (0, PANEL_H), (WIDTH, PANEL_H), 2)

    sc  = _font("medium").render(f"Score:{score}", True, GOLD)
    lv  = _font("medium").render(f"Lv:{level}",   True, ACCENT)
    pb  = _font("small").render(f"Best:{personal_best}", True, MUTED)
    surface.blit(sc,  (6,  4))
    surface.blit(lv,  (WIDTH//2 - lv.get_width()//2, 4))
    surface.blit(pb,  (WIDTH - pb.get_width() - 6, 4))

    # Active power-up badge
    if active_pu and active_pu in PU_KINDS:
        remaining = max(0, (pu_end_ms - pygame.time.get_ticks()) // 1000)
        col_, icon, label = PU_KINDS[active_pu]
        badge = _font("small").render(f"{icon} {label} {remaining}s", True, col_)
        surface.blit(badge, (WIDTH//2 - badge.get_width()//2, 32))