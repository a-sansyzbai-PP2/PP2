import pygame
import random
import sys

# Initialize pygame and set up constants, colors, and the screen
pygame.init()


CELL      = 20          # size of one cell in pixels
COLS      = 25          # number of columns in the game field
ROWS      = 25          # number of rows in the game field
PANEL_H   = 50          # height of the top panel with HUD
WIDTH     = COLS * CELL
HEIGHT    = ROWS * CELL + PANEL_H

# Colors
BG_COLOR      = ( 15,  15,  15)
GRID_COLOR    = ( 30,  30,  30)
SNAKE_HEAD    = ( 50, 220,  50)
SNAKE_BODY    = ( 30, 160,  30)
SNAKE_OUTLINE = ( 10,  90,  10)
FOOD_COLOR    = (220,  50,  50)
FOOD_SHINE    = (255, 120, 120)
WALL_COLOR    = ( 80,  80,  80)
TEXT_COLOR    = (255, 255, 255)
GOLD          = (255, 215,   0)
RED           = (220,  30,  30)

# Initial speed (frames per second for snake movement)
BASE_FPS  = 60
BASE_MOVE = 8    # number of frames between snake steps (the smaller the faster)

# Points for food to advance to the next level
FOOD_PER_LEVEL = 4

# Setting up the screen and fonts
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock  = pygame.time.Clock()

font_large  = pygame.font.SysFont("Consolas", 40, bold=True)
font_medium = pygame.font.SysFont("Consolas", 24, bold=True)
font_small  = pygame.font.SysFont("Consolas", 18)


# Helper function: Convert cell coordinates to pixel coordinates
def cell_to_px(col, row):
    """Converts cell coordinates to pixels with panel offset."""
    return col * CELL, row * CELL + PANEL_H


class Snake:
    """Snake: list of segments (col, row) + direction."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Starting position — center of the field, length 3."""
        cx, cy        = COLS // 2, ROWS // 2
        self.body     = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)   # движение вправо
        self.next_dir  = (1, 0)
        self.grew      = False    # флаг роста (чтобы не удалять хвост)

    def set_direction(self, dx, dy):
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.next_dir = (dx, dy)

    def step(self):
        self.direction = self.next_dir
        head_x, head_y = self.body[0]
        new_head = (head_x + self.direction[0],
                    head_y + self.direction[1])

        # Check for collision with walls
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            return False   # столкновение со стеной

        # Check for collision with itself
        if new_head in self.body:
            return False

        self.body.insert(0, new_head)

        if self.grew:
            self.grew = False  # not removing tail this turn
        else:
            self.body.pop()    # remove tail segment

        return True

    def grow(self):
        self.grew = True

    def draw(self, surface):
        """Draw the snake: head is brighter, body is darker, with an outline."""
        for i, (col, row) in enumerate(self.body):
            px, py = cell_to_px(col, row)
            color  = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(surface, color,
                             (px + 1, py + 1, CELL - 2, CELL - 2),
                             border_radius=4)
            pygame.draw.rect(surface, SNAKE_OUTLINE,
                             (px + 1, py + 1, CELL - 2, CELL - 2),
                             1, border_radius=4)
            # Draw eyes on the head
            if i == 0:
                self._draw_eyes(surface, px, py)

    def _draw_eyes(self, surface, px, py):
        """Draw eyes on the head of the snake depending on its direction."""
        dx, dy = self.direction
        # Offsets for eye positions based on direction
        offsets = {
            ( 1,  0): [(12, 5),  (12, 13)],   # вправо
            (-1,  0): [(5,  5),  (5,  13)],   # влево
            ( 0, -1): [(5,  5),  (13,  5)],   # вверх
            ( 0,  1): [(5, 13),  (13, 13)],   # вниз
        }
        for ex, ey in offsets.get((dx, dy), [(5, 5), (13, 5)]):
            pygame.draw.circle(surface, TEXT_COLOR, (px + ex, py + ey), 3)
            pygame.draw.circle(surface, BG_COLOR,   (px + ex, py + ey), 1)


class Food:
    """Food: random position, does not intersect with the snake or walls."""

    def __init__(self):
        self.pos = (0, 0)

    def respawn(self, snake_body):
        """Generate a new position, free from the snake's body."""
        free_cells = [
            (c, r)
            for c in range(COLS)
            for r in range(ROWS)
            if (c, r) not in snake_body
        ]
        if free_cells:
            self.pos = random.choice(free_cells)

    def draw(self, surface):
        col, row  = self.pos
        px, py    = cell_to_px(col, row)
        cx, cy    = px + CELL // 2, py + CELL // 2
        r         = CELL // 2 - 2
        pygame.draw.circle(surface, FOOD_COLOR, (cx, cy), r)
        pygame.draw.circle(surface, FOOD_SHINE, (cx - 3, cy - 3), 4)


# Drawing functions
def draw_field(surface):
    """Draw the game field (grid)."""
    # Field background
    pygame.draw.rect(surface, BG_COLOR,
                     (0, PANEL_H, WIDTH, HEIGHT - PANEL_H))

    # Grid lines
    for col in range(COLS):
        for row in range(ROWS):
            px, py = cell_to_px(col, row)
            pygame.draw.rect(surface, GRID_COLOR,
                             (px, py, CELL, CELL), 1)

    # Field border
    pygame.draw.rect(surface, WALL_COLOR,
                     (0, PANEL_H, WIDTH, HEIGHT - PANEL_H), 3)


# HUD and end screen
def draw_hud(surface, score, level):
    """Верхняя панель: очки и уровень."""
    pygame.draw.rect(surface, (20, 20, 40), (0, 0, WIDTH, PANEL_H))
    pygame.draw.line(surface, WALL_COLOR, (0, PANEL_H), (WIDTH, PANEL_H), 2)

    score_lbl = font_medium.render(f"Score: {score}", True, GOLD)
    level_lbl = font_medium.render(f"Level: {level}", True, (100, 200, 255))

    surface.blit(score_lbl, (10, PANEL_H // 2 - score_lbl.get_height() // 2))
    surface.blit(level_lbl, (WIDTH - level_lbl.get_width() - 10,
                              PANEL_H // 2 - level_lbl.get_height() // 2))


# End screen with options to restart or quit
def end_screen(score, level):
    """Show game over screen with final score and level, and options to restart or quit."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    lines = [
        (font_large,  "GAME OVER",           RED),
        (font_medium, f"Score: {score}",     GOLD),
        (font_medium, f"Level: {level}",     (100, 200, 255)),
        (font_small,  "R — restart  ESC — quit", TEXT_COLOR),
    ]
    total_h = sum(f.get_height() + 10 for f, _, _ in lines)
    y = HEIGHT // 2 - total_h // 2

    for fnt, text, color in lines:
        lbl = fnt.render(text, True, color)
        screen.blit(lbl, (WIDTH // 2 - lbl.get_width() // 2, y))
        y += lbl.get_height() + 10

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
        clock.tick(30)