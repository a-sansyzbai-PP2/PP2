import pygame
import datetime
import os

class MickeyClock:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.center = (screen_width // 2, screen_height // 2)
        self.start_time = datetime.datetime.now()

        assets_path = os.path.join(os.path.dirname(__file__), "images")

        self.bg = pygame.image.load(os.path.join(assets_path, "mickey.png"))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))

        self.hand_min_img = pygame.image.load(os.path.join(assets_path, "right_hand.png"))
        self.hand_sec_img = pygame.image.load(os.path.join(assets_path, "left_hand.png"))

        # right_hand смотрит на 2 часа (+60° от 12)
        # чтобы она показывала 12 когда угол=0, нужно offset = +60
        self.min_offset = 60

        # left_hand смотрит на 10 часов (-60° от 12)
        # чтобы она показывала 12 когда угол=0, нужно offset = -60
        self.sec_offset = -60

    def get_angles(self, current_time):
        # Секундная — всегда с 0, считаем от старта программы
        elapsed = (current_time - self.start_time).total_seconds()
        sec_angle = -(elapsed % 60) * 6 + self.sec_offset

        # Минутная — реальные минуты + плавность от секунд
        min_angle = -(current_time.minute * 6 + current_time.second * 0.1) + self.min_offset

        return sec_angle, min_angle

    def draw(self, surface):
        current_time = datetime.datetime.now()
        surface.blit(self.bg, (0, 0))

        sec_angle, min_angle = self.get_angles(current_time)

        self._blit_rotate(surface, self.hand_min_img, min_angle)
        self._blit_rotate(surface, self.hand_sec_img, sec_angle)

    def _blit_rotate(self, surface, image, angle):
        rotated = pygame.transform.rotate(image, angle)
        rect = rotated.get_rect(center=self.center)
        surface.blit(rotated, rect)