import pygame
import sys
import math

# 
# Initialization
# 
pygame.init()
SCREEN_W  = 900
SCREEN_H  = 640
TOOLBAR_H = 64          # height of the top toolbar

# Interface colors
BG_CANVAS   = (255, 255, 255)
BG_TOOLBAR  = ( 40,  40,  50)
HIGHLIGHT   = ( 80, 140, 220)
BORDER_CLR  = (100, 100, 110)
TEXT_COLOR  = (220, 220, 220)

PALETTE = [
    (  0,   0,   0), (255, 255, 255), (128, 128, 128), (192, 192, 192),
    (255,   0,   0), (128,   0,   0), (255, 128,   0), (128,  64,   0),
    (255, 255,   0), (128, 128,   0), (  0, 255,   0), (  0, 128,   0),
    (  0, 255, 255), (  0, 128, 128), (  0,   0, 255), (  0,   0, 128),
    (255,   0, 255), (128,   0, 128),
]

TOOL_PEN    = "pen"
TOOL_RECT   = "rect"
TOOL_CIRCLE = "circle"
TOOL_ERASER = "eraser"

# Creation of the window and surfaces

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Paint Pro")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 14, bold=True)

canvas = pygame.Surface((SCREEN_W, SCREEN_H - TOOLBAR_H))
canvas.fill(BG_CANVAS)

# elements (fixed positions)
plus_rect  = pygame.Rect(385, 28, 28, 22)
minus_rect = pygame.Rect(418, 28, 28, 22)
clear_rect = pygame.Rect(SCREEN_W - 80, 15, 70, 34)


class ToolButton:
    def __init__(self, x, y, w, h, label, tool_id): 
        self.rect    = pygame.Rect(x, y, w, h)
        self.label   = label #text to display on the button
        self.tool_id = tool_id #identifier for which tool this button represents
        
    def draw(self, surface, active_tool):
        color = HIGHLIGHT if self.tool_id == active_tool else BG_TOOLBAR #highlight the button if it's the currently selected tool
        pygame.draw.rect(surface, color, self.rect, border_radius=6) 
        pygame.draw.rect(surface, BORDER_CLR, self.rect, 1, border_radius=6)
        lbl = font.render(self.label, True, TEXT_COLOR)
        surface.blit(lbl, (self.rect.centerx - lbl.get_width() // 2,
                           self.rect.centery - lbl.get_height() // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

def draw_toolbar(surface, tool_buttons, cur_tool, cur_color, cur_size, palette_rects):
    pygame.draw.rect(surface, BG_TOOLBAR, (0, 0, SCREEN_W, TOOLBAR_H))

    for btn in tool_buttons:
        btn.draw(surface, cur_tool)

    # Color preview
    color_rect = pygame.Rect(330, 10, 44, 44) #draw a square showing the currently selected color
    pygame.draw.rect(surface, cur_color, color_rect, border_radius=4) #fill the square with the current color
    pygame.draw.rect(surface, TEXT_COLOR, color_rect, 2, border_radius=4) #outline the color preview square with a border

    # Size display
    size_lbl = font.render(f"Size: {cur_size}", True, TEXT_COLOR)
    surface.blit(size_lbl, (385, 10))

    # + and - buttons
    pygame.draw.rect(surface, BORDER_CLR, plus_rect,  border_radius=4)
    pygame.draw.rect(surface, BORDER_CLR, minus_rect, border_radius=4)
    surface.blit(font.render("+", True, TEXT_COLOR), (plus_rect.centerx - 4, plus_rect.centery - 8))
    surface.blit(font.render("-", True, TEXT_COLOR), (minus_rect.centerx - 4, minus_rect.centery - 8))

    # Color palette
    for idx, rect in enumerate(palette_rects): #draw the color palette squares, filling them with their respective colors and outlining them with a border
        pygame.draw.rect(surface, PALETTE[idx], rect, border_radius=3)
        pygame.draw.rect(surface, BORDER_CLR, rect, 1, border_radius=3)
    # clear button
    pygame.draw.rect(surface, (180, 40, 40), clear_rect, border_radius=6) #draw the clear button as a red rectangle with rounded corners
    surface.blit(font.render("Clear", True, TEXT_COLOR), (clear_rect.centerx - 18, clear_rect.centery - 8))

def to_canvas(x, y): #convert mouse coordinates to canvas coordinates by adjusting for the toolbar height
    return x, y - TOOLBAR_H