import pygame
import sys
from player import MusicPlayer

WIDTH, HEIGHT = 600, 400
FPS = 30

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("Arial", 28, bold=True)
font_med = pygame.font.SysFont("Arial", 20)
font_small = pygame.font.SysFont("Arial", 16)

player = MusicPlayer("music")

BG = (30, 30, 30)
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
GREEN = (100, 220, 100)
YELLOW = (255, 220, 50)

def draw_text(text, font, color, x, y, center=True):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.centerx = x
    else:
        rect.x = x
    rect.y = y
    screen.blit(surf, rect)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                player.play()
            elif event.key == pygame.K_s:
                player.stop()
            elif event.key == pygame.K_n:
                player.next_track()
            elif event.key == pygame.K_b:
                player.prev_track()
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

    screen.fill(BG)

    draw_text("🎵 Music Player", font_big, WHITE, WIDTH // 2, 40)

    status_color = GREEN if player.playing else GRAY
    draw_text(f"Status: {player.get_status()}", font_med, status_color, WIDTH // 2, 110)

    track_name = player.get_current_track_name()
    draw_text(f"Track: {track_name}", font_med, YELLOW, WIDTH // 2, 155)

    if player.tracks:
        draw_text(f"{player.current_index + 1} / {len(player.tracks)}", font_med, GRAY, WIDTH // 2, 200)
    else:
        draw_text("Put .mp3/.wav files in the 'music' folder", font_small, GRAY, WIDTH // 2, 200)

    controls = [
        "[P] Play",
        "[S] Stop",
        "[N] Next",
        "[B] Previous",
        "[Q] Quit",
    ]
    draw_text("Controls:", font_med, WHITE, WIDTH // 2, 260)
    for i, ctrl in enumerate(controls):
        draw_text(ctrl, font_small, GRAY, WIDTH // 2, 290 + i * 22)

    pygame.display.flip()
    clock.tick(FPS)