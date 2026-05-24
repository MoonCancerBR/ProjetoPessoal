import math

import pygame

from ...config.runtime import TweeningFallback, optional_import
from ...data.constants import *
from ..ui_utils import hex_color

pytweening = optional_import("pytweening") or TweeningFallback


class FeedbackRendererMixin:
    def _draw_floaters(self, game, camera):
        for floater in game.floaters:
            duration = floater["duration"]
            age = floater["age"]
            progress = min(1.0, age / duration)
            ftype = floater.get("type", "damage")

            if ftype == "alert":
                # Alertas de acao: fonte maior, fundo, borda, sobem mais rapido
                eased_offset = pytweening.easeOutCubic(progress) * 60
                fade_start = 0.4
                fade_progress = max(0.0, (progress - fade_start) / (1.0 - fade_start))
                alpha = int(255 * (1.0 - pytweening.easeInQuad(fade_progress)))
                x, y = self.world_to_screen(floater["pos"], camera)
                color = hex_color(floater["color"])
                surf, rect = self.font_small.render(floater["text"], color)
                pad_x, pad_y = 10, 5
                bg = pygame.Surface((rect.width + pad_x * 2, rect.height + pad_y * 2), pygame.SRCALPHA)
                bg_alpha = min(180, alpha)
                pygame.draw.rect(bg, (10, 5, 5, bg_alpha), bg.get_rect(), border_radius=6)
                pygame.draw.rect(bg, (*color, bg_alpha), bg.get_rect(), width=1, border_radius=6)
                bx = x - rect.width // 2 - pad_x
                by = int(y - 28 - eased_offset) - pad_y
                self.screen.blit(bg, (bx, by))
                surf.set_alpha(alpha)
                self.screen.blit(surf, (bx + pad_x, by + pad_y))
            else:
                # Floaters de dano: comportamento original leve e rapido
                eased_offset = pytweening.easeOutQuad(progress) * 40
                alpha = int(255 * (1.0 - pytweening.easeInQuad(progress)))
                x, y = self.world_to_screen(floater["pos"], camera)
                surf, rect = self.font_tiny.render(floater["text"], hex_color(floater["color"]))
                surf.set_alpha(alpha)
                self.screen.blit(surf, (x - rect.width // 2, y - 14 - eased_offset))

    def _draw_escort_event(self, game, camera):
        if not getattr(game, 'escort_event_active', False):
            return
            
        if getattr(game, 'escort_state', '') == 'seeking_spawn':
            sx, sy = self.world_to_screen(game.escort_spawn_pos, camera)
            self._draw_soft_circle((sx, sy), 150, '#3B82F6', alpha=40, rings=3)
            
        if getattr(game, 'escort_state', '') == 'escorting':
            ex, ey = self.world_to_screen(game.escort_extract_pos, camera)
            pulse = math.sin(game.time_alive * 3) * 15
            self._draw_soft_circle((ex, ey), 150 + pulse, '#10B981', alpha=50, rings=4)
            
            for npc in getattr(game, 'escort_npcs', []):
                if npc.hp <= 0: continue
                nx, ny = self.world_to_screen(npc.pos, camera)
                shadow_offset = self._get_shadow_offset(game, npc.pos)
                self._draw_shadow((nx, ny), npc.radius, alpha=110, offset=(shadow_offset.x, shadow_offset.y))
                
                pos_int = (int(nx), int(ny))
                rad_int = int(npc.radius)
                
                if npc.kind == 'executive':
                    fill_col = (255, 255, 255) if npc.hit_flash > 0 else (15, 23, 42)
                    pygame.draw.circle(self.screen, fill_col, pos_int, rad_int)
                    
                    if npc.hit_flash <= 0:
                        pygame.draw.line(self.screen, (245, 158, 11), (nx, ny - rad_int//2), (nx, ny + rad_int//2), 3)
                        
                    pygame.draw.circle(self.screen, (251, 191, 36), pos_int, rad_int, 2)
                else:
                    fill_col = (255, 255, 255) if npc.hit_flash > 0 else (56, 189, 248)
                    pygame.draw.circle(self.screen, fill_col, pos_int, rad_int)
                    
                    if npc.hit_flash <= 0:
                        pygame.draw.rect(self.screen, (3, 105, 161), (nx - 4, ny - 2, 8, 5), border_radius=1)
                        
                    pygame.draw.circle(self.screen, (148, 163, 184), pos_int, rad_int, 1)
                
                hp_pct = max(0, npc.hp / npc.max_hp)
                bar_w = 32 if npc.kind == 'executive' else 26
                bar_h = 4
                bar_x = nx - bar_w / 2
                bar_y = ny - npc.radius - 8
                pygame.draw.rect(self.screen, (200, 0, 0), (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(self.screen, (0, 200, 0), (bar_x, bar_y, bar_w * hp_pct, bar_h))
