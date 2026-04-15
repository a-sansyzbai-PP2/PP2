import pygame
import sys
import time
from clock import MickeyClock

IMG_SIZE = 560
WIDTH = IMG_SIZE
HEIGHT = IMG_SIZE + 80
FPS = 10

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mickey's Clock")
clock_tick = pygame.time.Clock()

mickey_clock = MickeyClock(WIDTH, IMG_SIZE)

font = pygame.font.SysFont("Arial", 32, bold=True)
font_small = pygame.font.SysFont("Arial", 20)

BG = (245, 245, 235)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    now = time.localtime()
    minutes = now.tm_min
    seconds = now.tm_sec

    screen.fill(BG)

    mickey_clock.draw(screen, minutes, seconds)

    time_str = f"{minutes:02d}:{seconds:02d}"
    text_surf = font.render(time_str, True, (30, 30, 30))
    screen.blit(text_surf, text_surf.get_rect(centerx=WIDTH // 2, y=IMG_SIZE + 10))

    label_surf = font_small.render("Mickey's Clock", True, (100, 100, 100))
    screen.blit(label_surf, label_surf.get_rect(centerx=WIDTH // 2, y=IMG_SIZE + 48))

    pygame.display.flip()
    clock_tick.tick(FPS)