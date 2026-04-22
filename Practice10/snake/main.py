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
    food  = Food()
    food.respawn(snake.body)

    score       = 0
    level       = 1
    food_eaten  = 0
    move_delay  = BASE_MOVE
    frame_count = 0

    running = True
    while running:
        clock.tick(BASE_FPS)
        frame_count += 1

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                # Change direction with arrow keys or WASD, but not opposite to current
                if event.key in (pygame.K_UP,    pygame.K_w): snake.set_direction( 0, -1)
                if event.key in (pygame.K_DOWN,  pygame.K_s): snake.set_direction( 0,  1)
                if event.key in (pygame.K_LEFT,  pygame.K_a): snake.set_direction(-1,  0)
                if event.key in (pygame.K_RIGHT, pygame.K_d): snake.set_direction( 1,  0)
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # Snake movement and game logic
        if frame_count % move_delay == 0:
            alive = snake.step()

            if not alive:
                # Game over: show end screen and restart if chosen
                draw_field(screen)
                food.draw(screen)
                snake.draw(screen)
                draw_hud(screen, score, level)
                pygame.display.flip()
                if end_screen(score, level):
                    main()
                return

            # Check if food is eaten
            if snake.body[0] == food.pos:
                snake.grow()
                food.respawn(snake.body)
                score      += 10 * level    # more points for higher levels
                food_eaten += 1

                # Level up after eating enough food: increase level and speed
                if food_eaten >= FOOD_PER_LEVEL:
                    level      += 1
                    food_eaten  = 0
                    # Decrease move delay to speed up the snake, but not too much
                    move_delay  = max(2, move_delay - 1)

        # Drawing
        draw_field(screen)
        food.draw(screen)
        snake.draw(screen)
        draw_hud(screen, score, level)
        pygame.display.flip()


if __name__ == "__main__":
    main()