import pygame
import random
import sys  # для выхода после quit

# Инициализация pygame и настройка констант, цветов и экрана
pygame.init()

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
FPS           = 60

WHITE   = (255, 255, 255)
BLACK   = (  0,   0,   0)
GRAY    = (100, 100, 100)
DARK    = ( 50,  50,  50)
RED     = (220,  30,  30)
YELLOW  = (255, 215,   0)
GREEN   = ( 30, 200,  30)
BLUE    = ( 30, 100, 220)
ORANGE  = (255, 140,   0)
SILVER  = (192, 192, 192)
GOLD    = (255, 200,   0)
DIAMOND = (100, 220, 255)

# Ширина дороги
ROAD_LEFT  = 60
ROAD_RIGHT = 340

# Создание окна и таймера
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Racer Game")
clock  = pygame.time.Clock()  # для управления частотой кадров

font_large  = pygame.font.SysFont("Arial", 36, bold=True)
font_medium = pygame.font.SysFont("Arial", 24, bold=True)
font_small  = pygame.font.SysFont("Arial", 18)


class PlayerCar:
    """Класс машины игрока: движение по клавишам, отрисовка."""

    WIDTH  = 50
    HEIGHT = 80
    SPEED  = 5

    def __init__(self):
        # Стартовая позиция — по центру внизу экрана
        self.x = SCREEN_WIDTH // 2 - self.WIDTH // 2
        self.y = SCREEN_HEIGHT - self.HEIGHT - 20
        self.rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)  # прямоугольник для коллизий

    def move(self, keys):
        """Перемещение машины по стрелкам, ограничено границами дороги."""

        # Горизонтальное движение
        if keys[pygame.K_LEFT] and self.rect.left > ROAD_LEFT:
            self.rect.x -= self.SPEED
        if keys[pygame.K_RIGHT] and self.rect.right < ROAD_RIGHT:
            self.rect.x += self.SPEED

        # Вертикальное движение
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.SPEED
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.SPEED

    def draw(self, surface):
        """Рисует машину игрока: кузов, лобовое стекло, фонари."""
        # Кузов машины
        pygame.draw.rect(surface, BLUE, self.rect, border_radius=8)
        # Лобовое стекло
        pygame.draw.rect(surface, (180, 220, 255),
                         (self.rect.x + 8, self.rect.y + 10, 34, 20),
                         border_radius=4)
        # Левый задний фонарь
        pygame.draw.rect(surface, RED,
                         (self.rect.x + 5, self.rect.bottom - 12, 12, 8),
                         border_radius=2)
        # Правый задний фонарь
        pygame.draw.rect(surface, RED,
                         (self.rect.right - 17, self.rect.bottom - 12, 12, 8),
                         border_radius=2)


class EnemyCar:
    """Класс машины противника: случайная полоса, случайный цвет, движение вниз."""

    WIDTH  = 50
    HEIGHT = 80
    COLORS = [RED, GREEN, ORANGE, (160, 32, 240)]

    def __init__(self, speed):
        self.color = random.choice(self.COLORS)  # случайный цвет из списка
        lane_width = (ROAD_RIGHT - ROAD_LEFT) // 3
        lane = random.randint(0, 2)  # случайная полоса (0, 1 или 2)
        x = ROAD_LEFT + lane * lane_width + (lane_width - self.WIDTH) // 2
        self.rect  = pygame.Rect(x, -self.HEIGHT, self.WIDTH, self.HEIGHT)  # стартует выше экрана
        self.speed = speed

    def update(self):
        """Перемещает машину вниз на величину скорости."""
        self.rect.y += self.speed

    def is_off_screen(self):
        """Возвращает True, если машина вышла за нижнюю границу экрана."""
        return self.rect.top > SCREEN_HEIGHT

    def draw(self, surface):
        """Рисует машину противника: кузов, стекло, фары."""
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        # Лобовое стекло
        pygame.draw.rect(surface, (200, 230, 200),
                         (self.rect.x + 8, self.rect.y + 10, 34, 20),
                         border_radius=4)
        # Левая фара
        pygame.draw.rect(surface, YELLOW,
                         (self.rect.x + 5, self.rect.bottom - 12, 12, 8),
                         border_radius=2)
        # Правая фара
        pygame.draw.rect(surface, YELLOW,
                         (self.rect.right - 17, self.rect.bottom - 12, 12, 8),
                         border_radius=2)


