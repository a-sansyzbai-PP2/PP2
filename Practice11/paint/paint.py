import pygame
import sys
import math

# ─── Инициализация ────────────────────────────────────────────────────────────
pygame.init()
SCREEN_W  = 980          # немного шире из-за новых кнопок
SCREEN_H  = 640
TOOLBAR_H = 64           # высота верхней панели

# Цвета интерфейса
BG_CANVAS   = (255, 255, 255)
BG_TOOLBAR  = ( 40,  40,  50)
HIGHLIGHT   = ( 80, 140, 220)
BORDER_CLR  = (100, 100, 110)
TEXT_COLOR  = (220, 220, 220)

# Палитра цветов
PALETTE = [
    (  0,   0,   0), (255, 255, 255), (128, 128, 128), (192, 192, 192),
    (255,   0,   0), (128,   0,   0), (255, 128,   0), (128,  64,   0),
    (255, 255,   0), (128, 128,   0), (  0, 255,   0), (  0, 128,   0),
    (  0, 255, 255), (  0, 128, 128), (  0,   0, 255), (  0,   0, 128),
    (255,   0, 255), (128,   0, 128),
]

# Идентификаторы инструментов
TOOL_PEN      = "pen"
TOOL_RECT     = "rect"
TOOL_CIRCLE   = "circle"
TOOL_ERASER   = "eraser"
TOOL_SQUARE   = "square"      # новый: квадрат (равносторонний прямоугольник)
TOOL_RTRI     = "rtri"        # новый: прямоугольный треугольник
TOOL_ETRI     = "etri"        # новый: равносторонний треугольник
TOOL_RHOMBUS  = "rhombus"     # новый: ромб

# Создание окна, холста и вспомогательных объектов
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Paint Pro")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 13, bold=True)

canvas = pygame.Surface((SCREEN_W, SCREEN_H - TOOLBAR_H))
canvas.fill(BG_CANVAS)

# Кнопки изменения размера и очистки (фиксированные позиции)
plus_rect  = pygame.Rect(385, 28, 28, 22)
minus_rect = pygame.Rect(418, 28, 28, 22)
clear_rect = pygame.Rect(SCREEN_W - 80, 15, 70, 34)


class ToolButton:
    """Кнопка инструмента на панели: хранит позицию, метку и id инструмента."""

    def __init__(self, x, y, w, h, label, tool_id):
        self.rect    = pygame.Rect(x, y, w, h)
        self.label   = label    # текст на кнопке
        self.tool_id = tool_id  # к какому инструменту относится

    def draw(self, surface, active_tool):
        """Рисует кнопку, подсвечивая активный инструмент."""
        color = HIGHLIGHT if self.tool_id == active_tool else BG_TOOLBAR
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, BORDER_CLR, self.rect, 1, border_radius=6)
        lbl = font.render(self.label, True, TEXT_COLOR)
        surface.blit(lbl, (self.rect.centerx - lbl.get_width() // 2,
                           self.rect.centery - lbl.get_height() // 2))

    def is_clicked(self, pos):
        """Возвращает True, если клик попал в кнопку."""
        return self.rect.collidepoint(pos)


# ─── Вспомогательные функции рисования фигур ──────────────────────────────────

def draw_square(surface, color, start, end, size):
    """Рисует квадрат: сторона = минимальная из сторон drag-прямоугольника."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    # Берём меньший из двух размеров, сохраняя знак
    side = min(abs(dx), abs(dy))
    sx   = start[0] + (side if dx >= 0 else -side)
    sy   = start[1] + (side if dy >= 0 else -side)
    rx   = min(start[0], sx)
    ry   = min(start[1], sy)
    pygame.draw.rect(surface, color, (rx, ry, side, side), size)


def draw_right_triangle(surface, color, start, end, size):
    """Рисует прямоугольный треугольник.
    Прямой угол — в точке start, гипотенуза — от (end[0], start[1]) до (start[0], end[1])."""
    p1 = start                       # прямой угол
    p2 = (end[0], start[1])          # верхний правый угол
    p3 = (start[0], end[1])          # нижний левый угол
    pygame.draw.polygon(surface, color, [p1, p2, p3], size)


def draw_equilateral_triangle(surface, color, start, end, size):
    """Рисует равносторонний треугольник.
    Основание горизонтально между start и (end[0], start[1]),
    вершина поднята на высоту = (√3/2) * сторона."""
    base_len = end[0] - start[0]    # длина основания (знаковая)
    # Основание: два нижних угла
    p1 = start
    p2 = (end[0], start[1])
    # Высота равностороннего треугольника = сторона * √3/2
    height = int(abs(base_len) * math.sqrt(3) / 2)
    # Вершина над серединой основания; направление выбирается по dy
    mid_x   = (start[0] + end[0]) // 2
    # Если тащим вниз — вершина вверху, иначе — внизу
    sign    = -1 if end[1] >= start[1] else 1
    p3      = (mid_x, start[1] + sign * height)
    pygame.draw.polygon(surface, color, [p1, p2, p3], size)


def draw_rhombus(surface, color, start, end, size):
    """Рисует ромб по диагоналям: start и end — противоположные угла.
    Четыре вершины: верхняя, правая, нижняя, левая."""
    cx  = (start[0] + end[0]) // 2   # центр по горизонтали
    cy  = (start[1] + end[1]) // 2   # центр по вертикали
    top    = (cx,       start[1])
    right  = (end[0],   cy)
    bottom = (cx,       end[1])
    left   = (start[0], cy)
    pygame.draw.polygon(surface, color, [top, right, bottom, left], size)


# ─── Отрисовка панели инструментов ───────────────────────────────────────────

def draw_toolbar(surface, tool_buttons, cur_tool, cur_color, cur_size, palette_rects):
    """Рисует всю панель: кнопки, цветовой превью, размер, палитру и очистку."""
    pygame.draw.rect(surface, BG_TOOLBAR, (0, 0, SCREEN_W, TOOLBAR_H))

    # Кнопки инструментов
    for btn in tool_buttons:
        btn.draw(surface, cur_tool)

    # Превью текущего цвета
    color_rect = pygame.Rect(490, 10, 44, 44)
    pygame.draw.rect(surface, cur_color, color_rect, border_radius=4)
    pygame.draw.rect(surface, TEXT_COLOR, color_rect, 2, border_radius=4)

    # Размер кисти
    size_lbl = font.render(f"Size: {cur_size}", True, TEXT_COLOR)
    surface.blit(size_lbl, (385, 10))

    # Кнопки + и -
    pygame.draw.rect(surface, BORDER_CLR, plus_rect,  border_radius=4)
    pygame.draw.rect(surface, BORDER_CLR, minus_rect, border_radius=4)
    surface.blit(font.render("+", True, TEXT_COLOR), (plus_rect.centerx - 4,  plus_rect.centery - 8))
    surface.blit(font.render("-", True, TEXT_COLOR), (minus_rect.centerx - 4, minus_rect.centery - 8))

    # Цветовая палитра
    for idx, rect in enumerate(palette_rects):
        pygame.draw.rect(surface, PALETTE[idx], rect, border_radius=3)
        pygame.draw.rect(surface, BORDER_CLR,   rect, 1, border_radius=3)

    # Кнопка очистки
    pygame.draw.rect(surface, (180, 40, 40), clear_rect, border_radius=6)
    surface.blit(font.render("Clear", True, TEXT_COLOR),
                 (clear_rect.centerx - 18, clear_rect.centery - 8))


def to_canvas(x, y):
    """Переводит экранные координаты в координаты холста (с учётом тулбара)."""
    return x, y - TOOLBAR_H