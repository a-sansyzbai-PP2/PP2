"""
config.py — Shared constants, colors, and grid helpers.
Import this everywhere instead of duplicating magic numbers.
"""

import pygame

# ── Grid ──────────────────────────────────────────────────────────────────────
CELL      = 20
COLS      = 25
ROWS      = 25
PANEL_H   = 56          # top HUD bar height
WIDTH     = COLS * CELL
HEIGHT    = ROWS * CELL + PANEL_H

# ── Timing ────────────────────────────────────────────────────────────────────
BASE_FPS       = 60
BASE_MOVE      = 8      # frames between snake steps (lower = faster)
FOOD_PER_LEVEL = 4      # food items needed to level up

# ── Power-up durations (ms) ───────────────────────────────────────────────────
POWERUP_DURATION   = 5_000   # effect lasts 5 s
POWERUP_FIELD_LIFE = 8_000   # disappears from field after 8 s

# ── Colors ────────────────────────────────────────────────────────────────────
BG_COLOR        = ( 15,  15,  15)
GRID_COLOR      = ( 30,  30,  30)
WALL_COLOR      = ( 80,  80,  80)
PANEL_COLOR     = ( 20,  20,  40)
TEXT_COLOR      = (255, 255, 255)
MUTED           = (120, 120, 140)
GOLD            = (255, 215,   0)
RED             = (220,  30,  30)
ACCENT          = ( 72, 144, 240)
GREEN_LT        = ( 50, 220,  50)
GREEN_DK        = ( 30, 160,  30)
GREEN_OL        = ( 10,  90,  10)

# Food colors
FOOD_NORMAL_FILL  = (220,  50,  50)
FOOD_NORMAL_SHINE = (255, 120, 120)
FOOD_BONUS_FILL   = (255, 215,   0)   # gold — high-value, disappears fast
FOOD_BONUS_SHINE  = (255, 255, 160)
FOOD_POISON_FILL  = ( 90,   0,  20)   # dark red
FOOD_POISON_SHINE = (160,  40,  40)

# Power-up colors
PU_SPEED_COL  = (  0, 220, 180)   # teal  — speed boost
PU_SLOW_COL   = (180,  80, 255)   # violet — slow motion
PU_SHIELD_COL = ( 80, 160, 255)   # blue   — shield

# Obstacle
OBSTACLE_COLOR  = (100,  60,  20)
OBSTACLE_BORDER = (160, 100,  40)


def cell_to_px(col: int, row: int) -> tuple[int, int]:
    return col * CELL, row * CELL + PANEL_H