# ─── Монеты с весами ──────────────────────────────────────────────────────────
#
# Каждый тип монеты имеет:
#   weight  — относительная вероятность появления (чем больше, тем чаще)
#   value   — сколько очков/монет даёт
#   color   — цвет круга
#   label   — символ в центре
#   speed_bonus — насколько ускоряет врагов при сборе (0 = не ускоряет)
#
COIN_TYPES = [
    {"weight": 60, "value": 1,  "color": SILVER, "label": "1",  "speed_bonus": 0},   # обычная
    {"weight": 30, "value": 3,  "color": GOLD,   "label": "3",  "speed_bonus": 0},   # золотая
    {"weight": 10, "value": 10, "color": DIAMOND,"label": "★",  "speed_bonus": 0},   # алмазная
]

# Предварительно вычисляем кумулятивные веса для быстрой выборки
_WEIGHTS = [t["weight"] for t in COIN_TYPES]


def _pick_coin_type():
    """Возвращает случайный тип монеты с учётом весов (взвешенная выборка)."""
    return random.choices(COIN_TYPES, weights=_WEIGHTS, k=1)[0]


class Coin:
    """Монета: случайный тип (по весам), падает сверху, собирается игроком."""

    RADIUS = 12
    SPEED  = 4

    def __init__(self):
        self.ctype  = _pick_coin_type()  # тип монеты с весом и ценностью
        x = random.randint(ROAD_LEFT + self.RADIUS, ROAD_RIGHT - self.RADIUS)
        self.rect   = pygame.Rect(x - self.RADIUS, -self.RADIUS * 2,
                                  self.RADIUS * 2, self.RADIUS * 2)
        self.center = [x, -self.RADIUS]

    def update(self):
        """Двигает монету вниз."""
        self.center[1] += self.SPEED
        self.rect.center = (int(self.center[0]), int(self.center[1]))

    def is_off_screen(self):
        """Возвращает True, если монета вышла за нижнюю границу."""
        return self.center[1] > SCREEN_HEIGHT + self.RADIUS

    @property
    def value(self):
        """Ценность монеты (количество очков)."""
        return self.ctype["value"]

    def draw(self, surface):
        """Рисует монету: цветной круг с обводкой и меткой ценности."""
        cx, cy = int(self.center[0]), int(self.center[1])
        color  = self.ctype["color"]
        # Заливка
        pygame.draw.circle(surface, color, (cx, cy), self.RADIUS)
        # Обводка чуть темнее
        pygame.draw.circle(surface, ORANGE, (cx, cy), self.RADIUS, 2)
        # Метка ценности в центре
        lbl = font_small.render(self.ctype["label"], True, BLACK)
        surface.blit(lbl, (cx - lbl.get_width() // 2,
                           cy - lbl.get_height() // 2))


# ─── Интерфейсные функции ─────────────────────────────────────────────────────

def draw_road(surface, offset):
    """Рисует дорогу: зелёные обочины, серое полотно, разметку."""
    surface.fill((34, 120, 34))  # зелёный фон (трава)
    pygame.draw.rect(surface, GRAY,
                     (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_HEIGHT))
    # Боковые белые линии
    pygame.draw.rect(surface, WHITE, (ROAD_LEFT, 0, 6, SCREEN_HEIGHT))
    pygame.draw.rect(surface, WHITE, (ROAD_RIGHT - 6, 0, 6, SCREEN_HEIGHT))

    # Пунктирные линии между полосами (с анимацией через offset)
    lane_width = (ROAD_RIGHT - ROAD_LEFT) // 3
    for i in range(1, 3):
        lx = ROAD_LEFT + lane_width * i
        for y in range(-80 + offset % 80, SCREEN_HEIGHT, 80):
            pygame.draw.rect(surface, WHITE, (lx - 2, y, 4, 40))


def game_over_screen(score, coins):
    """Экран завершения игры. Возвращает True при нажатии R (рестарт)."""
    while True:
        screen.fill(BLACK)
        title = font_large.render("GAME OVER", True, RED)
        s_lbl = font_medium.render(f"Score : {score}", True, WHITE)
        c_lbl = font_medium.render(f"Coins : {coins}", True, YELLOW)
        r_lbl = font_small.render("Press R — restart   ESC — quit", True, GRAY)

        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))
        screen.blit(s_lbl, (SCREEN_WIDTH // 2 - s_lbl.get_width() // 2, 260))
        screen.blit(c_lbl, (SCREEN_WIDTH // 2 - c_lbl.get_width() // 2, 300))
        screen.blit(r_lbl, (SCREEN_WIDTH // 2 - r_lbl.get_width() // 2, 380))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:      return True
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()