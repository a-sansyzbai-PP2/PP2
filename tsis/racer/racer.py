"""
racer.py — Game objects, road drawing, power-ups, and obstacles.
All pygame globals (screen, clock, constants) live here.
"""

import pygame
import random
import sys
import math

# ── Init ──────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()

SCREEN_WIDTH  = 420
SCREEN_HEIGHT = 640
FPS           = 60

# Road geometry
ROAD_LEFT  = 50
ROAD_RIGHT = 370
LANE_COUNT = 3
LANE_W     = (ROAD_RIGHT - ROAD_LEFT) // LANE_COUNT   # 106 px per lane

# Colors
WHITE   = (255, 255, 255)
BLACK   = (  0,   0,   0)
GRAY    = (110, 110, 110)
DARK    = ( 40,  40,  40)
RED     = (220,  30,  30)
YELLOW  = (255, 215,   0)
GREEN   = ( 30, 200,  80)
BLUE    = ( 30, 100, 220)
ORANGE  = (255, 140,   0)
PURPLE  = (160,  32, 240)
CYAN    = (  0, 220, 220)
GRASS   = ( 34, 120,  34)
NITRO_C = (  0, 240, 180)
SHIELD_C= ( 80, 160, 255)
REPAIR_C= (255,  80, 160)
OIL_C   = ( 20,  20,  30)

CAR_COLOR_MAP = {
    "blue":   BLUE,
    "red":    RED,
    "green":  GREEN,
    "orange": ORANGE,
    "purple": PURPLE,
}

# ── Sound system ─────────────────────────────────────────────────────────────
import struct
import math as _math

def _make_sound(freq=440, duration=0.1, volume=0.3, wave="sine"):
    """Generate a sound using only stdlib — no numpy needed."""
    sample_rate = 44100
    n = int(sample_rate * duration)
    buf = []
    for i in range(n):
        t = i / sample_rate
        fade = 1.0 - i / n
        if wave == "sine":
            v = _math.sin(2 * _math.pi * freq * t)
        elif wave == "square":
            v = 1.0 if _math.sin(2 * _math.pi * freq * t) >= 0 else -1.0
        elif wave == "noise":
            import random as _r
            v = _r.uniform(-1, 1)
        else:
            v = _math.sin(2 * _math.pi * freq * t)
        sample = int(v * fade * volume * 32767)
        sample = max(-32768, min(32767, sample))
        buf.append(struct.pack("<hh", sample, sample))  # stereo
    raw = b"".join(buf)
    return pygame.mixer.Sound(buffer=raw)

try:
    _SND_COIN    = _make_sound(freq=880,  duration=0.12, volume=0.4, wave="sine")
    _SND_POWERUP = _make_sound(freq=660,  duration=0.25, volume=0.4, wave="sine")
    _SND_CRASH   = _make_sound(freq=120,  duration=0.35, volume=0.5, wave="noise")
    _SND_OIL     = _make_sound(freq=200,  duration=0.20, volume=0.3, wave="square")
    _SND_NITRO   = _make_sound(freq=1000, duration=0.15, volume=0.3, wave="square")
    _SOUND_OK = True
except Exception:
    _SOUND_OK = False

def play_sfx(name: str, enabled: bool = True):
    """Play a named sound effect if sound is enabled."""
    if not enabled or not _SOUND_OK:
        return
    sfx = {
        "coin":    _SND_COIN,
        "powerup": _SND_POWERUP,
        "crash":   _SND_CRASH,
        "oil":     _SND_OIL,
        "nitro":   _SND_NITRO,
    }.get(name)
    if sfx:
        sfx.play()


# Window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Racer — TSIS 3")
clock  = pygame.time.Clock()

font_large  = pygame.font.SysFont("Arial", 36, bold=True)
font_medium = pygame.font.SysFont("Arial", 22, bold=True)
font_small  = pygame.font.SysFont("Arial", 16)
font_tiny   = pygame.font.SysFont("Arial", 13)


# ── Helpers ───────────────────────────────────────────────────────────────────
def lane_x(lane: int) -> int:
    """Return center x of the given lane (0-indexed)."""
    return ROAD_LEFT + lane * LANE_W + LANE_W // 2


