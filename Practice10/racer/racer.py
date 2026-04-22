import pygame
import random
import sys #for exit right after quit   


# Initialize pygame and set up constants, colors, and the screen

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

# width
ROAD_LEFT  = 60
ROAD_RIGHT = 340

# crteating window and clock

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) 
pygame.display.set_caption("Racer Game") 
clock  = pygame.time.Clock() #to control the frame rate

font_large  = pygame.font.SysFont("Arial", 36, bold=True)
font_medium = pygame.font.SysFont("Arial", 24, bold=True)
font_small  = pygame.font.SysFont("Arial", 18)


class PlayerCar:

    WIDTH  = 50
    HEIGHT = 80
    SPEED  = 5

    def __init__(self):
        # starting position
        self.x = SCREEN_WIDTH // 2 - self.WIDTH // 2
        self.y = SCREEN_HEIGHT - self.HEIGHT - 20
        self.rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT) #for collision detection

    def move(self, keys):

        # horizontal movement
        if keys[pygame.K_LEFT] and self.rect.left > ROAD_LEFT: #check if left arrow is pressed and car is not going off the road
            self.rect.x -= self.SPEED
        if keys[pygame.K_RIGHT] and self.rect.right < ROAD_RIGHT:#check if right arrow is pressed and car is not going off the road
            self.rect.x += self.SPEED

        # vertical movement
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.SPEED
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.SPEED

    def draw(self, surface):
        # draw the car body
        pygame.draw.rect(surface, BLUE,   self.rect, border_radius=8) #draw the car body as a blue rectangle with rounded corners
        # draw windows
        pygame.draw.rect(surface, (180, 220, 255),
                         (self.rect.x + 8, self.rect.y + 10, 34, 20), #draw the car windows on top of the car body
                         border_radius=4)
        # draw headlights
        pygame.draw.rect(surface, RED,
                         (self.rect.x + 5,  self.rect.bottom - 12, 12, 8), #draw the left headlight as a red rectangle
                         border_radius=2)
        pygame.draw.rect(surface, RED,
                         (self.rect.right - 17, self.rect.bottom - 12, 12, 8), #draw the right headlight as a red rectangle
                         border_radius=2)


# enemy car class

class EnemyCar:

    WIDTH  = 50
    HEIGHT = 80
    COLORS = [RED, GREEN, ORANGE, (160, 32, 240)]

    def __init__(self, speed):
        self.color = random.choice(self.COLORS)
        lane_width = (ROAD_RIGHT - ROAD_LEFT) // 3
        lane = random.randint(0, 2) # choose a random lane (0, 1, or 2)
        x = ROAD_LEFT + lane * lane_width + (lane_width - self.WIDTH) // 2 # calculate x position based on lane
        self.rect = pygame.Rect(x, -self.HEIGHT, self.WIDTH, self.HEIGHT) # start above the screen
        self.speed = speed

    def update(self):
        self.rect.y += self.speed # move the enemy car down the screen

    def is_off_screen(self):
        return self.rect.top > SCREEN_HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8) #draw the enemy car as a rectangle with its assigned color and rounded corners
        pygame.draw.rect(surface, (200, 230, 200), #draw the enemy car windows 
                         (self.rect.x + 8, self.rect.y + 10, 34, 20), 
                         border_radius=4)
        pygame.draw.rect(surface, YELLOW,
                         (self.rect.x + 5,  self.rect.bottom - 12, 12, 8),#draw the left headlight as a yellow rectangle
                         border_radius=2)
        pygame.draw.rect(surface, YELLOW,
                         (self.rect.right - 17, self.rect.bottom - 12, 12, 8),
                         border_radius=2)


class Coin:

    RADIUS = 12 
    SPEED  = 4

    def __init__(self):
        x = random.randint(ROAD_LEFT + self.RADIUS, ROAD_RIGHT - self.RADIUS) # random x position within the road boundaries
        self.rect   = pygame.Rect(x - self.RADIUS, -self.RADIUS * 2,
                                  self.RADIUS * 2, self.RADIUS * 2) 
        self.center = [x, -self.RADIUS]

    def update(self): 
        self.center[1] += self.SPEED # move the coin down the screen
        self.rect.center = (int(self.center[0]), int(self.center[1]))

    def is_off_screen(self):
        return self.center[1] > SCREEN_HEIGHT + self.RADIUS

    def draw(self, surface):
        cx, cy = int(self.center[0]), int(self.center[1]) #draw the coin as a yellow circle with an orange outline and a "$" symbol in the center
        pygame.draw.circle(surface, YELLOW,  (cx, cy), self.RADIUS)
        pygame.draw.circle(surface, ORANGE,  (cx, cy), self.RADIUS, 2) #outline
        lbl = font_small.render("$", True, ORANGE) #render creates the image of the text
        surface.blit(lbl, (cx - lbl.get_width() // 2,
                           cy - lbl.get_height() // 2))


# interface functions

def draw_road(surface, offset):
    surface.fill((34, 120, 34))
    pygame.draw.rect(surface, GRAY,
                     (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_HEIGHT)) 
    pygame.draw.rect(surface, WHITE, (ROAD_LEFT, 0, 6, SCREEN_HEIGHT))
    pygame.draw.rect(surface, WHITE, (ROAD_RIGHT - 6, 0, 6, SCREEN_HEIGHT))

    lane_width = (ROAD_RIGHT - ROAD_LEFT) // 3
    for i in range(1, 3):
        lx = ROAD_LEFT + lane_width * i
        for y in range(-80 + offset % 80, SCREEN_HEIGHT, 80): # dashed lane lines, %80 effect of road moving    
            pygame.draw.rect(surface, WHITE, (lx - 2, y, 4, 40))

def game_over_screen(score, coins):
    while True:
        screen.fill(BLACK)
        title = font_large.render("GAME OVER", True, RED)
        s_lbl = font_medium.render(f"Score : {score}",  True, WHITE)
        c_lbl = font_medium.render(f"Coins : {coins}",  True, YELLOW)
        r_lbl = font_small.render("Press R — restart   ESC — quit", True, GRAY)

        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))
        screen.blit(s_lbl, (SCREEN_WIDTH // 2 - s_lbl.get_width() // 2,  260))
        screen.blit(c_lbl, (SCREEN_WIDTH // 2 - c_lbl.get_width() // 2,  300))
        screen.blit(r_lbl, (SCREEN_WIDTH // 2 - r_lbl.get_width() // 2,  380))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: return True
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()