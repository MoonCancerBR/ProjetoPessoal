import math

import pygame
from pygame.math import Vector2


class EffectSurfaceCache:
    def __init__(self):
        self._soft_circles = {}
        self._shadows = {}

    def soft_circle(self, radius, rgb, alpha, rings):
        radius = max(1, int(radius))
        key = (radius, tuple(rgb[:3]), int(alpha), int(rings))
        if key not in self._soft_circles:
            size = radius * 2 + 4
            glow = pygame.Surface((size, size), pygame.SRCALPHA)
            for index in range(rings, 0, -1):
                ring_radius = max(1, int(radius * index / rings))
                ring_alpha = max(0, int(alpha * (index / rings) ** 1.8))
                pygame.draw.circle(glow, (*rgb[:3], ring_alpha), (size // 2, size // 2), ring_radius)
            self._soft_circles[key] = glow
        return self._soft_circles[key]

    def shadow(self, radius, alpha, y_scale):
        width = max(4, int(radius * 2.25))
        height = max(3, int(radius * y_scale))
        key = (width, height, int(alpha))
        if key not in self._shadows:
            shadow = pygame.Surface((width + 4, height + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, int(alpha)), (2, 2, width, height))
            self._shadows[key] = shadow
        return self._shadows[key], width


def draw_soft_circle(surface, center, radius, color, rgb_func, alpha=80, rings=3, cache=None):
    radius = max(1, int(radius))
    rgb = rgb_func(color)
    if cache is None:
        cache = EffectSurfaceCache()
    glow = cache.soft_circle(radius, rgb, alpha, rings)
    size = glow.get_width()
    surface.blit(glow, (int(center[0] - size // 2), int(center[1] - size // 2)))


def draw_shadow(surface, center, radius, alpha=92, y_scale=0.36, cache=None):
    if cache is None:
        cache = EffectSurfaceCache()
    shadow, width = cache.shadow(radius, alpha, y_scale)
    surface.blit(shadow, (int(center[0] - width / 2), int(center[1] + radius * 0.48)))


def draw_star(surface, center, outer, inner, color, points=5, angle_offset=-math.pi / 2):
    vertices = []
    for index in range(points * 2):
        radius = outer if index % 2 == 0 else inner
        angle = angle_offset + index * math.pi / points
        vertices.append((center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius))
    pygame.draw.polygon(surface, color, vertices)


def draw_special_blast(surface, game, camera, world_to_screen, screen_size):
    if game.special_blast_timer <= 0:
        return

    progress = 1 - game.special_blast_timer / 0.35
    radius = int(game.special_radius() * progress)
    x, y = world_to_screen(game.player.pos, camera)
    overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
    alpha = 1 - progress

    pygame.draw.circle(overlay, (56, 189, 248, int(72 * alpha)), (x, y), radius)
    pygame.draw.circle(overlay, (165, 243, 252, int(135 * alpha)), (x, y), radius, 8)
    pygame.draw.circle(overlay, (255, 255, 255, int(90 * alpha)), (x, y), max(1, radius // 2), 2)

    for index in range(10):
        angle = game.time_alive * 3 + index * math.tau / 10
        p1 = Vector2(x, y) + Vector2(math.cos(angle), math.sin(angle)) * radius * 0.32
        p2 = Vector2(x, y) + Vector2(math.cos(angle), math.sin(angle)) * radius * 0.92
        pygame.draw.line(overlay, (224, 242, 254, int(80 * alpha)), p1, p2, 2)

    surface.blit(overlay, (0, 0))