def random_lane_x(width: int) -> int:
    lane = random.randint(0, LANE_COUNT - 1)
    return lane_x(lane) - width // 2


# ── PlayerCar ─────────────────────────────────────────────────────────────────
class PlayerCar:
    WIDTH  = 46
    HEIGHT = 76
    BASE_SPEED = 5

    def __init__(self, color=BLUE):
        self.color   = color
        self.rect    = pygame.Rect(
            SCREEN_WIDTH // 2 - self.WIDTH // 2,
            SCREEN_HEIGHT - self.HEIGHT - 20,
            self.WIDTH, self.HEIGHT
        )
        self.speed   = self.BASE_SPEED
        # power-up state
        self.shield  = False
        self.nitro   = False
        self.nitro_timer  = 0    # frames remaining
        self.shield_hit   = False

    def move(self, keys):
        spd = self.speed + (4 if self.nitro else 0)
        if keys[pygame.K_LEFT]  and self.rect.left  > ROAD_LEFT:
            self.rect.x -= spd
        if keys[pygame.K_RIGHT] and self.rect.right < ROAD_RIGHT:
            self.rect.x += spd
        if keys[pygame.K_UP]    and self.rect.top   > 0:
            self.rect.y -= spd
        if keys[pygame.K_DOWN]  and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += spd

    def update(self):
        if self.nitro:
            self.nitro_timer -= 1
            if self.nitro_timer <= 0:
                self.nitro = False

    def draw(self, surface):
        # Body
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        # Windshield
        pygame.draw.rect(surface, (180, 220, 255),
                         (self.rect.x + 7, self.rect.y + 8, 32, 18), border_radius=4)
        # Rear window
        pygame.draw.rect(surface, (180, 220, 255),
                         (self.rect.x + 7, self.rect.y + 48, 32, 14), border_radius=4)
        # Tail-lights
        pygame.draw.rect(surface, RED,
                         (self.rect.x + 4, self.rect.bottom - 10, 12, 7), border_radius=2)
        pygame.draw.rect(surface, RED,
                         (self.rect.right - 16, self.rect.bottom - 10, 12, 7), border_radius=2)
        # Shield ring
        if self.shield:
            pygame.draw.circle(surface, SHIELD_C,
                                self.rect.center, self.WIDTH, 3)
        # Nitro flame
        if self.nitro:
            cx = self.rect.centerx
            by = self.rect.bottom
            pts = [(cx-8, by), (cx, by+18), (cx+8, by)]
            pygame.draw.polygon(surface, NITRO_C, pts)


# ── EnemyCar ──────────────────────────────────────────────────────────────────
class EnemyCar:
    WIDTH  = 46
    HEIGHT = 76
    COLORS = [RED, GREEN, ORANGE, PURPLE, (200, 100, 40)]

    def __init__(self, speed, player_rect=None):
        self.color = random.choice(self.COLORS)
        self.speed = speed
        x = self._safe_x(player_rect)
        self.rect  = pygame.Rect(x, -self.HEIGHT - random.randint(0, 60),
                                 self.WIDTH, self.HEIGHT)

    def _safe_x(self, player_rect):
        for _ in range(10):
            x = random_lane_x(self.WIDTH)
            if player_rect is None:
                return x
            if abs(x - player_rect.x) > self.WIDTH * 1.5:
                return x
        return random_lane_x(self.WIDTH)

    def update(self):
        self.rect.y += self.speed

    def is_off_screen(self):
        return self.rect.top > SCREEN_HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 230, 200),
                         (self.rect.x + 7, self.rect.y + 8, 32, 18), border_radius=4)
        pygame.draw.rect(surface, (200, 230, 200),
                         (self.rect.x + 7, self.rect.y + 48, 32, 14), border_radius=4)
        pygame.draw.rect(surface, YELLOW,
                         (self.rect.x + 4, self.rect.bottom - 10, 12, 7), border_radius=2)
        pygame.draw.rect(surface, YELLOW,
                         (self.rect.right - 16, self.rect.bottom - 10, 12, 7), border_radius=2)


