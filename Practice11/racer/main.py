import pygame
import random
import sys

from racer import (
    PlayerCar, EnemyCar, Coin,
    draw_road, game_over_screen,
    screen, clock,
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    font_medium, font_small,
    WHITE, YELLOW
)

# Количество монет (по очкам), при котором враги ускоряются
SPEED_UP_EVERY = 10


def main():
    player      = PlayerCar()
    enemies     = []
    coins       = []
    score       = 0
    coin_score  = 0   # суммарная ценность собранных монет (учитывает веса)
    road_offset = 0

    ENEMY_EVENT = pygame.USEREVENT + 1  # кастомное событие: новый враг
    COIN_EVENT  = pygame.USEREVENT + 2  # кастомное событие: новая монета
    pygame.time.set_timer(ENEMY_EVENT, 1500)  # враг каждые 1.5 сек
    pygame.time.set_timer(COIN_EVENT,  2500)  # монета каждые 2.5 сек

    enemy_speed    = 4
    last_threshold = 0   # последний порог монет, при котором ускорялись враги
    running        = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == ENEMY_EVENT:
                enemies.append(EnemyCar(enemy_speed))
            if event.type == COIN_EVENT:
                # Монета появляется с вероятностью 70%
                if random.random() < 0.7:
                    coins.append(Coin())

        # Обновление позиции игрока по нажатым клавишам
        keys = pygame.key.get_pressed()
        player.move(keys)

        # Обновление врагов
        for e in enemies[:]:
            e.update()
            if e.is_off_screen():
                enemies.remove(e)
                score += 1   # очко за каждого объехавшего врага
                if score % 5 == 0:
                    # Каждые 5 очков немного увеличиваем скорость врагов
                    enemy_speed = min(enemy_speed + 1, 12)

        # Обновление монет
        for c in coins[:]:
            c.update()
            if c.is_off_screen():
                coins.remove(c)

        # Проверка столкновения с врагами
        for e in enemies:
            if player.rect.colliderect(e.rect):
                if not game_over_screen(score, coin_score):
                    return
                main()   # рестарт
                return

        # Проверка сбора монет
        for c in coins[:]:
            if player.rect.colliderect(c.rect):
                coins.remove(c)
                coin_score += c.value   # прибавляем ценность монеты (с учётом веса)

                # ─── Ускорение врагов при накоплении N монет ──────────────
                # Каждые SPEED_UP_EVERY очков монет враги становятся быстрее.
                # last_threshold следит за тем, сколько раз уже применялось ускорение,
                # чтобы не повторять его при одном и том же пороге.
                new_threshold = coin_score // SPEED_UP_EVERY
                if new_threshold > last_threshold:
                    extra = new_threshold - last_threshold  # сколько порогов пройдено
                    enemy_speed = min(enemy_speed + extra, 14)  # ускоряем, но не более 14
                    # Обновляем скорость уже существующих врагов
                    for e in enemies:
                        e.speed = enemy_speed
                    last_threshold = new_threshold

        # Анимация движения дороги
        road_offset = (road_offset + enemy_speed) % 80
        draw_road(screen, road_offset)

        # Отрисовка объектов
        for e in enemies: e.draw(screen)
        for c in coins:   c.draw(screen)
        player.draw(screen)

        # HUD: очки и монеты
        score_lbl = font_medium.render(f"Score: {score}", True, WHITE)
        screen.blit(score_lbl, (10, 10))
        coin_lbl  = font_medium.render(f"Coins: {coin_score}", True, YELLOW)
        screen.blit(coin_lbl, (SCREEN_WIDTH - coin_lbl.get_width() - 10, 10))

        # Подсказка: до следующего ускорения
        next_up = SPEED_UP_EVERY - (coin_score % SPEED_UP_EVERY)
        hint    = font_small.render(f"Next speedup: {next_up} pts", True, (200, 200, 200))
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 10))

        pygame.display.flip()  # обновляем экран


if __name__ == "__main__":
    main()