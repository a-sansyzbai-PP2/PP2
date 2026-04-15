import pygame
import math
import os


def draw_mickey_hand(surface, cx, cy, angle_deg, length, color_glove, width):
    """
    Рисует руку Микки: линия от центра + белая перчатка на конце.
    angle_deg: 0 = вверх, по часовой стрелке.
    """
    angle_rad = math.radians(angle_deg)
    end_x = cx + length * math.sin(angle_rad)
    end_y = cy - length * math.cos(angle_rad)

    # рукав (толстая линия)
    pygame.draw.line(surface, (20, 20, 20),
                     (int(cx), int(cy)),
                     (int(end_x), int(end_y)), width)

    # белая перчатка — три кружка
    glove_r = width + 6
    pygame.draw.circle(surface, color_glove, (int(end_x), int(end_y)), glove_r)
    # пальцы — два маленьких кружка рядом
    finger_offset = glove_r - 2
    side_x = int(end_x + finger_offset * math.cos(angle_rad))
    side_y = int(end_y + finger_offset * math.sin(angle_rad))
    pygame.draw.circle(surface, color_glove, (side_x, side_y), glove_r - 3)
    side_x2 = int(end_x - finger_offset * math.cos(angle_rad))
    side_y2 = int(end_y - finger_offset * math.sin(angle_rad))
    pygame.draw.circle(surface, color_glove, (side_x2, side_y2), glove_r - 3)

    # обводка перчатки
    pygame.draw.circle(surface, (80, 80, 80), (int(end_x), int(end_y)), glove_r, 2)


class MickeyClock:
    def __init__(self, screen_width, img_size):
        self.cx = screen_width // 2
        self.cy = img_size // 2
        self.img_size = img_size
        self.mickey_img = None
        self._load_image()

    def _load_image(self):
        for name in ["mickeyclock.jpeg", "mickeyclock.jpg", "mickey_hand.png"]:
            path = os.path.join("images", name)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.mickey_img = pygame.transform.scale(img, (self.img_size, self.img_size))
                break

    def draw(self, surface, minutes, seconds):
        # угол: 0 = вверх, по часовой
        minute_angle = minutes * 6 + seconds * 0.1
        second_angle = seconds * 6

        radius = self.img_size // 2

        # фон — картинка Микки
        if self.mickey_img:
            rect = self.mickey_img.get_rect(center=(self.cx, self.cy))
            surface.blit(self.mickey_img, rect)
        else:
            pygame.draw.circle(surface, (255, 220, 150), (self.cx, self.cy), radius)

        # минутная рука (правая рука Микки) — чёрная перчатка
        draw_mickey_hand(surface, self.cx, self.cy,
                         angle_deg=minute_angle,
                         length=int(radius * 0.50),
                         color_glove=(240, 240, 240),
                         width=9)

        # секундная рука (левая рука Микки) — красная перчатка
        draw_mickey_hand(surface, self.cx, self.cy,
                         angle_deg=second_angle,
                         length=int(radius * 0.48),
                         color_glove=(220, 30, 30),
                         width=5)

        # центральная точка
        pygame.draw.circle(surface, (10, 10, 10), (self.cx, self.cy), 14)
        pygame.draw.circle(surface, (255, 255, 255), (self.cx, self.cy), 7)