# ── Coin ──────────────────────────────────────────────────────────────────────
COIN_VALUES = {
    "bronze": (1,  (180, 100,  30), ORANGE),
    "silver": (3,  (180, 180, 180), WHITE),
    "gold":   (5,  YELLOW,          ORANGE),
}
COIN_WEIGHTS = {"bronze": 0.60, "silver": 0.30, "gold": 0.10}

class Coin:
    RADIUS = 12
    SPEED  = 4

    def __init__(self, enemy_speed=4):
        kind_list = list(COIN_WEIGHTS.keys())
        weights   = [COIN_WEIGHTS[k] for k in kind_list]
        self.kind  = random.choices(kind_list, weights=weights)[0]
        self.value, self.fill, self.outline = COIN_VALUES[self.kind]
        x = random.randint(ROAD_LEFT + self.RADIUS, ROAD_RIGHT - self.RADIUS)
        self.center = [float(x), float(-self.RADIUS * 2)]
        self.rect   = pygame.Rect(x - self.RADIUS, -self.RADIUS * 2,
                                  self.RADIUS * 2, self.RADIUS * 2)
        self.speed  = self.SPEED + enemy_speed // 3

    def update(self):
        self.center[1] += self.speed
        self.rect.center = (int(self.center[0]), int(self.center[1]))

    def is_off_screen(self):
        return self.center[1] > SCREEN_HEIGHT + self.RADIUS

    def draw(self, surface):
        cx, cy = int(self.center[0]), int(self.center[1])
        pygame.draw.circle(surface, self.fill,    (cx, cy), self.RADIUS)
        pygame.draw.circle(surface, self.outline, (cx, cy), self.RADIUS, 2)
        lbl = font_tiny.render(str(self.value), True, self.outline)
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))


# ── PowerUp ───────────────────────────────────────────────────────────────────
POWERUP_TIMEOUT = 8 * FPS    # frames before auto-disappear

class PowerUp:
    RADIUS = 14
    SPEED  = 3
    KINDS  = {
        "nitro":  (NITRO_C,  "N", "Nitro"),
        "shield": (SHIELD_C, "S", "Shield"),
        "repair": (REPAIR_C, "R", "Repair"),
    }

    def __init__(self, kind=None):
        self.kind   = kind or random.choice(list(self.KINDS.keys()))
        self.color, self.letter, self.label = self.KINDS[self.kind]
        x = random.randint(ROAD_LEFT + self.RADIUS, ROAD_RIGHT - self.RADIUS)
        self.center = [float(x), float(-self.RADIUS * 2)]
        self.rect   = pygame.Rect(x - self.RADIUS, -self.RADIUS * 2,
                                  self.RADIUS * 2, self.RADIUS * 2)
        self.life   = POWERUP_TIMEOUT

    def update(self):
        self.center[1] += self.SPEED
        self.rect.center = (int(self.center[0]), int(self.center[1]))
        self.life -= 1

    def is_expired(self):
        return self.life <= 0 or self.center[1] > SCREEN_HEIGHT + self.RADIUS

    def draw(self, surface):
        cx, cy = int(self.center[0]), int(self.center[1])
        pygame.draw.circle(surface, self.color, (cx, cy), self.RADIUS)
        pygame.draw.circle(surface, WHITE,      (cx, cy), self.RADIUS, 2)
        lbl = font_small.render(self.letter, True, BLACK)
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))


# ── Obstacle ──────────────────────────────────────────────────────────────────
class Obstacle:
    """Base class for road hazards."""
    SPEED = 4

    def __init__(self, speed):
        self.speed = speed

    def update(self):
        self.rect.y += self.speed

    def is_off_screen(self):
        return self.rect.top > SCREEN_HEIGHT


