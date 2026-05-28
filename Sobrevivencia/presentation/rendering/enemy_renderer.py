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
            if enemy.frozen_timer > 0:
                color = (125, 211, 252)
            shadow_offset = self._get_shadow_offset(game, enemy.pos)
            self._draw_shadow((x, y), enemy.radius, alpha=86, offset=(shadow_offset.x, shadow_offset.y))
            if enemy.kind in ("chromatic", "miniboss", "sapper") or enemy.action:
                self._draw_soft_circle((x, y), enemy.radius + 18, color, alpha=44, rings=3)
            pygame.draw.circle(self.screen, color, (x, y), int(enemy.radius))
            pygame.draw.circle(self.screen, self._blend(color, "#FFFFFF", 0.22), (x - int(enemy.radius * 0.25), y - int(enemy.radius * 0.28)), max(2, int(enemy.radius * 0.18)))
            if enemy.poison_timer > 0:
                pygame.draw.circle(self.screen, hex_color(COLORS["poison"]), (x, y), int(enemy.radius + 4), 2)
            if getattr(enemy, "bleed_timer", 0) > 0:
                pygame.draw.circle(self.screen, (248, 113, 113), (x, y), int(enemy.radius + 7), 2)
            pygame.draw.circle(self.screen, (25, 25, 35), (x, y), int(enemy.radius), 2)
            if enemy.kind == "miniboss":
                pulse = int(4 + math.sin(game.time_alive * 5) * 2)
                pygame.draw.circle(self.screen, (254, 226, 226), (x, y), int(enemy.radius + pulse), 3)
                pygame.draw.circle(self.screen, (196, 181, 253), (x - 14, y - 10), 5)
                pygame.draw.circle(self.screen, (196, 181, 253), (x + 14, y - 10), 5)
                pygame.draw.line(self.screen, (49, 46, 129), (x - 18, y + 12), (x + 18, y + 12), 3)
                if enemy.action:
                    pygame.draw.circle(self.screen, hex_color(COLORS["danger"]), (x, y), int(enemy.radius + 12), 2)
            elif enemy.kind == "chromatic":
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), int(enemy.radius + 6), 2)
                self._draw_star((x, y), max(7, int(enemy.radius * 0.55)), max(3, int(enemy.radius * 0.25)), (255, 255, 255), points=4, angle_offset=enemy.phase)
                if enemy.lifetime > 0:
                    arc_rect = pygame.Rect(x - enemy.radius - 8, y - enemy.radius - 8, int((enemy.radius + 8) * 2), int((enemy.radius + 8) * 2))
                    pygame.draw.arc(self.screen, (226, 232, 240), arc_rect, -math.pi / 2, -math.pi / 2 + math.tau * (enemy.lifetime / CHROMATIC_LIFETIME), 3)
            elif enemy.kind == "brute":
                pygame.draw.circle(self.screen, (254, 226, 226), (x - 7, y - 5), 3)
                pygame.draw.circle(self.screen, (254, 226, 226), (x + 7, y - 5), 3)
                pygame.draw.line(self.screen, (127, 29, 29), (x - 13, y + 8), (x + 13, y + 8), 2)
            elif enemy.kind == "runner":
                pygame.draw.polygon(self.screen, (255, 228, 230), [(x, y - 7), (x + 8, y + 7), (x - 8, y + 7)])
                pygame.draw.line(self.screen, (15, 23, 42), (x, y - 12), (x, y + 10), 1)
            elif enemy.kind == "spitter":
                pygame.draw.circle(self.screen, (236, 252, 203), (x + 5, y - 4), 4)
                if enemy.action:
                    pygame.draw.circle(self.screen, (190, 242, 100), (x, y), int(enemy.radius + 8), 2)
                    pygame.draw.circle(self.screen, (236, 252, 203), (x, y), int(enemy.radius * 0.45), 1)
            elif enemy.kind == "bulwark":
                pygame.draw.circle(self.screen, (203, 213, 225), (x, y), int(enemy.radius + 8), 2)
                pygame.draw.rect(self.screen, (15, 23, 42), (x - 11, y - 7, 22, 14), 2, border_radius=3)
                pygame.draw.line(self.screen, (226, 232, 240), (x - 16, y - 13), (x + 16, y - 13), 2)
            elif enemy.kind == "sapper":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 12 + enemy.id)
                pygame.draw.circle(self.screen, (254, 240, 138), (x, y), int(enemy.radius + 5 + pulse * 3), 2)
                pygame.draw.line(self.screen, (113, 63, 18), (x - 6, y), (x + 6, y), 2)
                pygame.draw.line(self.screen, (113, 63, 18), (x, y - 6), (x, y + 6), 2)
            elif enemy.kind == "minion":
                glow_r = int(enemy.radius + 5)
                pygame.draw.circle(self.screen, (216, 180, 254), (x, y), glow_r, 2)
                pygame.draw.circle(self.screen, (192, 132, 252), (x, y), int(enemy.radius * 0.45))
            elif enemy.kind == "phantom":
                phase = enemy.phase
                if getattr(enemy, "intangible", False):
                    # Intangível: anel pulsante, translúcido, com vórtice rotativo
                    pulse = 0.5 + 0.5 * math.sin(game.time_alive * 8 + enemy.id)
                    glow_r = int(enemy.radius + 10 + pulse * 6)
                    phantom_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(phantom_surf, (216, 180, 254, int(60 + 60 * pulse)), (glow_r + 2, glow_r + 2), glow_r)
                    pygame.draw.circle(phantom_surf, (243, 232, 255, int(140 + 60 * pulse)), (glow_r + 2, glow_r + 2), glow_r, 2)
                    self.screen.blit(phantom_surf, (x - glow_r - 2, y - glow_r - 2))
                    # Vórtice: 4 linhas rotativas
                    for i in range(4):
                        ang = game.time_alive * 3 + i * math.tau / 4
                        px1 = x + math.cos(ang) * (enemy.radius * 0.5)
                        py1 = y + math.sin(ang) * (enemy.radius * 0.5)
                        px2 = x + math.cos(ang + 0.6) * (enemy.radius * 1.2 + pulse * 4)
                        py2 = y + math.sin(ang + 0.6) * (enemy.radius * 1.2 + pulse * 4)
                        pygame.draw.line(self.screen, (216, 180, 254, 180), (int(px1), int(py1)), (int(px2), int(py2)), 1)
                    # Texto "INTANGIVEL" flutuante
                    if self.font_tiny:
                        lbl, lrect = self.font_tiny.render("IMUNE", (216, 180, 254))
                        self.screen.blit(lbl, (x - lrect.width // 2, y - int(enemy.radius) - 16))
                else:
                    # Tangível: glow sólido roxo + caveira simplificada
                    pulse = 0.5 + 0.5 * math.sin(game.time_alive * 6 + enemy.id)
                    pygame.draw.circle(self.screen, (147, 51, 234), (x, y), int(enemy.radius + 6 + pulse * 3), 2)
                    pygame.draw.circle(self.screen, (216, 180, 254), (x, y), int(enemy.radius * 0.4))
                    # Olhos brilhantes
                    eye_off = int(enemy.radius * 0.25)
                    pygame.draw.circle(self.screen, (255, 255, 255), (x - eye_off, y - 2), 3)
                    pygame.draw.circle(self.screen, (255, 255, 255), (x + eye_off, y - 2), 3)
                    pygame.draw.circle(self.screen, (192, 132, 252), (x - eye_off, y - 2), 2)
                    pygame.draw.circle(self.screen, (192, 132, 252), (x + eye_off, y - 2), 2)
            elif enemy.kind == "golem":
                # Corpo rochoso quadrado com camadas e fissuras
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 2 + enemy.id)
                r_size = int(enemy.radius * 0.85)
                # Sombra/pedra base
                pygame.draw.rect(self.screen, (51, 65, 85), (x - r_size - 3, y - r_size + 3, r_size * 2 + 6, r_size * 2 + 6), border_radius=6)
                # Corpo principal
                pygame.draw.rect(self.screen, (71, 85, 105), (x - r_size, y - r_size, r_size * 2, r_size * 2), border_radius=5)
                # Camada de mineral
                pygame.draw.rect(self.screen, (100, 116, 139), (x - r_size, y - r_size, r_size * 2, r_size * 2), 3, border_radius=5)
                # Fissuras internas (linhas irregulares)
                pygame.draw.line(self.screen, (30, 41, 59), (x - r_size + 4, y - 3), (x + r_size - 6, y + 5), 2)
                pygame.draw.line(self.screen, (30, 41, 59), (x - 5, y - r_size + 4), (x + 7, y + r_size - 5), 2)
                # Brilho magnético (core azulado pulsante)
                core_r = max(3, int(enemy.radius * 0.28 + pulse * 2))
                pygame.draw.circle(self.screen, (56, 189, 248, 200), (x, y), core_r)
                pygame.draw.circle(self.screen, (186, 230, 253), (x, y), core_r, 1)
                # Indicador de imunidade a knockback
                if self.font_tiny:
                    lbl, lrect = self.font_tiny.render("IMUNE KB", (100, 116, 139))
                    self.screen.blit(lbl, (x - lrect.width // 2, y - int(enemy.radius) - 16))
            elif enemy.kind == "necromancer":
                # Aura de invocação com anéis orbitais e símbolo central
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 4 + enemy.id)
                summon_cd = getattr(enemy, "summon_cooldown", 12.0)
                charge_pct = max(0.0, 1.0 - summon_cd / 12.0)  # 0=recargando, 1=pronto
                # Anel externo pulsante
                outer_r = int(enemy.radius + 10 + pulse * 4)
                pygame.draw.circle(self.screen, (88, 28, 135), (x, y), outer_r, 2)
                pygame.draw.circle(self.screen, (192, 132, 252), (x, y), outer_r, 1)
                # Runas orbitais (3 esferas girando)
                for i in range(3):
                    ang = game.time_alive * 2.5 + i * math.tau / 3
                    rx = x + int(math.cos(ang) * (enemy.radius + 5))
                    ry = y + int(math.sin(ang) * (enemy.radius + 5))
                    pygame.draw.circle(self.screen, (216, 180, 254), (rx, ry), 3)
                    pygame.draw.circle(self.screen, (255, 255, 255), (rx, ry), 1)
                # Barra de recarga da invocação (arco)
                if charge_pct > 0.02:
                    arc_r = int(enemy.radius + 14)
                    arc_rect = pygame.Rect(x - arc_r, y - arc_r, arc_r * 2, arc_r * 2)
                    arc_color = (216, 180, 254) if charge_pct < 0.99 else (255, 220, 80)
                    pygame.draw.arc(self.screen, arc_color, arc_rect,
                                    -math.pi / 2, -math.pi / 2 + math.tau * charge_pct, 3)
                # Centro escuro com olho brilhante
                pygame.draw.circle(self.screen, (30, 10, 50), (x, y), int(enemy.radius * 0.55))
                pygame.draw.circle(self.screen, (192, 132, 252), (x, y), int(enemy.radius * 0.3 + pulse * 2))

            if enemy.health < enemy.max_health:
                bar_w = int(enemy.radius * 2.0)
                bar_rect = pygame.Rect(x - bar_w // 2, y - int(enemy.radius) - 10, bar_w, 4)
                pygame.draw.rect(self.screen, (64, 20, 26), bar_rect)
                bar_rect.width = int(bar_w * max(0, enemy.health / enemy.max_health))
                pygame.draw.rect(self.screen, (248, 113, 113), bar_rect)
