import math

import pygame

from ...data.constants import SCREEN_HEIGHT, SCREEN_WIDTH


class MinimapRendererMixin:
    def _draw_minimap(self, game):
        r = self._s(55)
        margin = self._s(20)
        cx = margin + r
        cy = SCREEN_HEIGHT - margin - r
        
        # Translucent glassmorphic circular panel with custom Pygame surface channel alpha
        minimap_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(minimap_surf, (15, 23, 42, 190), (r, r), r)
        
        radar_range = 1600.0  # Detection radius in world game coordinates
        scale = r / radar_range
        
        player = game.player
        if player.is_down and getattr(game, 'multiplayer', False) and getattr(game, 'player2', None):
            player = game.player2
            
        # Draw active Altares on radar
        if getattr(game, 'altars', None):
            for altar in game.altars:
                if not altar.active:
                    continue
                diff = altar.pos - player.pos
                if diff.length() < radar_range:
                    ax = r + diff.x * scale
                    ay = r + diff.y * scale
                    
                    if altar.kind == "weapon_altar":
                        color = (239, 68, 68) # Red
                    elif altar.kind == "stamps_altar":
                        color = (6, 182, 212) # Cyan
                    elif altar.kind == "skill_altar":
                        color = (139, 92, 246) # Purple
                    elif altar.kind == "black_market_altar":
                        color = (34, 197, 94) # Green
                    else:
                        color = (245, 158, 11) # Gold
                        
                    pulse = 1.0 + 0.3 * math.sin(game.time_alive * 8.0 + altar.age)
                    pygame.draw.circle(minimap_surf, color, (int(ax), int(ay)), int(self._s(4) * pulse))
                    pygame.draw.circle(minimap_surf, (255, 255, 255), (int(ax), int(ay)), int(self._s(4) * pulse), 1)

        # Draw Mini-boss / Boss threats
        if getattr(game, 'enemies', None):
            for enemy in game.enemies:
                if enemy.kind in ("miniboss", "reaper", "harbinger"):
                    diff = enemy.pos - player.pos
                    if diff.length() < radar_range:
                        ex = r + diff.x * scale
                        ey = r + diff.y * scale
                        pulse = 1.0 + 0.4 * math.sin(game.time_alive * 12.0)
                        if enemy.kind == "reaper":
                            pygame.draw.circle(minimap_surf, (220, 38, 38), (int(ex), int(ey)), int(self._s(5) * pulse))
                            pygame.draw.circle(minimap_surf, (255, 245, 245), (int(ex), int(ey)), int(self._s(2.5) * pulse))
                        elif enemy.kind == "harbinger":
                            pygame.draw.circle(minimap_surf, (127, 29, 29), (int(ex), int(ey)), int(self._s(4) * pulse))
                        else:
                            pygame.draw.circle(minimap_surf, (249, 115, 22), (int(ex), int(ey)), int(self._s(3) * pulse))

        # Draw stamp drops on radar (highlighted diamonds)
        if getattr(game, 'drops', None):
            for drop in game.drops:
                diff = drop.pos - player.pos
                if diff.length() < radar_range:
                    dx = r + diff.x * scale
                    dy = r + diff.y * scale
                    if drop.kind == "stamp":
                        try:
                            from Sobrevivencia.data.stamps import stamp_hud_color, Stamp
                            col_hex = stamp_hud_color(Stamp(key=drop.value))
                            from Sobrevivencia.presentation.ui_utils import hex_color as _hc
                            col = _hc(col_hex)
                        except Exception:
                            col = (255, 200, 50)
                        pulse = 1.0 + 0.5 * math.sin(game.time_alive * 10.0 + drop.pos.x)
                        sz = max(2, int(self._s(5) * pulse))
                        diamond = [
                            (int(dx), int(dy - sz)),
                            (int(dx + sz), int(dy)),
                            (int(dx), int(dy + sz)),
                            (int(dx - sz), int(dy)),
                        ]
                        pygame.draw.polygon(minimap_surf, col, diamond)
                        pygame.draw.polygon(minimap_surf, (255, 255, 255), diamond, 1)
                    elif drop.kind == "item_box":
                        pulse = 1.0 + 0.3 * math.sin(game.time_alive * 6.0 + drop.pos.y)
                        sz = max(2, int(self._s(4) * pulse))
                        pygame.draw.rect(minimap_surf, (56, 189, 248), (int(dx - sz), int(dy - sz), sz * 2, sz * 2))
                        pygame.draw.rect(minimap_surf, (255, 255, 255), (int(dx - sz), int(dy - sz), sz * 2, sz * 2), 1)

        # Draw P1 (Center of radar)
        pygame.draw.circle(minimap_surf, (56, 189, 248), (r, r), self._s(3))
        
        # Draw P2 if Coop active
        if getattr(game, 'multiplayer', False) and getattr(game, 'player2', None):
            p2 = game.player2
            if not p2.is_down:
                diff = p2.pos - player.pos
                if diff.length() < radar_range:
                    p2x = r + diff.x * scale
                    p2y = r + diff.y * scale
                    pygame.draw.circle(minimap_surf, (239, 68, 68), (int(p2x), int(p2y)), self._s(3))
                    
        # Blit minimap back to main viewport
        self.screen.blit(minimap_surf, (cx - r, cy - r))
        
        # Compass metal ring border
        pygame.draw.circle(self.screen, (30, 41, 59), (cx, cy), r, self._s(2))
        pygame.draw.circle(self.screen, (59, 130, 246, 100), (cx, cy), r + self._s(1), self._s(1))
        
        # Compass directional tick marks (N, S, W, E)
        tick = self._s(4)
        pygame.draw.line(self.screen, (255, 255, 255, 120), (cx, cy - r), (cx, cy - r + tick), 1) # N
        pygame.draw.line(self.screen, (255, 255, 255, 120), (cx, cy + r), (cx, cy + r - tick), 1) # S
        pygame.draw.line(self.screen, (255, 255, 255, 120), (cx - r, cy), (cx - r + tick, cy), 1) # W
        pygame.draw.line(self.screen, (255, 255, 255, 120), (cx + r, cy), (cx + r - tick, cy), 1) # E
        labels = (
            ("N", cx - self.font_tiny.get_rect("N").width // 2, cy - r + self._s(6)),
            ("S", cx - self.font_tiny.get_rect("S").width // 2, cy + r - self._s(17)),
            ("W", cx - r + self._s(7), cy - self._s(7)),
            ("E", cx + r - self._s(14), cy - self._s(7)),
        )
        for label, lx, ly in labels:
            self.font_tiny.render_to(self.screen, (lx, ly), label, (203, 213, 225))
