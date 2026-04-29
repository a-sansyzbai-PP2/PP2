import pygame
import random
import sys

# Инициализация pygame
pygame.init()

CELL      = 20          # размер одной клетки в пикселях
COLS      = 25          # количество столбцов игрового поля
ROWS      = 25          # количество строк игрового поля
PANEL_H   = 50          # высота верхней панели (HUD)
WIDTH     = COLS * CELL
HEIGHT    = ROWS * CELL + PANEL_H

# Цвета
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
ORANGE        = (255, 140,   0)
PURPLE        = (180,  50, 220)
CYAN          = ( 50, 220, 200)
SILVER        = (200, 200, 200)

# Начальная скорость змейки
BASE_FPS  = 60
BASE_MOVE = 8    # кадров между шагами змейки (меньше — быстрее)

# Сколько еды нужно съесть для перехода на следующий уровень
FOOD_PER_LEVEL = 4

# ─── Типы еды с весами ────────────────────────────────────────────────────────
#
# weight  — относительная вероятность появления (чем больше, тем чаще)
# value   — очки, которые даёт данная еда
# color   — цвет круга
# shine   — цвет блика
# label   — символ в центре (None = нет)
# lifetime — время жизни в секундах (None = не исчезает)
#
FOOD_TYPES = [
    {
        "weight":   60,
        "value":    10,
        "color":    FOOD_COLOR,
        "shine":    FOOD_SHINE,
        "label":    None,
        "lifetime": None,       # обычная еда — не исчезает
    },
    {
        "weight":   25,
        "value":    30,
        "color":    GOLD,
        "shine":    (255, 240, 100),
        "label":    "★",        # золотая еда — исчезает через 5 сек
        "lifetime": 5,
    },
    {
        "weight":   10,
        "value":    50,
        "color":    PURPLE,
        "shine":    (220, 130, 255),
        "label":    "♦",        # фиолетовая — исчезает через 3 сек
        "lifetime": 3,
    },
    {
        "weight":    5,
        "value":   100,
        "color":    CYAN,
        "shine":    (150, 255, 240),
        "label":    "✦",        # бонусная — исчезает через 2 сек
        "lifetime": 2,
    },
]

_FOOD_WEIGHTS = [t["weight"] for t in FOOD_TYPES]  # веса для взвешенной выборки

# Настройка экрана и шрифтов
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock  = pygame.time.Clock()

font_large  = pygame.font.SysFont("Consolas", 40, bold=True)
font_medium = pygame.font.SysFont("Consolas", 24, bold=True)
font_small  = pygame.font.SysFont("Consolas", 18)


def cell_to_px(col, row):
    """Переводит координаты клетки в пиксели с учётом отступа панели."""
    return col * CELL, row * CELL + PANEL_H


class Snake:
    """Змейка: список сегментов (col, row) + направление движения."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Начальная позиция — центр поля, длина 3."""
        cx, cy         = COLS // 2, ROWS // 2
        self.body      = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)   # движение вправо
        self.next_dir  = (1, 0)
        self.grew      = False    # флаг роста (хвост не удаляем при росте)

    def set_direction(self, dx, dy):
        """Меняет направление, если оно не является противоположным текущему."""
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.next_dir = (dx, dy)

    def step(self):
        """Делает один шаг: двигает змейку, проверяет коллизии.
        Возвращает False при столкновении (смерть), иначе True."""
        self.direction = self.next_dir
        head_x, head_y = self.body[0]
        new_head = (head_x + self.direction[0],
                    head_y + self.direction[1])

        # Столкновение со стеной
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            return False

        # Столкновение с собой
        if new_head in self.body:
            return False

        self.body.insert(0, new_head)

        if self.grew:
            self.grew = False   # в этом шаге хвост не удаляем
        else:
            self.body.pop()     # удаляем хвостовой сегмент

        return True

    def grow(self):
        """Помечает, что в следующем шаге змейка вырастет на 1."""
        self.grew = True

    def draw(self, surface):
        """Рисует змейку: голова ярче, тело темнее, с обводкой и глазами."""
        for i, (col, row) in enumerate(self.body):
            px, py = cell_to_px(col, row)
            color  = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(surface, color,
                             (px + 1, py + 1, CELL - 2, CELL - 2),
                             border_radius=4)
            pygame.draw.rect(surface, SNAKE_OUTLINE,
                             (px + 1, py + 1, CELL - 2, CELL - 2),
                             1, border_radius=4)
            if i == 0:
                self._draw_eyes(surface, px, py)

    def _draw_eyes(self, surface, px, py):
        """Рисует глаза на голове в зависимости от направления движения."""
        dx, dy = self.direction
        offsets = {
            ( 1,  0): [(12, 5),  (12, 13)],
            (-1,  0): [(5,  5),  (5,  13)],
            ( 0, -1): [(5,  5),  (13,  5)],
            ( 0,  1): [(5, 13),  (13, 13)],
        }
        for ex, ey in offsets.get((dx, dy), [(5, 5), (13, 5)]):
            pygame.draw.circle(surface, TEXT_COLOR, (px + ex, py + ey), 3)
            pygame.draw.circle(surface, BG_COLOR,   (px + ex, py + ey), 1)


