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


# main game loop

def main():
    player      = PlayerCar()
    enemies     = []
    coins       = []
    score       = 0
    coin_count  = 0
    road_offset = 0

    ENEMY_EVENT = pygame.USEREVENT + 1 # custom event for adding a new enemy car
    COIN_EVENT  = pygame.USEREVENT + 2 # custom event for adding a new coin
    pygame.time.set_timer(ENEMY_EVENT, 1500) # add a new enemy every 1.5 seconds
    pygame.time.set_timer(COIN_EVENT,  2500) # add a new coin every 2.5 seconds

    enemy_speed = 4
    running = True

    while running:
        dt = clock.tick(FPS) 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == ENEMY_EVENT:
                enemies.append(EnemyCar(enemy_speed))
            if event.type == COIN_EVENT:
                if random.random() < 0.7:
                    coins.append(Coin())

        keys = pygame.key.get_pressed()
        player.move(keys)

        for e in enemies[:]: 
            e.update()
            if e.is_off_screen():
                enemies.remove(e) # remove enemy if it goes off screen
                score += 1
                if score % 5 == 0:
                    enemy_speed = min(enemy_speed + 1, 12) # increase enemy speed every 5 points, up to a max of 12

        for c in coins[:]:
            c.update()
            if c.is_off_screen():
                coins.remove(c)

        for e in enemies:
            if player.rect.colliderect(e.rect): # collision with enemy car
                if not game_over_screen(score, coin_count): return
                main()
                return

        for c in coins[:]:
            if player.rect.colliderect(c.rect): # collision with coin
                coins.remove(c)
                coin_count += 1

        road_offset = (road_offset + enemy_speed) % 80 # move the road to create a scrolling effect
        draw_road(screen, road_offset)

        for e in enemies: e.draw(screen)
        for c in coins: c.draw(screen)
        player.draw(screen)

        score_lbl = font_medium.render(f"Score: {score}", True, WHITE) #draw the score and coin count at the top of the screen
        screen.blit(score_lbl, (10, 10)) 
        coin_lbl = font_medium.render(f"Coins: {coin_count}", True, YELLOW) 
        screen.blit(coin_lbl, (SCREEN_WIDTH - coin_lbl.get_width() - 10, 10))

        pygame.display.flip() # update the display with everything we've drawn

if __name__ == "__main__":
    main()