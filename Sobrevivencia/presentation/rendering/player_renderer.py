import math

import pygame
from pygame.math import Vector2

from ...data.constants import *
from ..ui_utils import hex_color

from ..effects.primitives import draw_special_blast


class PlayerRendererMixin:
    def _draw_constructs(self, game, camera):
        for c in getattr(game, 'player_constructs', []):
            x, y = self.world_to_screen(c.pos, camera)
            pulse = math.sin(game.time_alive * 8 + c.pos.x) * 3
            if c.kind in ("turret", "laser_turret", "drone", "robo_minion"):
                color = (245, 158, 11) if c.hit_flash <= 0 else (255, 255, 255)
                if c.kind == "laser_turret":
                    color = (250, 204, 21) if c.hit_flash <= 0 else (255, 255, 255)
                elif c.kind == "drone":
                    color = (56, 189, 248) if c.hit_flash <= 0 else (255, 255, 255)
                elif c.kind == "robo_minion":
                    color = (250, 204, 21) if c.hit_flash <= 0 else (255, 255, 255)
                barrel = Vector2(math.cos(c.angle), math.sin(c.angle))
                side = barrel.rotate(90)
                base_col = (120, 53, 15) if c.kind not in ("drone", "robo_minion") else (8, 47, 73)
                pygame.draw.circle(self.screen, base_col, (x, y), int(c.radius))
                pygame.draw.circle(self.screen, color, (x, y), int(c.radius), 3)
                barrel_end = Vector2(x, y) + barrel * (c.radius + 12 + pulse * 0.3)
                barrel_root = Vector2(x, y) - barrel * 4
                pygame.draw.line(self.screen, color, barrel_root, barrel_end, 3 if c.kind == "drone" else 4)
                pygame.draw.line(self.screen, (254, 243, 199), barrel_end - side * 3, barrel_end + side * 3, 2)
                if c.kind == "laser_turret":
                    pygame.draw.circle(self.screen, (254, 240, 138), (x, y), max(3, int(c.radius * 0.45)))
                if c.kind == "robo_minion":
                    bar_w = 34
                    bar_h = 4
                    fill = max(0.0, min(1.0, 1.0 - c.age / max(0.01, c.duration)))
                    bx = x - bar_w // 2
                    by = y - int(c.radius) - 12
                    pygame.draw.rect(self.screen, (30, 41, 59), (bx, by, bar_w, bar_h), border_radius=2)
                    pygame.draw.rect(self.screen, (250, 204, 21), (bx, by, int(bar_w * fill), bar_h), border_radius=2)
                    pygame.draw.rect(self.screen, (254, 243, 199), (bx, by, bar_w, bar_h), 1, border_radius=2)
            elif c.kind == "barrier":
                color = (14, 165, 233) if c.hit_flash <= 0 else (255, 255, 255)
                r = int(c.radius + pulse)
                pygame.draw.circle(self.screen, (8, 47, 73), (x, y), r)
                pygame.draw.circle(self.screen, color, (x, y), r, 3)
                pygame.draw.circle(self.screen, (186, 230, 253), (x, y), int(r * 0.5), 1)
                pygame.draw.line(self.screen, color, (x - r, y), (x + r, y), 2)
            elif c.kind == "torch":
                pygame.draw.line(self.screen, (139, 69, 19), (x, y + 10), (x, y - 8), 3)
                pygame.draw.circle(self.screen, (100, 100, 100), (x, y - 8), 4)
                flame_pulse = math.sin(game.time_alive * 12 + c.pos.x) * 2
                flame_color = (249, 115, 22) if (game.time_alive * 5) % 2 < 1 else (239, 68, 68)
                pygame.draw.circle(self.screen, flame_color, (x, y - 11), int(5 + flame_pulse))
                pygame.draw.circle(self.screen, (253, 224, 71), (x, y - 10), int(3 + flame_pulse * 0.5))

    def _draw_players(self, game, camera, mouse_pos, aim_from_joystick=False, p2_aim_pos=None):
        aim_positions = {0: mouse_pos}
        aim_modes = {0: aim_from_joystick}
        if p2_aim_pos is not None:
            aim_positions[1] = p2_aim_pos
            aim_modes[1] = True
        for player in game.players:
            self._draw_player(game, camera, player, aim_positions.get(player.player_index, mouse_pos), aim_modes.get(player.player_index, False))

    def _draw_player(self, game, camera, player, mouse_pos, aim_from_joystick=False):
        x, y = self.world_to_screen(player.pos, camera)
        aim = Vector2(mouse_pos) - Vector2(x, y)
        if aim.length_squared() <= 0:
            aim = Vector2(1, 0)
        aim = aim.normalize()
        nose = Vector2(x, y) + aim * (player.radius + 11)
        left = Vector2(x, y) + aim.rotate(132) * (player.radius * 0.86)
        right = Vector2(x, y) + aim.rotate(-132) * (player.radius * 0.86)

        aim_color = hex_color(P2_AIM_COLOR if player.player_index == 1 else P1_AIM_COLOR)
        self._draw_crosshair(player, (x, y), mouse_pos, aim, aim_from_joystick)
        shadow_offset = self._get_shadow_offset(game, player.pos)
        self._draw_shadow((x, y), player.radius, alpha=105, offset=(shadow_offset.x, shadow_offset.y))
        if player.dash_timer > 0:
            dash_alpha = int(55 + 85 * min(1.0, player.dash_timer / max(0.01, DASH_DURATION)))
            for step in range(1, 4):
                trail = Vector2(x, y) - player.dash_dir * step * player.radius * 0.9
                self._draw_soft_circle((trail.x, trail.y), player.radius * (1.0 - step * 0.12), aim_color, alpha=max(18, dash_alpha // (step + 1)), rings=2)
        if player.shield_timer > 0:
            pulse = 5 + int(math.sin(game.time_alive * 12) * 2)
            self._draw_soft_circle((x, y), player.radius + 24 + pulse, COLORS["shield"], alpha=55, rings=3)
            pygame.draw.circle(self.screen, hex_color(COLORS["shield"]), (x, y), int(player.radius + 12 + pulse), 3)
        elif player.invulnerable_timer > 0:
            self._draw_soft_circle((x, y), player.radius + 14, "#CBD5E1", alpha=38, rings=2)
            pygame.draw.circle(self.screen, (148, 163, 184), (x, y), int(player.radius + 7), 2)
        if getattr(game, "omni_kernel_active", False):
            omni_ready = game.omni_active_ready()
            omni_ratio = game.omni_active_charge_ratio()
            omni_color = "#FACC15" if omni_ready else "#38BDF8"
            orbit_radius = int(player.radius + 18 + math.sin(game.time_alive * 5.0 + player.player_index) * 2)
            if omni_ready:
                self._draw_soft_circle((x, y), orbit_radius + 8, omni_color, alpha=34, rings=2)
                for index in range(3):
                    angle = game.time_alive * 2.5 + index * math.tau / 3.0 + player.player_index * 0.4
                    orb = Vector2(x, y) + Vector2(math.cos(angle), math.sin(angle)) * (orbit_radius + 6)
                    pygame.draw.circle(self.screen, hex_color(omni_color), (int(orb.x), int(orb.y)), 4)
            else:
                arc_rect = pygame.Rect(0, 0, (orbit_radius + 6) * 2, (orbit_radius + 6) * 2)
                arc_rect.center = (x, y)
                pygame.draw.circle(self.screen, (30, 41, 59), (x, y), orbit_radius + 6, 2)
                pygame.draw.arc(
                    self.screen,
                    hex_color(omni_color),
                    arc_rect,
                    -math.pi / 2,
                    -math.pi / 2 + math.tau * omni_ratio,
                    4,
                )

        char_data = CHARACTERS[player.char_class]
        color = hex_color(char_data["color"])
        core = hex_color(char_data["core_color"])

        if player.is_down:
            pygame.draw.circle(self.screen, (71, 85, 105), (x, y), int(player.radius))
            pygame.draw.line(self.screen, aim_color, (x - 16, y - 16), (x + 16, y + 16), 4)
            pygame.draw.line(self.screen, aim_color, (x + 16, y - 16), (x - 16, y + 16), 4)
            progress = player.revive_progress / max(0.01, REVIVE_TIME)
            pygame.draw.circle(self.screen, aim_color, (x, y), int(REVIVE_RADIUS), 2)
            self._bar(x - 36, y - 48, 72, 8, progress, COLORS["xp"], COLORS["panel_2"], f"RESGATE J{player.player_index + 1}")
        else:
            self._draw_soft_circle((x, y), player.radius + 11, aim_color, alpha=34, rings=2)
            if not self._draw_player_atlas(player, (x, y), aim):
                pygame.draw.circle(self.screen, color, (x, y), int(player.radius))
                if char_data["shape"] == "circle_triangle":
                    pygame.draw.polygon(self.screen, core, [nose, left, right])
                    pygame.draw.line(self.screen, (224, 242, 254), nose, Vector2(x, y) - aim * player.radius * 0.35, 2)
                elif char_data["shape"] == "circle_square":
                    square_size = int(player.radius * 1.05)
                    square = pygame.Rect(0, 0, square_size, square_size)
                    square.center = (x, y)
                    pygame.draw.rect(self.screen, core, square, border_radius=2)
                    tool_end = Vector2(x, y) + aim * (player.radius * 0.72)
                    pygame.draw.line(self.screen, (254, 243, 199), (x, y), tool_end, 3)
                elif char_data["shape"] == "circle_diamond":
                    diamond = [
                        (x, y - int(player.radius * 0.86)),
                        (x + int(player.radius * 0.72), y),
                        (x, y + int(player.radius * 0.86)),
                        (x - int(player.radius * 0.72), y),
                    ]
                    pygame.draw.polygon(self.screen, core, diamond)
                    blade_tip = Vector2(x, y) + aim * (player.radius * 0.94)
                    blade_root = Vector2(x, y) - aim * (player.radius * 0.18)
                    pygame.draw.line(self.screen, (254, 226, 226), blade_root, blade_tip, 2)
                else:
                    self._draw_star((x, y), int(player.radius * 0.62), int(player.radius * 0.28), core, points=5)

        pygame.draw.circle(self.screen, (15, 23, 42), (x, y), int(player.radius), 2)
        pygame.draw.circle(self.screen, self._blend(color, "#FFFFFF", 0.32), (x - int(player.radius * 0.28), y - int(player.radius * 0.32)), max(2, int(player.radius * 0.18)))

        if not player.is_down and player.ammo_magazine <= 0:
            pulse = (pygame.time.get_ticks() // 250) % 2 == 0
            if pulse:
                msg = "SEM MUNICAO!" if player.ammo_reserve <= 0 else "RECARREGANDO"
                color = hex_color(COLORS["health"]) if player.ammo_reserve <= 0 else hex_color(COLORS["coin"])
                ammo_text, text_rect = self.font_small.render(msg, color)
                text_rect.center = (x, y - int(player.radius) - 20)
                
                # Create a semi-transparent background
                bg_surf = pygame.Surface((text_rect.width + 12, text_rect.height + 6), pygame.SRCALPHA)
                pygame.draw.rect(bg_surf, (15, 23, 42, 200), bg_surf.get_rect(), border_radius=4)
                self.screen.blit(bg_surf, (text_rect.x - 6, text_rect.y - 3))
                self.screen.blit(ammo_text, text_rect)

        # Relic aura: two rotating fire circles
        inv = game.get_inventory(player.player_index)
        has_relic = any(item.is_relic for item in inv.active_items())
        if has_relic:
            aura_r = 82
            overlay_aura = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(2):
                angle = game.relic_aura_angle + i * math.pi
                cx2 = int(x + math.cos(angle) * aura_r * 0.72)
                cy2 = int(y + math.sin(angle) * aura_r * 0.72)
                pygame.draw.circle(overlay_aura, (250, 160, 50, 170), (cx2, cy2), 12)
                pygame.draw.circle(overlay_aura, (255, 210, 100, 90), (cx2, cy2), 20)
            pygame.draw.circle(overlay_aura, (167, 139, 250, 40), (x, y), aura_r)
            pygame.draw.circle(overlay_aura, (250, 180, 50, 100), (x, y), aura_r, 2)
            self.screen.blit(overlay_aura, (0, 0))

    def _draw_player_atlas(self, player, center, aim):
        try:
            atlas = self.assets.character_atlas(player.char_class)
            frame = atlas.frame("idle_0")
        except (FileNotFoundError, KeyError, pygame.error):
            return False

        size = max(18, int(player.radius * 2.7))
        angle = -math.degrees(math.atan2(aim.y, aim.x))
        angle = int(round(angle / 15.0) * 15)
        cache = getattr(self, "_player_sprite_cache", None)
        if cache is None:
            cache = {}
            self._player_sprite_cache = cache
        key = (player.char_class, "idle_0", size, angle)
        sprite = cache.get(key)
        if sprite is None:
            sprite = pygame.transform.smoothscale(frame, (size, size))
            sprite = pygame.transform.rotate(sprite, angle)
            cache[key] = sprite
        rect = sprite.get_rect(center=(int(center[0]), int(center[1])))
        self.screen.blit(sprite, rect)
        return True

    def _draw_special_blast(self, game, camera):
        draw_special_blast(
            self.screen,
            game,
            camera,
            self.world_to_screen,
            (SCREEN_WIDTH, SCREEN_HEIGHT),
        )

    def _draw_crosshair(self, player, start_pos, end_pos, aim_dir, is_joystick):
        if player.is_down:
            return

        cx, cy = int(end_pos[0]), int(end_pos[1])
        px, py = int(start_pos[0]), int(start_pos[1])
        ticks = pygame.time.get_ticks()

        # Determine state color
        base_color = hex_color(P2_AIM_COLOR if player.player_index == 1 else P1_AIM_COLOR)
        if player.reload_timer > 0:
            base_color = hex_color(COLORS["coin"])  # Golden/Orange when reloading
        elif player.ammo_magazine <= 0:
            base_color = hex_color(COLORS["danger"])  # Red when out of ammo

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # 1. Fading Dashed Laser Sight
        dist = Vector2(end_pos).distance_to(Vector2(start_pos))
        dash_len, gap_len = 8, 8
        if dist > 30:
            num_dashes = int(dist / (dash_len + gap_len))
            for i in range(num_dashes):
                # Fade out as it gets further from player (closer to crosshair)
                alpha = int(255 * (1.0 - (i / max(1, num_dashes))))
                if alpha <= 0: continue
                start_dash = Vector2(start_pos) + aim_dir * (i * (dash_len + gap_len) + 24)
                end_dash = start_dash + aim_dir * dash_len
                # Don't draw past the crosshair
                if start_dash.distance_to(Vector2(start_pos)) > dist - 20: break
                pygame.draw.line(overlay, (*base_color, alpha // 2), start_dash, end_dash, 2)
                pygame.draw.line(overlay, (*base_color, alpha), start_dash, end_dash, 1)

        # 2. Modern Rotating Reticle
        pulse = 0.5 + 0.5 * math.sin(ticks * 0.008)
        outer_r = 16 + int(pulse * 2)
        ring_alpha = 150 + int(105 * pulse)
        
        # Draw 4 rotating segments
        angle_offset = (ticks * 0.15) % 360
        rect = pygame.Rect(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
        for i in range(4):
            start_angle = math.radians(angle_offset + i * 90)
            end_angle = math.radians(angle_offset + i * 90 + 45)  # 45 deg arc
            pygame.draw.arc(overlay, (*base_color, ring_alpha), rect, start_angle, end_angle, 2)

        # Inner Precision Cross
        cross_len = 6
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            pygame.draw.line(overlay, (*base_color, 255), 
                             (cx + dx * 5, cy + dy * 5), 
                             (cx + dx * (5 + cross_len), cy + dy * (5 + cross_len)), 2)

        # Center Dot
        pygame.draw.circle(overlay, (255, 255, 255, 255), (cx, cy), 2)
        pygame.draw.circle(overlay, (*base_color, 180), (cx, cy), 4, 1)

        # 3. Dynamic Reloading Ring
        if player.reload_timer > 0:
            reload_progress = 1.0 - (player.reload_timer / max(0.01, player.reload_duration))
            rel_r = outer_r + 6
            rel_rect = pygame.Rect(cx - rel_r, cy - rel_r, rel_r * 2, rel_r * 2)
            pygame.draw.circle(overlay, (*base_color, 40), (cx, cy), rel_r, 3)
            pygame.draw.arc(overlay, (*base_color, 255), rel_rect, math.pi / 2, math.pi / 2 + (2 * math.pi * reload_progress), 3)

        # 4. Joystick Directional Arrow Indicator
        if is_joystick:
            arrow_tip = Vector2(cx, cy) + aim_dir * (outer_r + 8 + pulse * 3)
            side = aim_dir.rotate(90)
            arrow_left = arrow_tip - aim_dir * 8 + side * 5
            arrow_right = arrow_tip - aim_dir * 8 - side * 5
            pygame.draw.polygon(overlay, (*base_color, 220), 
                                [(arrow_tip.x, arrow_tip.y), 
                                 (arrow_left.x, arrow_left.y), 
                                 (arrow_right.x, arrow_right.y)])

        self.screen.blit(overlay, (0, 0))
