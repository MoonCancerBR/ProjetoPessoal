# Código Completo Atualizado — EnemyRendererMixin

import math
import pygame
from pygame.math import Vector2
from ...data.constants import *
from ..ui_utils import hex_color


class EnemyRendererMixin:
    def _draw_enemies(self, game, camera):
        for enemy in game.enemies:
            x, y = self.world_to_screen(enemy.pos, camera)

            color = (255, 255, 255) if enemy.hit_flash > 0 else hex_color(enemy.color)

            if enemy.kind == "chromatic" and enemy.hit_flash <= 0:
                palette = [
                    (34, 211, 238),
                    (236, 72, 153),
                    (250, 204, 21),
                    (74, 222, 128),
                    (167, 139, 250),
                ]
                color = palette[int(game.time_alive * 14 + enemy.id) % len(palette)]

            if enemy.frozen_timer > 0 or getattr(game, "omni_time_freeze_active", lambda: False)():
                color = (125, 211, 252)

            shadow_offset = self._get_shadow_offset(game, enemy.pos)

            self._draw_shadow(
                (x, y),
                enemy.radius,
                alpha=86,
                offset=(shadow_offset.x, shadow_offset.y)
            )

            if enemy.kind in ("chromatic", "miniboss", "sapper", "reaper", "god") or enemy.action:
                self._draw_soft_circle(
                    (x, y),
                    enemy.radius + 18,
                    color,
                    alpha=44,
                    rings=3
                )
            elif getattr(game, "light_level", 1.0) < 0.15:
                self._draw_soft_circle((x, y), enemy.radius + 10, "#FB7185", alpha=34, rings=2)

            pygame.draw.circle(self.screen, color, (x, y), int(enemy.radius))

            pygame.draw.circle(
                self.screen,
                self._blend(color, "#FFFFFF", 0.22),
                (x - int(enemy.radius * 0.25), y - int(enemy.radius * 0.28)),
                max(2, int(enemy.radius * 0.18))
            )

            if enemy.poison_timer > 0:
                pygame.draw.circle(
                    self.screen,
                    hex_color(COLORS["poison"]),
                    (x, y),
                    int(enemy.radius + 4),
                    2
                )

            if getattr(enemy, "bleed_timer", 0) > 0:
                pygame.draw.circle(
                    self.screen,
                    (248, 113, 113),
                    (x, y),
                    int(enemy.radius + 7),
                    2
                )

            if getattr(enemy, "blood_mark_timer", 0) > 0:
                mark_level = max(1, getattr(enemy, "blood_mark_level", 1))
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 11 + enemy.id)
                mark_radius = int(enemy.radius + 10 + pulse * 3 + min(5, mark_level))
                pygame.draw.circle(self.screen, (185, 28, 28), (x, y), mark_radius, 2)
                pygame.draw.circle(self.screen, (254, 226, 226), (x, y), max(3, int(enemy.radius * 0.26 + pulse)), 1)
                pygame.draw.line(self.screen, (220, 38, 38), (x - 5, y - 5), (x + 5, y + 5), 2)
                pygame.draw.line(self.screen, (220, 38, 38), (x + 5, y - 5), (x - 5, y + 5), 2)

            pygame.draw.circle(
                self.screen,
                (25, 25, 35),
                (x, y),
                int(enemy.radius),
                2
            )
            if getattr(game, "light_level", 1.0) < 0.15:
                pygame.draw.circle(self.screen, (254, 202, 202), (x, y), int(enemy.radius + 3), 2)

            # =========================================================
            # MINIBOSS — COLOSSO RITUALÍSTICO
            # =========================================================

            if enemy.kind == "reaper":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 7 + enemy.id)
                aura_r = int(enemy.radius + 28 + pulse * 12)

                self._draw_soft_circle((x, y), aura_r + 12, "#7F1D1D", alpha=95, rings=5)
                self._draw_soft_circle((x, y), aura_r, "#111827", alpha=72, rings=4)
                pygame.draw.circle(self.screen, (185, 28, 28), (x, y), int(enemy.radius + 9), 4)
                pygame.draw.circle(self.screen, (255, 245, 245), (x, y), int(enemy.radius + 17 + pulse * 5), 2)

                for i in range(4):
                    ang = game.time_alive * 1.6 + i * math.tau / 4
                    outer = Vector2(x, y) + Vector2(math.cos(ang), math.sin(ang)) * (enemy.radius + 18 + pulse * 5)
                    tang = Vector2(-math.sin(ang), math.cos(ang))
                    blade_a = outer + tang * 10
                    blade_b = outer - tang * 10
                    blade_tip = outer + Vector2(math.cos(ang), math.sin(ang)) * 10
                    pygame.draw.polygon(self.screen, (248, 113, 113), [blade_a, blade_b, blade_tip])

                skull = pygame.Rect(x - 18, y - 16, 36, 32)
                pygame.draw.ellipse(self.screen, (15, 23, 42), skull)
                pygame.draw.ellipse(self.screen, (220, 38, 38), skull, 3)
                pygame.draw.circle(self.screen, (254, 226, 226), (x - 7, y - 2), 4)
                pygame.draw.circle(self.screen, (254, 226, 226), (x + 7, y - 2), 4)
                pygame.draw.line(self.screen, (248, 113, 113), (x - 10, y + 9), (x + 10, y + 9), 2)

                if enemy.action:
                    pygame.draw.circle(self.screen, (254, 242, 242), (x, y), int(enemy.radius + 28 + pulse * 8), 3)
                if self.font_tiny:
                    label = f"CEIFADOR {getattr(game, 'reaper_defeats', 0) + 1}"
                    lbl, lrect = self.font_tiny.render(label, (254, 202, 202))
                    self.screen.blit(lbl, (x - lrect.width // 2, y - int(enemy.radius) - 28))

            elif enemy.kind == "god":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 5 + enemy.id)
                aura_r = int(enemy.radius + 36 + pulse * 18)

                # Massive golden/cyan divine aura
                self._draw_soft_circle((x, y), aura_r + 20, "#FDE047", alpha=110, rings=6)
                self._draw_soft_circle((x, y), aura_r + 8, "#22D3EE", alpha=55, rings=4)
                self._draw_soft_circle((x, y), aura_r, "#FFFFFF", alpha=30, rings=3)

                # Outer divine rings
                pygame.draw.circle(self.screen, (255, 215, 0), (x, y), int(enemy.radius + 14), 4)
                pygame.draw.circle(self.screen, (34, 211, 238), (x, y), int(enemy.radius + 22 + pulse * 8), 2)

                # Rotating celestial rings
                for i in range(8):
                    ang = game.time_alive * 2.0 + i * math.tau / 8
                    outer = Vector2(x, y) + Vector2(math.cos(ang), math.sin(ang)) * (enemy.radius + 26 + pulse * 10)
                    inner = Vector2(x, y) + Vector2(math.cos(ang + 0.4), math.sin(ang + 0.4)) * (enemy.radius * 0.5)
                    pygame.draw.line(self.screen, (255, 248, 220), inner, outer, 2)
                    pygame.draw.circle(self.screen, (255, 215, 0), (int(outer.x), int(outer.y)), 4)
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(outer.x), int(outer.y)), 2)

                # Counter-rotating ring
                for i in range(6):
                    ang = -game.time_alive * 1.4 + i * math.tau / 6
                    orb = Vector2(x, y) + Vector2(math.cos(ang), math.sin(ang)) * (enemy.radius + 16)
                    pygame.draw.circle(self.screen, (34, 211, 238), (int(orb.x), int(orb.y)), 3)

                # Divine halo above head
                halo_y = y - int(enemy.radius) - 18 + int(math.sin(game.time_alive * 3.0) * 3)
                halo_rect = pygame.Rect(x - 20, halo_y - 5, 40, 10)
                pygame.draw.ellipse(self.screen, (255, 215, 0), halo_rect, 2)
                pygame.draw.ellipse(self.screen, (255, 248, 220), halo_rect.inflate(-6, -2), 1)

                # Core divine body
                skull_w = int(enemy.radius * 1.3)
                skull_h = int(enemy.radius * 1.1)
                skull = pygame.Rect(x - skull_w // 2, y - skull_h // 2, skull_w, skull_h)
                pygame.draw.ellipse(self.screen, (15, 23, 42), skull)
                pygame.draw.ellipse(self.screen, (255, 215, 0), skull, 3)

                # Glowing eyes
                eye_pulse = int(200 + 55 * math.sin(game.time_alive * 8.0))
                eye_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(eye_surf, (255, 215, 0, eye_pulse), (6, 10), 5)
                pygame.draw.circle(eye_surf, (255, 215, 0, eye_pulse), (14, 10), 5)
                pygame.draw.circle(eye_surf, (255, 255, 255, 255), (6, 10), 2)
                pygame.draw.circle(eye_surf, (255, 255, 255, 255), (14, 10), 2)
                self.screen.blit(eye_surf, (x - 10, y - 12))

                # Mouth line
                pygame.draw.line(self.screen, (255, 215, 0), (x - 8, y + 8), (x + 8, y + 8), 2)

                # Action indicator
                if enemy.action:
                    pygame.draw.circle(self.screen, (255, 248, 220), (x, y), int(enemy.radius + 34 + pulse * 12), 3)

                # Label
                if self.font_tiny:
                    label = '"GOD"'
                    lbl, lrect = self.font_tiny.render(label, (255, 215, 0))
                    self.screen.blit(lbl, (x - lrect.width // 2, y - int(enemy.radius) - 40))

            elif enemy.kind == "harbinger":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 6 + enemy.id)
                aura_r = int(enemy.radius + 24 + pulse * 10)

                self._draw_soft_circle((x, y), aura_r, "#4C1D95", alpha=78, rings=5)
                pygame.draw.circle(self.screen, (76, 29, 149), (x, y), int(enemy.radius + 7), 4)
                pygame.draw.circle(self.screen, (167, 139, 250), (x, y), int(enemy.radius + 15 + pulse * 5), 2)

                for i in range(8):
                    ang = -game.time_alive * 1.8 + i * math.tau / 8
                    outer = Vector2(x, y) + Vector2(math.cos(ang), math.sin(ang)) * (enemy.radius + 20 + pulse * 6)
                    inner = Vector2(x, y) + Vector2(math.cos(ang + 0.35), math.sin(ang + 0.35)) * (enemy.radius * 0.55)
                    pygame.draw.line(self.screen, (139, 92, 246), inner, outer, 2)
                    pygame.draw.circle(self.screen, (192, 132, 252), (int(outer.x), int(outer.y)), 3)

                skull_w = int(enemy.radius * 1.25)
                skull_h = int(enemy.radius * 1.05)
                skull = pygame.Rect(x - skull_w // 2, y - skull_h // 2, skull_w, skull_h)
                pygame.draw.ellipse(self.screen, (30, 10, 45), skull)
                pygame.draw.ellipse(self.screen, (109, 40, 217), skull, 3)

                if enemy.action:
                    pygame.draw.circle(self.screen, (254, 240, 138), (x, y), int(enemy.radius + 27 + pulse * 8), 3)
                if self.font_tiny:
                    label = f"ARAUTO {getattr(game, 'harbinger_defeats', 0) + 1}"
                    lbl, lrect = self.font_tiny.render(label, (254, 202, 202))
                    self.screen.blit(lbl, (x - lrect.width // 2, y - int(enemy.radius) - 26))

            elif enemy.kind == "miniboss":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 3)

                outer_r = int(enemy.radius + 8 + pulse * 4)

                pygame.draw.circle(self.screen, (120, 40, 160), (x, y), outer_r, 3)
                pygame.draw.circle(self.screen, (220, 180, 255), (x, y), outer_r + 6, 1)

                for i in range(6):
                    ang = game.time_alive * 0.7 + i * math.tau / 6

                    rx = x + math.cos(ang) * (enemy.radius + 12)
                    ry = y + math.sin(ang) * (enemy.radius + 12)

                    pygame.draw.circle(
                        self.screen,
                        (192, 132, 252),
                        (int(rx), int(ry)),
                        4
                    )

                for i in range(5):
                    ang = i * math.tau / 5 + game.time_alive * 0.3

                    x1 = x + math.cos(ang) * 10
                    y1 = y + math.sin(ang) * 10

                    x2 = x + math.cos(ang) * (enemy.radius - 6)
                    y2 = y + math.sin(ang) * (enemy.radius - 6)

                    pygame.draw.line(
                        self.screen,
                        (255, 90, 120),
                        (x1, y1),
                        (x2, y2),
                        2
                    )

                core_r = int(enemy.radius * 0.42 + pulse * 3)

                pygame.draw.circle(self.screen, (45, 10, 70), (x, y), core_r)
                pygame.draw.circle(self.screen, (220, 180, 255), (x, y), core_r, 2)

                if enemy.action:
                    pygame.draw.circle(
                        self.screen,
                        hex_color(COLORS["danger"]),
                        (x, y),
                        int(enemy.radius + 18 + pulse * 6),
                        3
                    )

            # =========================================================
            # CHROMATIC
            # =========================================================

            elif enemy.kind == "chromatic":
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 255),
                    (x, y),
                    int(enemy.radius + 6),
                    2
                )

                self._draw_star(
                    (x, y),
                    max(7, int(enemy.radius * 0.55)),
                    max(3, int(enemy.radius * 0.25)),
                    (255, 255, 255),
                    points=4,
                    angle_offset=enemy.phase
                )

                if enemy.lifetime > 0:
                    arc_rect = pygame.Rect(
                        x - enemy.radius - 8,
                        y - enemy.radius - 8,
                        int((enemy.radius + 8) * 2),
                        int((enemy.radius + 8) * 2)
                    )

                    pygame.draw.arc(
                        self.screen,
                        (226, 232, 240),
                        arc_rect,
                        -math.pi / 2,
                        -math.pi / 2 + math.tau * (
                            enemy.lifetime / CHROMATIC_LIFETIME
                        ),
                        3
                    )

            # =========================================================
            # BRUTE — MASSA GRAVITACIONAL
            # =========================================================

            elif enemy.kind == "brute":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 3 + enemy.id)

                for r in range(3):
                    pygame.draw.circle(
                        self.screen,
                        (120 + r * 20, 40, 60),
                        (x, y),
                        int(enemy.radius - r * 5),
                        2
                    )

                crack_color = (255, 90, 90)

                pygame.draw.line(
                    self.screen,
                    crack_color,
                    (x - 12, y - 6),
                    (x + 3, y + 2),
                    2
                )

                pygame.draw.line(
                    self.screen,
                    crack_color,
                    (x + 2, y + 2),
                    (x + 10, y + 11),
                    2
                )

                core_r = max(4, int(enemy.radius * 0.24 + pulse * 2))

                pygame.draw.circle(self.screen, (255, 120, 120), (x, y), core_r)
                pygame.draw.circle(self.screen, (255, 220, 220), (x, y), core_r, 1)

            # =========================================================
            # RUNNER — FRAGMENTO CINÉTICO
            # =========================================================

            elif enemy.kind == "runner":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 12 + enemy.id)

                angle = enemy.phase if hasattr(enemy, "phase") else 0

                size = enemy.radius + 4

                pts = []

                for i in range(3):
                    ang = angle + i * math.tau / 3

                    pts.append((
                        x + math.cos(ang) * size,
                        y + math.sin(ang) * size
                    ))

                pygame.draw.polygon(self.screen, (255, 245, 250), pts, 2)

                core_r = max(2, int(enemy.radius * 0.3 + pulse * 2))

                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), core_r)

                for i in range(3):
                    trail_ang = angle + math.pi + (i - 1) * 0.25

                    tx = x + math.cos(trail_ang) * (enemy.radius + 6)
                    ty = y + math.sin(trail_ang) * (enemy.radius + 6)

                    pygame.draw.line(
                        self.screen,
                        (255, 220, 240),
                        (x, y),
                        (tx, ty),
                        2
                    )

            # =========================================================
            # SPITTER — ORGANISMO CORROSIVO
            # =========================================================

            elif enemy.kind == "spitter":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 5 + enemy.id)

                pygame.draw.circle(
                    self.screen,
                    (132, 204, 22),
                    (x, y),
                    int(enemy.radius + 5 + pulse * 2),
                    2
                )

                for i in range(4):
                    ang = game.time_alive * 2 + i * math.tau / 4

                    bx = x + math.cos(ang) * (enemy.radius * 0.65)
                    by = y + math.sin(ang) * (enemy.radius * 0.65)

                    pygame.draw.circle(
                        self.screen,
                        (217, 249, 157),
                        (int(bx), int(by)),
                        3
                    )

                core_r = max(4, int(enemy.radius * 0.35))

                pygame.draw.circle(self.screen, (236, 252, 203), (x, y), core_r)

                if enemy.action:
                    for i in range(6):
                        ang = i * math.tau / 6 + game.time_alive * 4

                        px = x + math.cos(ang) * (enemy.radius + 12)
                        py = y + math.sin(ang) * (enemy.radius + 12)

                        pygame.draw.line(
                            self.screen,
                            (190, 242, 100),
                            (int(px), int(py)),
                            (x, y),
                            2
                        )

            # =========================================================
            # BULWARK — FORTALEZA AMBULANTE
            # =========================================================

            elif enemy.kind == "bulwark":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 2 + enemy.id)

                pygame.draw.circle(
                    self.screen,
                    (148, 163, 184),
                    (x, y),
                    int(enemy.radius + 10),
                    2
                )

                for i in range(6):
                    ang = game.time_alive * 0.5 + i * math.tau / 6

                    hx = x + math.cos(ang) * (enemy.radius * 0.75)
                    hy = y + math.sin(ang) * (enemy.radius * 0.75)

                    pygame.draw.circle(
                        self.screen,
                        (226, 232, 240),
                        (int(hx), int(hy)),
                        4,
                        1
                    )

                shield_w = int(enemy.radius * 1.4)
                shield_h = int(enemy.radius * 0.8)

                pygame.draw.rect(
                    self.screen,
                    (30, 41, 59),
                    (x - shield_w // 2, y - shield_h // 2, shield_w, shield_h),
                    border_radius=6
                )

                pygame.draw.rect(
                    self.screen,
                    (148, 163, 184),
                    (x - shield_w // 2, y - shield_h // 2, shield_w, shield_h),
                    2,
                    border_radius=6
                )

            # =========================================================
            # SAPPER — REATOR INSTÁVEL
            # =========================================================

            elif enemy.kind == "sapper":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 14 + enemy.id)

                outer_r = int(enemy.radius + 4 + pulse * 5)

                pygame.draw.circle(
                    self.screen,
                    (250, 204, 21),
                    (x, y),
                    outer_r,
                    2
                )

                for i in range(3):
                    ang = game.time_alive * 3 + i * math.tau / 3

                    px = x + math.cos(ang) * (enemy.radius * 0.5)
                    py = y + math.sin(ang) * (enemy.radius * 0.5)

                    pygame.draw.circle(
                        self.screen,
                        (255, 240, 180),
                        (int(px), int(py)),
                        3
                    )

                pygame.draw.circle(
                    self.screen,
                    (120, 53, 15),
                    (x, y),
                    int(enemy.radius * 0.45)
                )

                for i in range(3):
                    ang1 = i * math.tau / 3
                    ang2 = ang1 + 0.6

                    x1 = x + math.cos(ang1) * 4
                    y1 = y + math.sin(ang1) * 4

                    x2 = x + math.cos(ang2) * 12
                    y2 = y + math.sin(ang2) * 12

                    pygame.draw.line(
                        self.screen,
                        (255, 220, 120),
                        (x1, y1),
                        (x2, y2),
                        2
                    )

            # =========================================================
            # MINION — FRAGMENTO INVOCADO
            # =========================================================

            elif enemy.kind == "minion":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 8 + enemy.id)

                for i in range(4):
                    ang = game.time_alive * 2 + i * math.tau / 4

                    fx = x + math.cos(ang) * (enemy.radius * 0.7)
                    fy = y + math.sin(ang) * (enemy.radius * 0.7)

                    pygame.draw.circle(
                        self.screen,
                        (233, 213, 255),
                        (int(fx), int(fy)),
                        2
                    )

                pygame.draw.circle(
                    self.screen,
                    (192, 132, 252),
                    (x, y),
                    int(enemy.radius * 0.5 + pulse * 2)
                )

                pygame.draw.circle(
                    self.screen,
                    (255, 255, 255),
                    (x, y),
                    max(2, int(enemy.radius * 0.18))
                )

            # =========================================================
            # PHANTOM
            # =========================================================

            elif enemy.kind == "phantom":
                phase = enemy.phase

                if getattr(enemy, "intangible", False):
                    pulse = 0.5 + 0.5 * math.sin(game.time_alive * 8 + enemy.id)
                    glow_r = int(enemy.radius + 10 + pulse * 6)

                    phantom_surf = pygame.Surface(
                        (glow_r * 2 + 4, glow_r * 2 + 4),
                        pygame.SRCALPHA
                    )

                    pygame.draw.circle(
                        phantom_surf,
                        (216, 180, 254, int(60 + 60 * pulse)),
                        (glow_r + 2, glow_r + 2),
                        glow_r
                    )

                    pygame.draw.circle(
                        phantom_surf,
                        (243, 232, 255, int(140 + 60 * pulse)),
                        (glow_r + 2, glow_r + 2),
                        glow_r,
                        2
                    )

                    self.screen.blit(
                        phantom_surf,
                        (x - glow_r - 2, y - glow_r - 2)
                    )

                    for i in range(4):
                        ang = game.time_alive * 3 + i * math.tau / 4

                        px1 = x + math.cos(ang) * (enemy.radius * 0.5)
                        py1 = y + math.sin(ang) * (enemy.radius * 0.5)

                        px2 = x + math.cos(ang + 0.6) * (
                            enemy.radius * 1.2 + pulse * 4
                        )

                        py2 = y + math.sin(ang + 0.6) * (
                            enemy.radius * 1.2 + pulse * 4
                        )

                        pygame.draw.line(
                            self.screen,
                            (216, 180, 254, 180),
                            (int(px1), int(py1)),
                            (int(px2), int(py2)),
                            1
                        )

                    if self.font_tiny:
                        lbl, lrect = self.font_tiny.render(
                            "IMUNE",
                            (216, 180, 254)
                        )

                        self.screen.blit(
                            lbl,
                            (x - lrect.width // 2, y - int(enemy.radius) - 16)
                        )

                else:
                    pulse = 0.5 + 0.5 * math.sin(game.time_alive * 6 + enemy.id)

                    pygame.draw.circle(
                        self.screen,
                        (147, 51, 234),
                        (x, y),
                        int(enemy.radius + 6 + pulse * 3),
                        2
                    )

                    pygame.draw.circle(
                        self.screen,
                        (216, 180, 254),
                        (x, y),
                        int(enemy.radius * 0.4)
                    )

            # =========================================================
            # GOLEM
            # =========================================================

            elif enemy.kind == "golem":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 2 + enemy.id)

                r_size = int(enemy.radius * 0.85)

                pygame.draw.rect(
                    self.screen,
                    (51, 65, 85),
                    (x - r_size - 3, y - r_size + 3,
                     r_size * 2 + 6, r_size * 2 + 6),
                    border_radius=6
                )

                pygame.draw.rect(
                    self.screen,
                    (71, 85, 105),
                    (x - r_size, y - r_size,
                     r_size * 2, r_size * 2),
                    border_radius=5
                )

                pygame.draw.rect(
                    self.screen,
                    (100, 116, 139),
                    (x - r_size, y - r_size,
                     r_size * 2, r_size * 2),
                    3,
                    border_radius=5
                )

                pygame.draw.line(
                    self.screen,
                    (30, 41, 59),
                    (x - r_size + 4, y - 3),
                    (x + r_size - 6, y + 5),
                    2
                )

                pygame.draw.line(
                    self.screen,
                    (30, 41, 59),
                    (x - 5, y - r_size + 4),
                    (x + 7, y + r_size - 5),
                    2
                )

                core_r = max(3, int(enemy.radius * 0.28 + pulse * 2))

                pygame.draw.circle(
                    self.screen,
                    (56, 189, 248),
                    (x, y),
                    core_r
                )

                pygame.draw.circle(
                    self.screen,
                    (186, 230, 253),
                    (x, y),
                    core_r,
                    1
                )

                if self.font_tiny:
                    lbl, lrect = self.font_tiny.render(
                        "IMUNE KB",
                        (100, 116, 139)
                    )

                    self.screen.blit(
                        lbl,
                        (x - lrect.width // 2, y - int(enemy.radius) - 16)
                    )

            # =========================================================
            # NECROMANCER
            # =========================================================

            elif enemy.kind == "necromancer":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 4 + enemy.id)

                summon_cd = getattr(enemy, "summon_cooldown", 12.0)
                charge_pct = max(0.0, 1.0 - summon_cd / 12.0)

                outer_r = int(enemy.radius + 10 + pulse * 4)

                pygame.draw.circle(
                    self.screen,
                    (88, 28, 135),
                    (x, y),
                    outer_r,
                    2
                )

                pygame.draw.circle(
                    self.screen,
                    (192, 132, 252),
                    (x, y),
                    outer_r,
                    1
                )

                for i in range(3):
                    ang = game.time_alive * 2.5 + i * math.tau / 3

                    rx = x + int(math.cos(ang) * (enemy.radius + 5))
                    ry = y + int(math.sin(ang) * (enemy.radius + 5))

                    pygame.draw.circle(
                        self.screen,
                        (216, 180, 254),
                        (rx, ry),
                        3
                    )

                    pygame.draw.circle(
                        self.screen,
                        (255, 255, 255),
                        (rx, ry),
                        1
                    )

                if charge_pct > 0.02:
                    arc_r = int(enemy.radius + 14)

                    arc_rect = pygame.Rect(
                        x - arc_r,
                        y - arc_r,
                        arc_r * 2,
                        arc_r * 2
                    )

                    arc_color = (
                        (216, 180, 254)
                        if charge_pct < 0.99
                        else (255, 220, 80)
                    )

                    pygame.draw.arc(
                        self.screen,
                        arc_color,
                        arc_rect,
                        -math.pi / 2,
                        -math.pi / 2 + math.tau * charge_pct,
                        3
                    )

                pygame.draw.circle(
                    self.screen,
                    (30, 10, 50),
                    (x, y),
                    int(enemy.radius * 0.55)
                )

                pygame.draw.circle(
                    self.screen,
                    (192, 132, 252),
                    (x, y),
                    int(enemy.radius * 0.3 + pulse * 2)
                )

            # =========================================================
            # HEALTH BAR
            # =========================================================

            if enemy.health < enemy.max_health:
                bar_w = int(enemy.radius * 2.0)

                bar_rect = pygame.Rect(
                    x - bar_w // 2,
                    y - int(enemy.radius) - 10,
                    bar_w,
                    4
                )

                pygame.draw.rect(self.screen, (64, 20, 26), bar_rect)

                bar_rect.width = int(
                    bar_w * max(0, enemy.health / enemy.max_health)
                )

                pygame.draw.rect(self.screen, (248, 113, 113), bar_rect)
