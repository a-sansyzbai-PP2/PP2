import pygame
import sys

from snake import (
    Snake, Food,
    draw_field, draw_hud, end_screen,
    screen, clock,
    BASE_FPS, BASE_MOVE, FOOD_PER_LEVEL,
)


def main():
    snake = Snake()

    # Основная еда (всегда есть на поле)
    food = Food()
    food.respawn(snake.body)

    # Дополнительная еда (бонусная, может быть None)
    bonus_food        = None
    BONUS_INTERVAL    = 8000   # миллисекунды между появлениями бонусной еды
    last_bonus_time   = pygame.time.get_ticks()

    score       = 0
    level       = 1
    food_eaten  = 0
    move_delay  = BASE_MOVE
    frame_count = 0

    running = True
    while running:
        clock.tick(BASE_FPS)
        frame_count += 1
        now = pygame.time.get_ticks()

        # ─── Обработка событий ────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                # Смена направления стрелками или WASD
                if event.key in (pygame.K_UP,    pygame.K_w): snake.set_direction( 0, -1)
                if event.key in (pygame.K_DOWN,  pygame.K_s): snake.set_direction( 0,  1)
                if event.key in (pygame.K_LEFT,  pygame.K_a): snake.set_direction(-1,  0)
                if event.key in (pygame.K_RIGHT, pygame.K_d): snake.set_direction( 1,  0)
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # ─── Логика исчезающей еды ────────────────────────────────────────
        # Основная еда: если исчезла — возрождаем новую
        if food.is_expired():
            food.respawn(snake.body)

        # Бонусная еда: появляется каждые BONUS_INTERVAL мс
        if bonus_food is None and now - last_bonus_time >= BONUS_INTERVAL:
            bonus_food      = Food()
            bonus_food.respawn(snake.body)
            last_bonus_time = now

        # Если бонусная еда истекла — убираем её
        if bonus_food is not None and bonus_food.is_expired():
            bonus_food      = None
            last_bonus_time = now   # сбрасываем таймер

        # ─── Шаг змейки ───────────────────────────────────────────────────
        if frame_count % move_delay == 0:
            alive = snake.step()

            if not alive:
                # Смерть: показываем экран завершения, затем рестарт или выход
                draw_field(screen)
                food.draw(screen)
                if bonus_food:
                    bonus_food.draw(screen)
                snake.draw(screen)
                draw_hud(screen, score, level)
                pygame.display.flip()
                if end_screen(score, level):
                    main()
                return

            # ─── Поедание основной еды ────────────────────────────────────
            if snake.body[0] == food.pos:
                snake.grow()
                pts        = food.value * level   # очки масштабируются по уровню
                score      += pts
                food_eaten += 1
                food.respawn(snake.body)           # новая еда

                # Повышение уровня при достижении порога
                if food_eaten >= FOOD_PER_LEVEL:
                    level      += 1
                    food_eaten  = 0
                    move_delay  = max(2, move_delay - 1)   # ускоряем змейку

            # ─── Поедание бонусной еды ────────────────────────────────────
            if bonus_food is not None and snake.body[0] == bonus_food.pos:
                snake.grow()
                pts         = bonus_food.value * level
                score      += pts
                bonus_food  = None      # убираем бонусную еду
                last_bonus_time = now   # сбрасываем таймер следующей

        # ─── Отрисовка ────────────────────────────────────────────────────
        draw_field(screen)
        food.draw(screen)
        if bonus_food:
            bonus_food.draw(screen)
        snake.draw(screen)
        draw_hud(screen, score, level)
        pygame.display.flip()


if __name__ == "__main__":
    main()