class OilSpill(Obstacle):
    """Slows the player for 2 seconds if driven over."""
    W, H = 56, 28

    def __init__(self, speed):
        super().__init__(speed)
        x = random_lane_x(self.W)
        self.rect  = pygame.Rect(x, -self.H - random.randint(0, 80), self.W, self.H)
        self.color = OIL_C

    def draw(self, surface):
        pygame.draw.ellipse(surface, self.color, self.rect)
        pygame.draw.ellipse(surface, (60, 60, 90), self.rect, 2)
        lbl = font_tiny.render("OIL", True, (100, 100, 160))
        surface.blit(lbl, (self.rect.centerx - lbl.get_width() // 2,
                           self.rect.centery - lbl.get_height() // 2))


class Barrier(Obstacle):
    """Static barrier — instant crash if hit (unless shielded)."""
    W, H = 60, 18

    def __init__(self, speed):
        super().__init__(speed)
        x = random_lane_x(self.W)
        self.rect  = pygame.Rect(x, -self.H - random.randint(0, 80), self.W, self.H)

    def draw(self, surface):
        pygame.draw.rect(surface, RED, self.rect, border_radius=4)
        # Stripes
        for i in range(3):
            sx = self.rect.x + i * 20 + 4
            pygame.draw.rect(surface, WHITE, (sx, self.rect.y + 4, 10, self.H - 8), border_radius=2)
        lbl = font_tiny.render("STOP", True, WHITE)
        surface.blit(lbl, (self.rect.centerx - lbl.get_width() // 2,
                           self.rect.centery - lbl.get_height() // 2))


class NitroStrip(Obstacle):
    """Harmless — gives the player a short boost."""
    W, H = 60, 20

    def __init__(self, speed):
        super().__init__(speed)
        x = random_lane_x(self.W)
        self.rect = pygame.Rect(x, -self.H - random.randint(0, 80), self.W, self.H)

    def draw(self, surface):
        pygame.draw.rect(surface, NITRO_C, self.rect, border_radius=4)
        lbl = font_tiny.render("BOOST", True, BLACK)
        surface.blit(lbl, (self.rect.centerx - lbl.get_width() // 2,
                           self.rect.centery - lbl.get_height() // 2))


# ── Road drawing ──────────────────────────────────────────────────────────────
def draw_road(surface, offset):
    surface.fill(GRASS)
    # Asphalt
    pygame.draw.rect(surface, GRAY, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_HEIGHT))
    # Road edges
    pygame.draw.rect(surface, WHITE, (ROAD_LEFT,      0, 5, SCREEN_HEIGHT))
    pygame.draw.rect(surface, WHITE, (ROAD_RIGHT - 5, 0, 5, SCREEN_HEIGHT))
    # Dashed lane dividers
    for i in range(1, LANE_COUNT):
        lx = ROAD_LEFT + LANE_W * i
        for y in range(-80 + offset % 80, SCREEN_HEIGHT, 80):
            pygame.draw.rect(surface, WHITE, (lx - 2, y, 4, 40))


def draw_hud(surface, score, coins, distance, player, active_powerup, powerup_timer):
    """Top HUD bar."""
    pygame.draw.rect(surface, (20, 20, 30), (0, 0, SCREEN_WIDTH, 44))
    pygame.draw.line(surface, GRAY, (0, 44), (SCREEN_WIDTH, 44), 1)

    sc = font_medium.render(f"Score:{score}", True, WHITE)
    co = font_medium.render(f"${coins}", True, YELLOW)
    di = font_small.render(f"{distance}m", True, CYAN)
    surface.blit(sc, (6, 12))
    surface.blit(co, (SCREEN_WIDTH // 2 - co.get_width() // 2, 12))
    surface.blit(di, (SCREEN_WIDTH - di.get_width() - 8, 14))

    # Active power-up badge
    if active_powerup:
        secs = max(0, powerup_timer // FPS)
        col  = PowerUp.KINDS.get(active_powerup, (WHITE, "", ""))[0]
        label = PowerUp.KINDS.get(active_powerup, (WHITE, "", active_powerup))[2]
        badge = font_tiny.render(f"[{label} {secs}s]", True, col)
        surface.blit(badge, (SCREEN_WIDTH - badge.get_width() - 8, 30))

    # Shield indicator
    if player.shield:
        sh = font_tiny.render("[SHIELD]", True, SHIELD_C)
        surface.blit(sh, (6, 30))