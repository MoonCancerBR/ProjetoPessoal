import math

import pygame

from ..ui_utils import hex_color
from .. import arcade_theme
from ...data.constants import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH, TERRAIN_TYPES, WORLD_TILE_SIZE


class WorldRendererMixin:
    def _draw_terrain(self, game, camera):
        if getattr(game, "current_dimension", "main") == "pocket":
            self._draw_pocket_terrain(game, camera)
            return
        if getattr(game, "current_dimension", "main") == "olympus":
            self._draw_olympus_terrain(game, camera)
            return
        tile = WORLD_TILE_SIZE
        for x, y, size, kind, variation in game.world.iter_visible_terrain(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            data = TERRAIN_TYPES[kind]
            rect = pygame.Rect(int(x - camera.x), int(y - camera.y), size + 1, size + 1)
            base = hex_color(data["color"])
            pygame.draw.rect(self.screen, base, rect)
            if variation < 0.18:
                pygame.draw.rect(self.screen, self._blend(base, "#020617", 0.08), rect)
            if variation > 0.62:
                accent = hex_color(data["accent"])
                if kind == "sand":
                    pygame.draw.circle(self.screen, self._blend(accent, "#FFFFFF", 0.18), (rect.left + tile // 3, rect.top + tile // 2), 2)
                    pygame.draw.line(self.screen, accent, (rect.left + 14, rect.top + 30), (rect.right - 16, rect.top + 22), 1)
                    pygame.draw.line(self.screen, accent, (rect.left + 26, rect.bottom - 24), (rect.right - 28, rect.bottom - 34), 1)
                elif kind == "grass":
                    pygame.draw.circle(self.screen, accent, (rect.left + tile // 3, rect.top + tile // 3), 3)
                    pygame.draw.circle(self.screen, accent, (rect.left + tile * 2 // 3, rect.top + tile * 2 // 3), 2)
                    pygame.draw.line(self.screen, self._blend(accent, "#FFFFFF", 0.08), (rect.left + 18, rect.bottom - 18), (rect.left + 28, rect.bottom - 30), 1)
                elif kind == "mud":
                    pygame.draw.ellipse(self.screen, self._blend(accent, "#020617", 0.25), rect.inflate(-42, -58), 1)
                    pygame.draw.ellipse(self.screen, accent, rect.inflate(-62, -72), 1)
                else:
                    pygame.draw.line(self.screen, accent, (rect.left + 8, rect.top + 8), (rect.right - 8, rect.bottom - 8), 1)
                    pygame.draw.line(self.screen, self._blend(accent, "#FFFFFF", 0.18), (rect.left + 18, rect.top + 58), (rect.right - 24, rect.top + 52), 1)

    def _draw_pocket_terrain(self, game, camera):
        tile = WORLD_TILE_SIZE
        start_x = math.floor(camera.x / tile) * tile
        start_y = math.floor(camera.y / tile) * tile
        for x in range(int(start_x), int(camera.x + SCREEN_WIDTH + tile), tile):
            for y in range(int(start_y), int(camera.y + SCREEN_HEIGHT + tile), tile):
                rect = pygame.Rect(int(x - camera.x), int(y - camera.y), tile + 1, tile + 1)
                checker = ((x // tile) + (y // tile)) % 2
                base = (43, 17, 72) if checker else (57, 24, 95)
                pygame.draw.rect(self.screen, base, rect)
                pygame.draw.rect(self.screen, (88, 28, 135), rect, width=1)
                cx = rect.centerx + int(math.sin(game.time_alive * 1.4 + x * 0.01) * 6)
                cy = rect.centery + int(math.cos(game.time_alive * 1.2 + y * 0.01) * 6)
                pygame.draw.circle(self.screen, (126, 34, 206), (cx, cy), 2)
                if checker:
                    pygame.draw.line(self.screen, (105, 44, 160), (rect.left + 14, rect.bottom - 22), (rect.right - 18, rect.top + 26), 1)

    def _draw_olympus_terrain(self, game, camera):
        tile = WORLD_TILE_SIZE
        t = game.time_alive
        start_x = math.floor(camera.x / tile) * tile
        start_y = math.floor(camera.y / tile) * tile
        for x in range(int(start_x), int(camera.x + SCREEN_WIDTH + tile), tile):
            for y in range(int(start_y), int(camera.y + SCREEN_HEIGHT + tile), tile):
                rect = pygame.Rect(int(x - camera.x), int(y - camera.y), tile + 1, tile + 1)
                checker = ((x // tile) + (y // tile)) % 2
                # Golden marble checkerboard
                if checker:
                    base = (218, 185, 107)  # warm gold
                else:
                    base = (245, 236, 210)  # cream marble
                pygame.draw.rect(self.screen, base, rect)
                # Marble veins
                vein_color = (198, 168, 92) if checker else (225, 215, 185)
                pygame.draw.rect(self.screen, vein_color, rect, width=1)
                # Subtle diagonal marble cracks
                if checker:
                    pygame.draw.line(self.screen, (188, 158, 82),
                                     (rect.left + 10, rect.top + 8),
                                     (rect.right - 12, rect.bottom - 10), 1)
                else:
                    pygame.draw.line(self.screen, (215, 205, 175),
                                     (rect.right - 14, rect.top + 6),
                                     (rect.left + 16, rect.bottom - 8), 1)
                # Animated divine sparkles
                sparkle_phase = math.sin(t * 2.8 + x * 0.007 + y * 0.009)
                if sparkle_phase > 0.7:
                    sx = rect.centerx + int(math.sin(t * 1.6 + x * 0.01) * 8)
                    sy = rect.centery + int(math.cos(t * 1.3 + y * 0.01) * 8)
                    alpha_pulse = int(160 + 80 * sparkle_phase)
                    sparkle_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
                    pygame.draw.circle(sparkle_surf, (255, 248, 220, min(255, alpha_pulse)), (6, 6), 3)
                    pygame.draw.circle(sparkle_surf, (255, 215, 0, min(255, alpha_pulse // 2)), (6, 6), 6)
                    self.screen.blit(sparkle_surf, (sx - 6, sy - 6))
        # Floating cloud wisps overlay
        cloud_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(6):
            cx = int((SCREEN_WIDTH * 0.15 * i + t * (18 + i * 7)) % (SCREEN_WIDTH + 200)) - 100
            cy = int(SCREEN_HEIGHT * 0.12 * (i + 1) + math.sin(t * 0.4 + i * 1.5) * 30)
            cloud_w = 140 + i * 20
            cloud_h = 30 + i * 5
            cloud_alpha = int(22 + 10 * math.sin(t * 0.7 + i))
            pygame.draw.ellipse(cloud_overlay, (255, 255, 255, cloud_alpha),
                                (cx, cy, cloud_w, cloud_h))
            pygame.draw.ellipse(cloud_overlay, (255, 248, 220, cloud_alpha // 2),
                                (cx + 20, cy - 8, cloud_w - 40, cloud_h + 8))
        self.screen.blit(cloud_overlay, (0, 0))

    def _draw_hazards(self, game, camera):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for hazard in game.world.iter_visible_hazards(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            rect = hazard.rect
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            pulse = 0.5 + 0.5 * math.sin(game.time_alive * 6 + hazard.pulse)

            if hazard.kind == "fire":
                pygame.draw.rect(overlay, (127, 29, 29, 58), screen_rect.inflate(8, 8), border_radius=10)
                pygame.draw.rect(overlay, (239, 68, 68, 78), screen_rect, border_radius=8)
                pygame.draw.rect(overlay, (251, 146, 60, 150), screen_rect, width=2, border_radius=8)
                for index in range(5):
                    x = screen_rect.left + 12 + index * max(12, screen_rect.width // 5)
                    y = screen_rect.centery + math.sin(game.time_alive * 5 + index) * 10
                    pygame.draw.line(overlay, (254, 215, 170, 170), (x, y + 14), (x + 8, y - 14), 2)
                    pygame.draw.circle(overlay, (255, 247, 237, 120), (x + 8, int(y - 14)), max(2, int(3 + pulse * 2)))
            elif hazard.kind == "ice":
                pygame.draw.rect(overlay, (8, 47, 73, 64), screen_rect.inflate(6, 6), border_radius=10)
                pygame.draw.rect(overlay, (125, 211, 252, 70), screen_rect, border_radius=8)
                pygame.draw.rect(overlay, (186, 230, 253, 150), screen_rect, width=2, border_radius=8)
                for index in range(4):
                    y = screen_rect.top + 16 + index * max(12, screen_rect.height // 4)
                    pygame.draw.line(overlay, (224, 242, 254, 135), (screen_rect.left + 12, y), (screen_rect.right - 12, y - 8), 1)
                pygame.draw.line(overlay, (240, 249, 255, 95), screen_rect.topleft, screen_rect.bottomright, 1)
            elif hazard.kind == "mine":
                center = screen_rect.center
                radius = int(13 + pulse * 3)
                is_dash_mine = str(getattr(hazard, "id", "")).startswith("dash_mine:")
                if is_dash_mine:
                    glow = (34, 211, 238, int(38 + 34 * pulse))
                    body = (8, 47, 73, 240)
                    ring = (103, 232, 249, 220)
                    core = (250, 204, 21, 230)
                    edge = (255, 255, 255, 210)
                    points = [
                        (center[0], center[1] - radius - 2),
                        (center[0] + radius + 6, center[1]),
                        (center[0], center[1] + radius + 2),
                        (center[0] - radius - 6, center[1]),
                    ]
                    pygame.draw.circle(overlay, glow, center, radius + 14)
                    pygame.draw.polygon(overlay, body, points)
                    pygame.draw.polygon(overlay, ring, points, 2)
                    pygame.draw.circle(overlay, core, center, max(3, radius // 3))
                    pygame.draw.line(overlay, edge, (center[0] - 7, center[1] - 7), (center[0] + 7, center[1] + 7), 2)
                    pygame.draw.line(overlay, edge, (center[0] - 7, center[1] + 7), (center[0] + 7, center[1] - 7), 2)
                else:
                    pygame.draw.circle(overlay, (248, 113, 113, int(34 + 36 * pulse)), center, radius + 13)
                    pygame.draw.circle(overlay, (127, 29, 29, 230), center, radius)
                    pygame.draw.circle(overlay, (248, 113, 113, 220), center, radius + 4, 2)
                    pygame.draw.circle(overlay, (254, 226, 226, 220), center, max(3, radius // 3))
                    pygame.draw.line(overlay, (254, 226, 226, 190), (center[0] - 6, center[1]), (center[0] + 6, center[1]), 2)
                    pygame.draw.line(overlay, (254, 226, 226, 190), (center[0], center[1] - 6), (center[0], center[1] + 6), 2)
        self.screen.blit(overlay, (0, 0))

    def _draw_world_objects(self, game, camera):
        if getattr(game, "light_level", 1.0) < 0.35:
            for light in game.world.iter_visible_static_lights(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
                x, y = self.world_to_screen(light.pos, camera)
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 3.0 + light.pos.x)
                color = "#FACC15" if light.kind == "lamp" else "#38BDF8"
                self._draw_soft_circle((x, y), light.radius * (0.94 + pulse * 0.08), color, alpha=58, rings=5)
                pygame.draw.circle(self.screen, hex_color(color), (x, y), 10)
                pygame.draw.circle(self.screen, (255, 247, 237), (x, y), 4)
        for rect in game.world.iter_visible_obstacles(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            shadow = screen_rect.move(4, 6)
            pygame.draw.rect(self.screen, (6, 10, 18), shadow, border_radius=5)
            pygame.draw.rect(self.screen, (31, 41, 55), screen_rect, border_radius=5)
            pygame.draw.rect(self.screen, (15, 23, 42), screen_rect, width=2, border_radius=5)
            pygame.draw.line(self.screen, (71, 85, 105), screen_rect.topleft, screen_rect.topright, 1)
            pygame.draw.line(self.screen, (8, 13, 24), screen_rect.bottomleft, screen_rect.bottomright, 2)
            if screen_rect.width > 52 and screen_rect.height > 34:
                pygame.draw.line(self.screen, (45, 57, 76), (screen_rect.left + 10, screen_rect.top + 10), (screen_rect.right - 12, screen_rect.bottom - 12), 1)

        for item in game.world.iter_visible_destructibles(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            rect = item.rect
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            if item.kind == "special":
                color = (56, 189, 248)
            elif item.kind == "cache":
                color = (245, 158, 11)
            else:
                color = (146, 64, 14)
            if item.hit_flash > 0:
                color = (253, 230, 138)
            pygame.draw.rect(self.screen, (69, 26, 3), screen_rect.move(3, 4), border_radius=4)
            pygame.draw.rect(self.screen, color, screen_rect, border_radius=4)
            pygame.draw.rect(self.screen, self._blend(color, "#020617", 0.42), screen_rect, width=2, border_radius=4)
            pygame.draw.line(self.screen, (254, 215, 170), screen_rect.topleft, screen_rect.bottomright, 1)
            pygame.draw.line(self.screen, self._blend(color, "#FFFFFF", 0.35), (screen_rect.left + 4, screen_rect.top + 4), (screen_rect.right - 5, screen_rect.top + 4), 1)
            if item.kind == "special":
                pygame.draw.circle(self.screen, (224, 242, 254), screen_rect.center, max(4, screen_rect.width // 5), 1)

    def _draw_altars(self, game, camera):
        if not getattr(game, "altars", None):
            return
        for altar in game.altars:
            if not altar.active:
                continue
            x, y = self.world_to_screen(altar.pos, camera)
            pulse = 0.5 + 0.5 * math.sin(game.time_alive * 4.0 + altar.age)

            style = arcade_theme.altar_style(altar.kind)
            color_hex = style["color"]
            accent_hex = "#FFF7D6"

            color = hex_color(color_hex)
            accent = hex_color(accent_hex)
            self._draw_soft_circle((x, y), altar.radius + 18 + pulse * 6, color_hex, alpha=50, rings=4)

            pygame.draw.circle(self.screen, (15, 23, 42), (x, y), int(altar.radius))
            pygame.draw.circle(self.screen, color, (x, y), int(altar.radius * 0.8), 3)

            core_y = y - 16 + math.sin(game.time_alive * 3.5 + altar.age) * 5
            pygame.draw.circle(self.screen, color, (x, int(core_y)), int(6 + pulse * 2))
            pygame.draw.circle(self.screen, accent, (x, int(core_y)), int(2 + pulse))

            label = f"ALTAR {style['label']}"
            font = self.font_small
            if font:
                text_rect = font.get_rect(label, size=13)
                label_rect = pygame.Rect(
                    x - text_rect.width // 2 - 7,
                    int(core_y) - 27,
                    text_rect.width + 14,
                    text_rect.height + 6,
                )
                pygame.draw.rect(self.screen, (3, 7, 18), label_rect)
                pygame.draw.rect(self.screen, accent, label_rect, width=2)
                font.render_to(
                    self.screen,
                    (label_rect.x + 7, label_rect.y + 3),
                    label,
                    (255, 247, 214),
                    size=13,
                )

    def _draw_altar_labels(self, game, camera):
        if not getattr(game, "altars", None) or not self.font_small:
            return
        for altar in game.altars:
            if not altar.active:
                continue
            x, y = self.world_to_screen(altar.pos, camera)
            style = arcade_theme.altar_style(altar.kind)
            label = f"{style['glyph']}  {style['label']}"
            color_hex = style["color"]
            rect = self.font_small.get_rect(label, size=14)
            box = pygame.Rect(x - rect.width // 2 - 8, y - int(altar.radius) - 34, rect.width + 16, rect.height + 8)
            pygame.draw.rect(self.screen, (3, 7, 18), box)
            pygame.draw.rect(self.screen, hex_color(color_hex), box, width=2)
            self.font_small.render_to(self.screen, (box.x + 8, box.y + 4), label, (255, 247, 214), size=14)