class Food:
    """Еда: случайный тип (по весам), может исчезать по таймеру."""

    RADIUS = CELL // 2 - 2   # радиус круга еды

    def __init__(self):
        self.pos      = (0, 0)
        self.ftype    = FOOD_TYPES[0]   # тип (будет задан в respawn)
        self.born_at  = 0               # время появления (pygame.time.get_ticks)
        self.lifetime = None            # время жизни в секундах (None = бессмертная)

    def respawn(self, snake_body):
        """Выбирает случайный тип по весам и случайную свободную клетку."""
        # Взвешенная выборка типа еды
        self.ftype    = random.choices(FOOD_TYPES, weights=_FOOD_WEIGHTS, k=1)[0]
        self.born_at  = pygame.time.get_ticks()
        self.lifetime = self.ftype["lifetime"]  # None или количество секунд

        # Случайная свободная клетка
        free_cells = [
            (c, r)
            for c in range(COLS)
            for r in range(ROWS)
            if (c, r) not in snake_body
        ]
        if free_cells:
            self.pos = random.choice(free_cells)

    def is_expired(self):
        """Возвращает True, если еда с таймером исчезла (время вышло)."""
        if self.lifetime is None:
            return False   # бессмертная еда
        elapsed = (pygame.time.get_ticks() - self.born_at) / 1000   # секунды
        return elapsed >= self.lifetime

    def time_left(self):
        """Возвращает оставшееся время жизни в секундах (или None)."""
        if self.lifetime is None:
            return None
        elapsed = (pygame.time.get_ticks() - self.born_at) / 1000
        return max(0.0, self.lifetime - elapsed)

    @property
    def value(self):
        """Очки за эту еду."""
        return self.ftype["value"]

    def draw(self, surface):
        """Рисует еду: цветной круг с бликом, меткой и таймером если нужен."""
        col, row = self.pos
        px, py   = cell_to_px(col, row)
        cx, cy   = px + CELL // 2, py + CELL // 2
        r        = self.RADIUS

        # Мигание за последнюю секунду перед исчезновением
        tl = self.time_left()
        if tl is not None and tl < 1.0:
            # Мигаем с частотой ~4 Гц: видим, если чётная часть 250 мс
            if int(pygame.time.get_ticks() / 125) % 2 == 0:
                return   # не рисуем — эффект мигания

        # Заливка
        pygame.draw.circle(surface, self.ftype["color"], (cx, cy), r)
        # Блик
        pygame.draw.circle(surface, self.ftype["shine"], (cx - 3, cy - 3), 4)

        # Метка типа (если задана)
        if self.ftype["label"]:
            lbl = font_small.render(self.ftype["label"], True, TEXT_COLOR)
            surface.blit(lbl, (cx - lbl.get_width() // 2,
                               cy - lbl.get_height() // 2))

        # Таймер исчезновения: маленький текст под едой
        if tl is not None:
            timer_lbl = font_small.render(f"{tl:.1f}", True, GOLD)
            surface.blit(timer_lbl, (cx - timer_lbl.get_width() // 2,
                                     cy + r + 1))


# ─── Отрисовка поля ───────────────────────────────────────────────────────────

def draw_field(surface):
    """Рисует игровое поле: фон, сетку и рамку."""
    pygame.draw.rect(surface, BG_COLOR,
                     (0, PANEL_H, WIDTH, HEIGHT - PANEL_H))
    for col in range(COLS):
        for row in range(ROWS):
            px, py = cell_to_px(col, row)
            pygame.draw.rect(surface, GRID_COLOR,
                             (px, py, CELL, CELL), 1)
    pygame.draw.rect(surface, WALL_COLOR,
                     (0, PANEL_H, WIDTH, HEIGHT - PANEL_H), 3)


# ─── HUD ──────────────────────────────────────────────────────────────────────

def draw_hud(surface, score, level):
    """Рисует верхнюю панель: счёт и уровень."""
    pygame.draw.rect(surface, (20, 20, 40), (0, 0, WIDTH, PANEL_H))
    pygame.draw.line(surface, WALL_COLOR, (0, PANEL_H), (WIDTH, PANEL_H), 2)

    score_lbl = font_medium.render(f"Score: {score}", True, GOLD)
    level_lbl = font_medium.render(f"Level: {level}", True, (100, 200, 255))

    surface.blit(score_lbl, (10, PANEL_H // 2 - score_lbl.get_height() // 2))
    surface.blit(level_lbl, (WIDTH - level_lbl.get_width() - 10,
                              PANEL_H // 2 - level_lbl.get_height() // 2))


# ─── Экран завершения ─────────────────────────────────────────────────────────

def end_screen(score, level):
    """Показывает экран Game Over. Возвращает True при нажатии R (рестарт)."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    lines = [
        (font_large,  "GAME OVER",               RED),
        (font_medium, f"Score: {score}",          GOLD),
        (font_medium, f"Level: {level}",          (100, 200, 255)),
        (font_small,  "R — restart  ESC — quit",  TEXT_COLOR),
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