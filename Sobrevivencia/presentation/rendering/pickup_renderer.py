import math

import pygame
from pygame.math import Vector2

from ...data.constants import *
from ..ui_utils import hex_color

class PickupRendererMixin:
    def _draw_drops(self, game, camera):
        for drop in game.drops:
            x, y = self.world_to_screen(drop.pos + Vector2(0, math.sin(drop.bob) * 3), camera)
            pulse = 0.5 + 0.5 * math.sin(drop.bob * 1.7)
            if drop.kind == "xp":
                self._draw_soft_circle((x, y), drop.radius + 8 + pulse * 3, COLORS["xp"], alpha=45, rings=3)
                pygame.draw.circle(self.screen, hex_color(COLORS["xp"]), (x, y), int(drop.radius))
                pygame.draw.circle(self.screen, (187, 247, 208), (x, y), int(drop.radius * 0.45))
            elif drop.kind == "ammo":
                self._draw_soft_circle((x, y), drop.radius + 8, COLORS["projectile"], alpha=38, rings=3)
                pygame.draw.rect(self.screen, (103, 232, 249), (x - 7, y - 4, 14, 8), border_radius=3)
                pygame.draw.rect(self.screen, (8, 47, 73), (x - 7, y - 4, 14, 8), 1, border_radius=3)
                pygame.draw.circle(self.screen, (224, 242, 254), (x + 6, y), 3)
            elif drop.kind == "coin":
                self._draw_soft_circle((x, y), drop.radius + 7 + pulse * 2, COLORS["coin"], alpha=48, rings=3)
                pygame.draw.circle(self.screen, hex_color(COLORS["coin"]), (x, y), int(drop.radius))
                pygame.draw.circle(self.screen, (113, 63, 18), (x, y), int(drop.radius), 2)
                pygame.draw.circle(self.screen, (255, 247, 237), (x - 3, y - 3), 2)
            elif drop.kind == "heal":
                self._draw_soft_circle((x, y), drop.radius + 9, COLORS["health"], alpha=48, rings=3)
                pygame.draw.circle(self.screen, hex_color(COLORS["health"]), (x, y), int(drop.radius))
                pygame.draw.line(self.screen, (255, 255, 255), (x - 5, y), (x + 5, y), 2)
                pygame.draw.line(self.screen, (255, 255, 255), (x, y - 5), (x, y + 5), 2)
            elif drop.kind == "shield":
                self._draw_soft_circle((x, y), drop.radius + 10, COLORS["shield"], alpha=42, rings=3)
                pygame.draw.circle(self.screen, hex_color(COLORS["shield"]), (x, y), int(drop.radius), 3)
                pygame.draw.circle(self.screen, (191, 219, 254), (x, y), int(drop.radius * 0.45))
            elif drop.kind == "item_box":
                self._draw_soft_circle((x, y), drop.radius + 12 + pulse * 3, COLORS["special"], alpha=55, rings=3)
                rect = pygame.Rect(x - int(drop.radius), y - int(drop.radius), int(drop.radius * 2), int(drop.radius * 2))
                pygame.draw.rect(self.screen, hex_color(COLORS["special"]), rect, border_radius=4)
                pygame.draw.rect(self.screen, (224, 242, 254), rect, 2, border_radius=4)
                pygame.draw.line(self.screen, (8, 47, 73), (x - 5, y), (x + 5, y), 2)
                pygame.draw.line(self.screen, (8, 47, 73), (x, y - 5), (x, y + 5), 2)
            elif drop.kind == "vacuum":
                self._draw_soft_circle((x, y), drop.radius + 12 + pulse * 4, "#06B6D4", alpha=60, rings=4)
                pygame.draw.circle(self.screen, (6, 182, 212), (x, y), int(drop.radius))
                pygame.draw.circle(self.screen, (22, 78, 99), (x, y), int(drop.radius * 0.7), 2)
                pygame.draw.rect(self.screen, (239, 68, 68), (x - 4, y - 3, 3, 4))
                pygame.draw.rect(self.screen, (59, 130, 246), (x + 2, y - 3, 3, 4))
            elif drop.kind in ("portal", "exit_portal"):
                self._draw_soft_circle((x, y), drop.radius + 20 + pulse * 6, "#C084FC", alpha=75, rings=4)
                pygame.draw.circle(self.screen, (168, 85, 247), (x, y), int(drop.radius * 1.3))
                for r_idx in range(3):
                    angle = (drop.bob * 2.5 + r_idx * (math.tau / 3.0)) % math.tau
                    swirl_x = x + math.cos(angle) * (drop.radius * 0.8)
                    swirl_y = y + math.sin(angle) * (drop.radius * 0.8)
                    pygame.draw.circle(self.screen, (243, 232, 255), (int(swirl_x), int(swirl_y)), 4)
            elif drop.kind == "chalice":
                self._draw_soft_circle((x, y), drop.radius + 16 + pulse * 6, "#FACC15", alpha=86, rings=4)
                pygame.draw.circle(self.screen, (250, 204, 21), (x, y), int(drop.radius))
                pygame.draw.circle(self.screen, (255, 247, 237), (x, y), int(drop.radius * 0.45))
                pygame.draw.circle(self.screen, (113, 63, 18), (x, y), int(drop.radius), 2)
            elif drop.kind == "stamp":
                try:
                    from Sobrevivencia.data.stamps import stamp_hud_color, Stamp
                except Exception:
                    pass
                color_hex = stamp_hud_color(Stamp(key=drop.value))
                self._draw_soft_circle((x, y), drop.radius + 10 + pulse * 3, color_hex, alpha=65, rings=3)
                rect_size = int(drop.radius * 1.5)
                stamp_surface = pygame.Surface((rect_size, rect_size), pygame.SRCALPHA)
                pygame.draw.rect(stamp_surface, hex_color(color_hex), (0, 0, rect_size, rect_size), border_radius=3)
                pygame.draw.rect(stamp_surface, (255, 255, 255), (0, 0, rect_size, rect_size), width=1, border_radius=3)
                rotated_surf = pygame.transform.rotate(stamp_surface, 45)
                rotated_rect = rotated_surf.get_rect(center=(x, y))
                self.screen.blit(rotated_surf, rotated_rect.topleft)
            if getattr(game, "light_level", 1.0) < 0.15:
                outline = (250, 204, 21) if drop.kind in ("coin", "chalice") else (186, 230, 253)
                pygame.draw.circle(self.screen, outline, (x, y), int(drop.radius + 5), 2)
