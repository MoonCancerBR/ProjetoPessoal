import math

import pygame
from pygame.math import Vector2

from ...data.constants import *
from ..ui_utils import hex_color

class ProjectileRendererMixin:
    def _draw_projectiles(self, game, camera):
        for projectile in game.projectiles:
            x, y = self.world_to_screen(projectile.pos, camera)
            if getattr(projectile, "color", ""):
                color = projectile.color
            elif projectile.freeze:
                color = COLORS["projectile_freeze"]
            elif projectile.poison:
                color = COLORS["poison"]
            else:
                color = COLORS["projectile"]
            rgb = hex_color(color)
            if projectile.vel.length_squared() > 0:
                tail = Vector2(x, y) - projectile.vel.normalize() * (projectile.radius * getattr(projectile, "trail_scale", 3.2))
                line_w = 3 if getattr(projectile, "style", "") in ("huntress_burst", "engineer_laser") else 2
                pygame.draw.line(self.screen, self._blend(rgb, "#FFFFFF", 0.25), (int(tail.x), int(tail.y)), (x, y), line_w)
            halo_alpha = 58 if getattr(projectile, "style", "") == "vanguard_pellet" else 44
            self._draw_soft_circle((x, y), projectile.radius + 6, rgb, alpha=halo_alpha, rings=2)
            if getattr(game, "light_level", 1.0) < 0.15:
                outline = (103, 232, 249) if getattr(projectile, "owner", 0) >= 0 else (248, 113, 113)
                pygame.draw.circle(self.screen, outline, (x, y), int(projectile.radius + 5), 2)
            shell_radius = int(projectile.radius + (3 if getattr(projectile, "style", "") == "huntress_burst" else 2))
            pygame.draw.circle(self.screen, rgb, (x, y), shell_radius)
            core_outline = (127, 29, 29) if getattr(projectile, "style", "") == "vanguard_pellet" else (8, 47, 73)
            pygame.draw.circle(self.screen, core_outline, (x, y), int(projectile.radius), 1)

    def _draw_item_events(self, game, camera):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for event in game.item_events:
            event_type = event.get("type", "storm")
            if event_type == "arrow_rain":
                alpha = max(0, min(1, event["timer"] * 2))
                pos = event["pos"] - camera
                radius = event["radius"]
                rgba = (56, 189, 248, int(120 * alpha))
                pygame.draw.circle(overlay, (14, 165, 233, int(26 * alpha)), (int(pos.x), int(pos.y)), int(radius))
                pygame.draw.circle(overlay, rgba, (int(pos.x), int(pos.y)), int(radius), 2)
                pygame.draw.circle(overlay, (224, 242, 254, int(120 * alpha)), (int(pos.x), int(pos.y)), int(radius * 0.55), 1)
                for i in range(5):
                    ox = math.sin(game.time_alive * 20 + i) * radius * 0.8
                    oy = math.cos(game.time_alive * 15 + i) * radius * 0.8
                    tip = (pos.x + ox, pos.y + oy)
                    pygame.draw.line(overlay, (224, 242, 254, int(190 * alpha)), (tip[0] - 8, tip[1] - 34), tip, 2)
                    pygame.draw.polygon(overlay, (56, 189, 248, int(170 * alpha)), [tip, (tip[0] - 4, tip[1] - 10), (tip[0] + 5, tip[1] - 8)])
            elif event_type == "blood_zone":
                age = event.get("age", 0.0)
                duration = max(0.01, event.get("duration", 2.0))
                alpha = max(0.0, 1.0 - age / duration)
                pos = event["pos"] - camera
                radius = event["radius"]
                pulse = 0.82 + 0.18 * math.sin(game.time_alive * 9.5 + radius * 0.02)
                outer = int(radius * pulse)
                inner = int(radius * 0.58)
                pygame.draw.circle(overlay, (18, 18, 24, int(82 * alpha)), (int(pos.x), int(pos.y)), outer)
                pygame.draw.circle(overlay, (127, 29, 29, int(155 * alpha)), (int(pos.x), int(pos.y)), outer, 3)
                pygame.draw.circle(overlay, (239, 68, 68, int(95 * alpha)), (int(pos.x), int(pos.y)), inner, 2)
                for index in range(6):
                    ang = game.time_alive * 1.8 + index * math.tau / 6
                    orb = Vector2(pos.x, pos.y) + Vector2(math.cos(ang), math.sin(ang)) * (radius * 0.72)
                    pygame.draw.circle(overlay, (220, 38, 38, int(180 * alpha)), (int(orb.x), int(orb.y)), 4)
            elif event_type == "danger_circle":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 1))
                alpha = max(0, 1 - age / duration)
                pos = event["pos"] - camera
                radius = event["radius"]
                pulse_radius = radius * (0.86 + 0.14 * math.sin(game.time_alive * 18))
                warn = hex_color(event.get("color", COLORS["danger"]))
                pygame.draw.circle(overlay, (*warn, int(44 + 60 * alpha)), (int(pos.x), int(pos.y)), int(pulse_radius))
                pygame.draw.circle(overlay, (254, 226, 226, int(210 * alpha)), (int(pos.x), int(pos.y)), int(radius), 4)
            elif event_type == "danger_line":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 1))
                alpha = max(0, 1 - age / duration)
                start = event["start"] - camera
                end = event["end"] - camera
                width = int(event.get("width", 42))
                warn = hex_color(event.get("color", COLORS["danger"]))
                pygame.draw.line(overlay, (*warn, int(72 + 75 * alpha)), (start.x, start.y), (end.x, end.y), width)
                pygame.draw.line(overlay, (254, 226, 226, int(220 * alpha)), (start.x, start.y), (end.x, end.y), 3)
            elif event_type == "laser":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 0.2))
                alpha = max(0, 1 - age / duration)
                start = event["start"] - camera
                end = event["end"] - camera
                width = int(event.get("width", 44))
                beam = hex_color(event.get("color", "#FB923C"))
                pygame.draw.line(overlay, (*beam, int(210 * alpha)), (start.x, start.y), (end.x, end.y), width)
                pygame.draw.line(overlay, (255, 247, 237, int(245 * alpha)), (start.x, start.y), (end.x, end.y), max(3, width // 5))
            elif event_type == "explosion":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 0.2))
                alpha = max(0, 1 - age / duration)
                pos = event["pos"] - camera
                progress = min(1.0, age / duration)
                current_radius = event["radius"] * (1 - alpha**2)
                core_r = max(4, int(event["radius"] * 0.18 * alpha))
                pygame.draw.circle(overlay, (251, 146, 60, int(80 * alpha)), (int(pos.x), int(pos.y)), int(current_radius))
                pygame.draw.circle(overlay, (254, 240, 138, int(230 * alpha)), (int(pos.x), int(pos.y)), int(current_radius), max(2, int(5 * alpha)))
                pygame.draw.circle(overlay, (255, 247, 237, int(190 * alpha)), (int(pos.x), int(pos.y)), core_r)
                for i in range(6):
                    ang = game.time_alive * 2.0 + i * math.tau / 6
                    inner = Vector2(pos.x, pos.y) + Vector2(math.cos(ang), math.sin(ang)) * current_radius * 0.35
                    outer = Vector2(pos.x, pos.y) + Vector2(math.cos(ang), math.sin(ang)) * current_radius * (0.72 + 0.12 * progress)
                    pygame.draw.line(overlay, (253, 186, 116, int(135 * alpha)), inner, outer, 2)
            elif event_type == "summon_pulse":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 2.0))
                alpha = max(0, 1 - age / duration)
                pulse = 0.5 + 0.5 * math.sin(age * 10)
                pos = event["pos"] - camera
                radius = int(event["radius"] * (0.85 + 0.15 * pulse))
                pygame.draw.circle(overlay, (192, 132, 252, int(110 * alpha)), (int(pos.x), int(pos.y)), radius)
                pygame.draw.circle(overlay, (216, 180, 254, int(200 * alpha)), (int(pos.x), int(pos.y)), radius, 4)
            elif event_type == "omni_burst":
                age = event.get("age", 0.0)
                duration = max(0.01, event.get("duration", 1.0))
                alpha = max(0.0, 1.0 - age / duration)
                pos = event["pos"] - camera
                base_radius = event.get("radius", 220)
                color = hex_color(event.get("color", "#BAE6FD"))
                ring_radius = int(base_radius * (0.45 + 0.70 * (age / duration)))
                core_radius = max(8, int(base_radius * 0.16 * alpha))
                pygame.draw.circle(overlay, (*color, int(40 * alpha)), (int(pos.x), int(pos.y)), ring_radius)
                pygame.draw.circle(overlay, (*color, int(190 * alpha)), (int(pos.x), int(pos.y)), ring_radius, 4)
                pygame.draw.circle(overlay, (255, 255, 255, int(210 * alpha)), (int(pos.x), int(pos.y)), core_radius, 2)
                for index in range(3):
                    angle = age * 8.0 + index * math.tau / 3.0
                    orbit = Vector2(math.cos(angle), math.sin(angle)) * max(18, ring_radius * 0.62)
                    shard = Vector2(pos.x, pos.y) + orbit
                    pygame.draw.circle(overlay, (*color, int(220 * alpha)), (int(shard.x), int(shard.y)), max(4, int(8 * alpha)))
            else:
                if "start" not in event or "end" not in event:
                    continue
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 1))
                alpha = max(0, 1 - age / duration)
                start = event["start"] - camera
                end = event["end"] - camera
                color = hex_color(event.get("color", "#FFFFFF"))
                rgba = (*color, int(220 * alpha))
                pygame.draw.line(overlay, rgba, (start.x, start.y), (end.x, end.y), 4)
                pygame.draw.circle(overlay, rgba, (int(end.x), int(end.y)), 18, 2)
        self.screen.blit(overlay, (0, 0))

    def _draw_slashes(self, game, camera):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for slash in game.slashes:
            progress = min(1.0, slash.age / max(0.01, slash.duration))
            origin = slash.origin - camera
            base_angle = math.atan2(slash.direction.y, slash.direction.x)
            start = base_angle - slash.arc * 0.5
            end = base_angle + slash.arc * 0.5
            points = [(origin.x, origin.y)]
            steps = 12
            radius = slash.radius * (0.82 + 0.18 * progress)
            for i in range(steps + 1):
                angle = start + (end - start) * (i / steps)
                points.append((origin.x + math.cos(angle) * radius, origin.y + math.sin(angle) * radius))
            alpha = int(135 * (1 - progress * 0.55))
            fill = hex_color(getattr(slash, "color", "") or "#FDE047")
            edge = hex_color(getattr(slash, "edge_color", "") or "#FEF3C7")
            pygame.draw.polygon(overlay, (*fill, alpha), points)
            pygame.draw.lines(overlay, (*edge, 225), False, points[1:], 4)
            inner = [(origin.x, origin.y)]
            inner_radius = radius * 0.72
            for i in range(steps + 1):
                angle = start + (end - start) * (i / steps)
                inner.append((origin.x + math.cos(angle) * inner_radius, origin.y + math.sin(angle) * inner_radius))
            accent = self._blend(fill, "#FFFFFF", 0.28)
            pygame.draw.lines(overlay, (*accent, int(120 * (1 - progress))), False, inner[1:], 2)
        self.screen.blit(overlay, (0, 0))
