"""
main.py — Entry point. Orchestrates screens and the main game loop.

Run:  python main.py
"""

import pygame
import random
import sys

from racer import (
    PlayerCar, EnemyCar, Coin, PowerUp,
    OilSpill, Barrier, NitroStrip,
    draw_road, draw_hud, play_sfx,
    screen, clock,
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    CAR_COLOR_MAP, BLUE,
    WHITE, YELLOW,
)
from ui import main_menu, name_entry, settings_screen, leaderboard_screen, game_over_screen
from persistence import load_settings, add_entry


# ── Difficulty presets ────────────────────────────────────────────────────────
DIFF = {
    "easy":   {"base_speed": 3, "enemy_interval": 2000, "obstacle_interval": 4000},
    "normal": {"base_speed": 4, "enemy_interval": 1500, "obstacle_interval": 3000},
    "hard":   {"base_speed": 6, "enemy_interval": 1000, "obstacle_interval": 2000},
}


# ── Main game loop ────────────────────────────────────────────────────────────
def play_game(player_name: str, settings: dict) -> None:
    diff      = DIFF[settings.get("difficulty", "normal")]
    car_color = CAR_COLOR_MAP.get(settings.get("car_color", "blue"), BLUE)
    sound_on  = settings.get("sound", True)

    player    = PlayerCar(color=car_color)
    enemies   = []
    coins     = []
    powerups  = []
    obstacles = []

    score        = 0
    coin_count   = 0
    distance     = 0        # metres (1 m ≈ 10 frames)
    road_offset  = 0

    enemy_speed  = diff["base_speed"]
    oil_slow_timer = 0      # frames of slowdown remaining

    # Active power-up tracking
    active_powerup   = None   # "nitro" | "shield" | "repair" | None
    powerup_timer    = 0      # frames remaining for display

    # Custom events
    ENEMY_EVENT    = pygame.USEREVENT + 1
    COIN_EVENT     = pygame.USEREVENT + 2
    POWERUP_EVENT  = pygame.USEREVENT + 3
    OBSTACLE_EVENT = pygame.USEREVENT + 4

    pygame.time.set_timer(ENEMY_EVENT,    diff["enemy_interval"])
    pygame.time.set_timer(COIN_EVENT,     2000)
    pygame.time.set_timer(POWERUP_EVENT,  7000)
    pygame.time.set_timer(OBSTACLE_EVENT, diff["obstacle_interval"])

    frame = 0

    while True:
        clock.tick(FPS)
        frame += 1
        distance = frame // 10          # distance in metres

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == ENEMY_EVENT:
                enemies.append(EnemyCar(enemy_speed, player.rect))

            if event.type == COIN_EVENT:
                if random.random() < 0.75:
                    coins.append(Coin(enemy_speed))

            if event.type == POWERUP_EVENT:
                # Only one power-up on screen at a time
                if len(powerups) == 0 and random.random() < 0.6:
                    powerups.append(PowerUp())

            if event.type == OBSTACLE_EVENT:
                kind = random.choice([OilSpill, Barrier, NitroStrip])
                obstacles.append(kind(enemy_speed))

        # ── Player movement ───────────────────────────────────────────────────
        keys = pygame.key.get_pressed()
        if oil_slow_timer > 0:
            # Temporarily slow the player
            saved = player.speed
            player.speed = max(1, player.speed - 3)
            player.move(keys)
            player.speed = saved
            oil_slow_timer -= 1
        else:
            player.move(keys)
        player.update()

        # ── Update enemies ────────────────────────────────────────────────────
        for e in enemies[:]:
            e.update()
            if e.is_off_screen():
                enemies.remove(e)
                score += 1
                # Scale difficulty every 5 points
                if score % 5 == 0:
                    enemy_speed = min(enemy_speed + 1, 14)
                    # Speed up timers (clamp at minimum interval)
                    new_int = max(600, diff["enemy_interval"] - score * 20)
                    pygame.time.set_timer(ENEMY_EVENT, new_int)
                    new_obs = max(1200, diff["obstacle_interval"] - score * 30)
                    pygame.time.set_timer(OBSTACLE_EVENT, new_obs)

        # ── Update coins ──────────────────────────────────────────────────────
        for c in coins[:]:
            c.update()
            if c.is_off_screen():
                coins.remove(c)
            elif player.rect.colliderect(c.rect):
                coins.remove(c)
                coin_count += c.value
                score      += c.value * 2
                play_sfx("coin", sound_on)

        # ── Update power-ups ──────────────────────────────────────────────────
        for p in powerups[:]:
            p.update()
            if p.is_expired():
                powerups.remove(p)
            elif player.rect.colliderect(p.rect):
                powerups.remove(p)
                _apply_powerup(p.kind, player)
                active_powerup = p.kind
                powerup_timer  = 4 * FPS  # display for 4 s
                score += 10
                play_sfx("powerup", sound_on)

        if powerup_timer > 0:
            powerup_timer -= 1
            if powerup_timer == 0:
                active_powerup = None

        # ── Update obstacles ──────────────────────────────────────────────────
        hit_obstacle = False
        for o in obstacles[:]:
            o.update()
            if o.is_off_screen():
                obstacles.remove(o)
                continue
            if player.rect.colliderect(o.rect):
                if isinstance(o, NitroStrip):
                    # Free nitro boost
                    player.nitro       = True
                    player.nitro_timer = 3 * FPS
                    active_powerup     = "nitro"
                    powerup_timer      = 3 * FPS
                    obstacles.remove(o)
                    play_sfx("nitro", sound_on)
                elif isinstance(o, OilSpill):
                    oil_slow_timer = 2 * FPS   # slow for 2 s
                    obstacles.remove(o)
                    play_sfx("oil", sound_on)
                elif isinstance(o, Barrier):
                    if player.shield:
                        player.shield = False   # shield absorbs hit
                        obstacles.remove(o)
                    else:
                        hit_obstacle = True
                        break

        # ── Collision with enemy car ──────────────────────────────────────────
        crashed = hit_obstacle
        if not crashed:
            for e in enemies:
                if player.rect.colliderect(e.rect):
                    if player.shield:
                        player.shield = False
                        enemies.remove(e)
                        break
                    else:
                        crashed = True
                        break

        if crashed:
            play_sfx("crash", sound_on)
            _end_run(player_name, score, distance, coin_count, settings)
            return

        # ── Score from distance ───────────────────────────────────────────────
        if frame % 60 == 0:        # +1 score per second
            score += 1

        # ── Road scroll speed ─────────────────────────────────────────────────
        road_offset = (road_offset + enemy_speed) % 80

        # ── Draw ──────────────────────────────────────────────────────────────
        draw_road(screen, road_offset)

        for o in obstacles: o.draw(screen)
        for e in enemies:   e.draw(screen)
        for c in coins:     c.draw(screen)
        for p in powerups:  p.draw(screen)
        player.draw(screen)

        draw_hud(screen, score, coin_count, distance, player, active_powerup, powerup_timer)

        pygame.display.flip()


def _apply_powerup(kind: str, player: PlayerCar):
    if kind == "nitro":
        player.nitro       = True
        player.nitro_timer = 4 * FPS
    elif kind == "shield":
        player.shield = True
    elif kind == "repair":
        # Repair clears any active slow and restores shield
        player.shield = True


def _end_run(name, score, distance, coins, settings):
    """Save score and show game-over screen; loop back or return to menu."""
    add_entry(name, score, distance, coins)
    result = game_over_screen(name, score, distance, coins)
    if result == "retry":
        play_game(name, settings)
    # else: returns to main(), which goes back to main_menu


# ── App entry point ───────────────────────────────────────────────────────────
def app():
    settings    = load_settings()
    player_name = None

    while True:
        action = main_menu(settings)["action"]

        if action == "play":
            if player_name is None:
                player_name = name_entry()
            play_game(player_name, settings)

        elif action == "leaderboard":
            leaderboard_screen()

        elif action == "settings":
            settings = settings_screen(settings)

        elif action == "quit":
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    app()