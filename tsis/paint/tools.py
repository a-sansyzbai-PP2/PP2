"""
tools.py  —  constants, UI helpers, tool definitions, flood-fill
All pygame globals are initialised here so paint.py just imports them.
"""

import pygame
import sys
import collections

# ─────────────────────────────────────────────────────────────
#  Initialisation
# ─────────────────────────────────────────────────────────────
pygame.init()

SCREEN_W  = 950
SCREEN_H  = 680
TOOLBAR_H = 64          # two-row toolbar

BG_CANVAS   = (255, 255, 255)
BG_TOOLBAR  = ( 30,  30,  40)
HIGHLIGHT   = ( 72, 140, 230)
BORDER_CLR  = ( 90,  90, 100)
TEXT_COLOR  = (220, 220, 220)
SIZE_ACTIVE = ( 60, 200, 120)

# 18-colour palette
PALETTE = [
    (  0,   0,   0), (255, 255, 255), (128, 128, 128), (192, 192, 192),
    (255,   0,   0), (128,   0,   0), (255, 128,   0), (128,  64,   0),
    (255, 255,   0), (128, 128,   0), (  0, 255,   0), (  0, 128,   0),
    (  0, 255, 255), (  0, 128, 128), (  0,   0, 255), (  0,   0, 128),
    (255,   0, 255), (128,   0, 128),
]

# Tool IDs
TOOL_PEN      = "pen"
TOOL_LINE     = "line"
TOOL_RECT     = "rect"
TOOL_CIRCLE   = "circle"
TOOL_ERASER   = "eraser"
TOOL_FILL     = "fill"
TOOL_TEXT     = "text"
TOOL_SQUARE   = "square"
TOOL_RTRIANGLE  = "rtriangle"
TOOL_ETRIANGLE  = "etriangle"
TOOL_RHOMBUS  = "rhombus"

# ─────────────────────────────────────────────────────────────
#  Window / surfaces
# ─────────────────────────────────────────────────────────────
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Paint Pro — Extended")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 14, bold=True)

canvas = pygame.Surface((SCREEN_W, SCREEN_H - TOOLBAR_H))
canvas.fill(BG_CANVAS)

# ─────────────────────────────────────────────────────────────
#  Fixed toolbar widgets
# ─────────────────────────────────────────────────────────────
# Brush-size preset buttons (label, px-value, rect)
_SZ_X = 300
size_btns = [
    (2,  pygame.Rect(_SZ_X,      36, 36, 20)),   # Small  — key 1
    (5,  pygame.Rect(_SZ_X + 40, 36, 36, 20)),   # Medium — key 2
    (10, pygame.Rect(_SZ_X + 80, 36, 36, 20)),   # Large  — key 3
]

plus_rect  = pygame.Rect(300,  8, 28, 22)
minus_rect = pygame.Rect(332,  8, 28, 22)
clear_rect = pygame.Rect(SCREEN_W - 80, 15, 70, 34)


# ─────────────────────────────────────────────────────────────
#  ToolButton class
# ─────────────────────────────────────────────────────────────
class ToolButton:
    def __init__(self, x, y, w, h, label, tool_id):
        self.rect    = pygame.Rect(x, y, w, h)
        self.label   = label
        self.tool_id = tool_id

    def draw(self, surface, active_tool):
        color = HIGHLIGHT if self.tool_id == active_tool else BG_TOOLBAR
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, BORDER_CLR, self.rect, 1, border_radius=5)
        lbl = font.render(self.label, True, TEXT_COLOR)
        surface.blit(lbl, (self.rect.centerx - lbl.get_width()  // 2,
                           self.rect.centery - lbl.get_height() // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ─────────────────────────────────────────────────────────────
#  draw_toolbar
# ─────────────────────────────────────────────────────────────
def draw_toolbar(surface, tool_buttons, cur_tool, cur_color, cur_size, palette_rects):
    pygame.draw.rect(surface, BG_TOOLBAR, (0, 0, SCREEN_W, TOOLBAR_H))

    for btn in tool_buttons:
        btn.draw(surface, cur_tool)

    # Color swatch
    cr = pygame.Rect(440, 10, 14, 44)
    pygame.draw.rect(surface, cur_color, cr, border_radius=3)
    pygame.draw.rect(surface, TEXT_COLOR, cr, 2, border_radius=3)

    # + / − size buttons
    pygame.draw.rect(surface, BORDER_CLR, plus_rect,  border_radius=4)
    pygame.draw.rect(surface, BORDER_CLR, minus_rect, border_radius=4)
    surface.blit(font.render("+", True, TEXT_COLOR),
                 (plus_rect.centerx  - 4, plus_rect.centery  - 8))
    surface.blit(font.render("−", True, TEXT_COLOR),
                 (minus_rect.centerx - 4, minus_rect.centery - 8))

    # Size presets S / M / L
    labels = {2: "S", 5: "M", 10: "L"}
    for sz, rect in size_btns:
        active = abs(cur_size - sz) < 2
        col    = SIZE_ACTIVE if active else BORDER_CLR
        pygame.draw.rect(surface, col, rect, border_radius=4)
        lbl = font.render(labels[sz], True, TEXT_COLOR)
        surface.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                           rect.centery - lbl.get_height() // 2))

    # Current size number
    sz_lbl = font.render(f"sz:{cur_size}", True, TEXT_COLOR)
    surface.blit(sz_lbl, (300, 10))

    # Palette
    for idx, rect in enumerate(palette_rects):
        pygame.draw.rect(surface, PALETTE[idx], rect, border_radius=3)
        pygame.draw.rect(surface, BORDER_CLR,   rect, 1, border_radius=3)

    # Clear button
    pygame.draw.rect(surface, (180, 40, 40), clear_rect, border_radius=6)
    surface.blit(font.render("Clear", True, TEXT_COLOR),
                 (clear_rect.centerx - 18, clear_rect.centery - 8))

    # Help hints
    hint = font.render("1/2/3 = S/M/L size   Ctrl+S = save PNG", True, (120, 120, 130))
    surface.blit(hint, (SCREEN_W - hint.get_width() - 84, 50))


# ─────────────────────────────────────────────────────────────
#  Coordinate helper
# ─────────────────────────────────────────────────────────────
def to_canvas(x, y):
    """Screen → canvas coordinates."""
    return x, y - TOOLBAR_H


# ─────────────────────────────────────────────────────────────
#  Flood-fill  (BFS, pixel-exact)
# ─────────────────────────────────────────────────────────────
def flood_fill(surface: pygame.Surface, pos: tuple, new_color: tuple):
    """
    BFS flood-fill on a pygame.Surface.
    Fills the connected region of identical colour around `pos`
    with `new_color`. Exact colour match (no tolerance).
    """
    x0, y0 = int(pos[0]), int(pos[1])
    w, h   = surface.get_size()

    if not (0 <= x0 < w and 0 <= y0 < h):
        return

    # Normalise colours to RGB (drop alpha if present)
    target = surface.get_at((x0, y0))[:3]
    fill   = new_color[:3]

    if target == fill:
        return                          # nothing to do

    # Lock surface for direct pixel access
    surface.lock()
    queue = collections.deque()
    queue.append((x0, y0))
    visited = set()
    visited.add((x0, y0))

    while queue:
        cx, cy = queue.popleft()
        surface.set_at((cx, cy), fill)

        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = cx + dx, cy + dy
            if (0 <= nx < w and 0 <= ny < h
                    and (nx, ny) not in visited
                    and surface.get_at((nx, ny))[:3] == target):
                visited.add((nx, ny))
                queue.append((nx, ny))

    surface.unlock()