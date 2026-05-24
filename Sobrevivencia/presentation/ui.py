import math

import pygame
import pygame.freetype
from pygame.math import Vector2

if __package__:
    from ..config.runtime import NullGUIManager, logger, optional_import
    from ..data.constants import *
    from .ui_utils import hex_color
else:
    from Sobrevivencia.config.runtime import NullGUIManager, logger, optional_import
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.presentation.ui_utils import hex_color


if __package__:
    from .menus.hud import HudMenu
    from .menus.inventory_menu import InventoryMenu
    from .menus.inventory_gui import InventoryGUI
    from .menus.shop_menus import ShopMenus
    from .menus.system_menus import SystemMenus
    from .menus.encyclopedia_menu import EncyclopediaMenu
    from .menus.ui_components import UIComponentFactory, sync_windows_for_state
    from .animation_manager import AnimationManager
    from .particle_manager import ParticleManager
    from .effects.primitives import EffectSurfaceCache, draw_shadow, draw_soft_circle, draw_star
    from .rendering.assets import AssetRegistry
    from .rendering.entity_renderer import EntityRendererMixin
    from .rendering.world_renderer import WorldRendererMixin

else:
    from Sobrevivencia.presentation.menus.hud import HudMenu
    from Sobrevivencia.presentation.menus.inventory_menu import InventoryMenu
    from Sobrevivencia.presentation.menus.inventory_gui import InventoryGUI
    from Sobrevivencia.presentation.menus.shop_menus import ShopMenus
    from Sobrevivencia.presentation.menus.system_menus import SystemMenus
    from Sobrevivencia.presentation.menus.encyclopedia_menu import EncyclopediaMenu
    from Sobrevivencia.presentation.menus.ui_components import UIComponentFactory, sync_windows_for_state
    from Sobrevivencia.presentation.animation_manager import AnimationManager
    from Sobrevivencia.presentation.particle_manager import ParticleManager
    from Sobrevivencia.presentation.effects.primitives import EffectSurfaceCache, draw_shadow, draw_soft_circle, draw_star
    from Sobrevivencia.presentation.rendering.assets import AssetRegistry
    from Sobrevivencia.presentation.rendering.entity_renderer import EntityRendererMixin
    from Sobrevivencia.presentation.rendering.world_renderer import WorldRendererMixin

moderngl = optional_import("moderngl")
np = optional_import("numpy")
pygame_gui = optional_import("pygame_gui")


class UI(WorldRendererMixin, EntityRendererMixin, HudMenu, InventoryGUI, InventoryMenu, ShopMenus, SystemMenus, EncyclopediaMenu):
    def __init__(self, screen):
        self.screen_original = screen
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen = self.game_surface  # Redireciona desenhos legados para a superfície offscreen
        self.ctx = None
        if moderngl is not None and np is not None:
            try:
                self.ctx = moderngl.create_context()
                logger.info(f"Contexto ModernGL criado: {self.ctx.info}")

                # ModernGL Setup
                self.quad_buffer = self.ctx.buffer(np.array([
                    # x, y, u, v
                    -1.0,  1.0, 0.0, 0.0, # TL
                     1.0,  1.0, 1.0, 0.0, # TR
                    -1.0, -1.0, 0.0, 1.0, # BL
                     1.0,  1.0, 1.0, 0.0, # TR
                     1.0, -1.0, 1.0, 1.0, # BR
                    -1.0, -1.0, 0.0, 1.0, # BL
                ], dtype='f4'))

                self.prog = self.ctx.program(
                    vertex_shader='''
                        #version 330
                        in vec2 in_vert;
                        in vec2 in_texcoord;
                        out vec2 v_texcoord;
                        void main() {
                            gl_Position = vec4(in_vert, 0.0, 1.0);
                            v_texcoord = in_texcoord;
                        }
                    ''',
                    fragment_shader='''
                        #version 330
                        uniform sampler2D Texture;
                        uniform vec2 ScreenResolution;
                        uniform vec3 AmbientColor;

                        #define MAX_LIGHTS 64
                        uniform int NumLights;
                        uniform vec4 Lights[MAX_LIGHTS];
                        uniform vec3 LightColors[MAX_LIGHTS];

                        in vec2 v_texcoord;
                        out vec4 f_color;

                        void main() {
                            vec4 baseColor = texture(Texture, v_texcoord);
                            vec2 fragPos = gl_FragCoord.xy;
                            fragPos.y = ScreenResolution.y - fragPos.y;

                            vec3 lightSum = AmbientColor;
                            int count = clamp(NumLights, 0, MAX_LIGHTS);
                            for (int i = 0; i < count; ++i) {
                                vec2 lightPos = Lights[i].xy;
                                float radius = Lights[i].z;
                                float intensity = Lights[i].w;
                                vec3 color = LightColors[i];

                                float dist = distance(fragPos, lightPos);
                                if (dist < radius) {
                                    float attenuation = 1.0 - smoothstep(0.0, radius, dist);
                                    lightSum += color * attenuation * intensity;
                                }
                            }

                            lightSum = clamp(lightSum, 0.0, 1.0);
                            f_color = vec4(baseColor.rgb * lightSum, baseColor.a);
                        }
                    '''
                )
                self.vao = self.ctx.vertex_array(self.prog, [
                    (self.quad_buffer, '2f 2f', 'in_vert', 'in_texcoord')
                ])
                self.tex = self.ctx.texture((SCREEN_WIDTH, SCREEN_HEIGHT), 4)
                self.tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            except Exception as e:
                logger.warning(f"ModernGL indisponivel ({e}). Usando renderizador CPU.")
                self.ctx = None

        pygame.freetype.init()
        # Escala dinamica: base 1100x720, ajusta fontes pela menor dimensao.
        ui_scale = max(0.85, min(1.25, min(SCREEN_WIDTH / 1100.0, SCREEN_HEIGHT / 720.0)))
        self.assets = AssetRegistry(ui_scale=ui_scale)
        self.font_big = self.assets.font("Segoe UI", 42, bold=True)
        self.font_title = self.assets.font("Segoe UI", 26, bold=True)
        self.font = self.assets.font("Segoe UI", 18)
        self.font_small = self.assets.font("Segoe UI", 16)
        self.font_tiny = self.assets.font("Segoe UI", 13)
        self.effect_cache = EffectSurfaceCache()
        self.animation_manager = AnimationManager()
        self.particle_manager = ParticleManager()
        if pygame_gui is not None:
            try:
                self.gui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), self.assets.theme_path)
            except Exception:
                self.gui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
            try:
                self.gui_manager.preload_fonts([
                    {'name': 'noto_sans', 'point_size': 14, 'style': 'bold', 'antialiased': '1'}
                ])
            except Exception:
                pass
        else:
            self.gui_manager = NullGUIManager()
        self.components = UIComponentFactory(self.gui_manager)
        self.init_inventory_gui()
        self.init_shop_menus()
        self.init_encyclopedia_menu()

        self.item_icons = self.assets.load_item_icons(
            ["storm_core", "guardian_plate", "magnet_orb", "chrono_boots", "blade_relay"],
            size=(32, 32),
        )

    def sync_menu_windows(self, state):
        sync_windows_for_state(self, state)

    def draw_gui_layer(self):
        self.gui_manager.update(0.016)
        self.gui_manager.draw_ui(self.screen)

    def get_item_icon(self, key, size=(32, 32)):
        try:
            return self.assets.item_icon(key, size)
        except (FileNotFoundError, pygame.error):
            return self.item_icons.get(key)

    def draw_player_window_accent(self, window, player_index):
        if window is None or player_index is None:
            return
        rect = window.get_abs_rect() if hasattr(window, "get_abs_rect") else getattr(window, "rect", None)
        if rect is None:
            return
        color_key = P2_AIM_COLOR if player_index == 1 else P1_AIM_COLOR
        color = hex_color(color_key)
        pygame.draw.rect(self.screen, color, rect, width=3, border_radius=8)
        pygame.draw.line(self.screen, color, (rect.left + 14, rect.top + 2), (rect.right - 44, rect.top + 2), 3)

    def _scroll_container_to_item(self, scroll_container, item_top, item_height, visible_height, content_height):
        scroll_bar = getattr(scroll_container, "vert_scroll_bar", None)
        if scroll_bar is None:
            return

        max_scroll = max(0, content_height - visible_height)
        if max_scroll <= 0:
            return

        target_scroll = item_top - max(8, (visible_height - item_height) // 2)
        target_scroll = max(0, min(target_scroll, max_scroll))
        scroll_bar.set_scroll_from_start_percentage(target_scroll / max(1, content_height))

    def screen_to_world(self, screen_pos, camera):
        return Vector2(screen_pos[0] + camera.x, screen_pos[1] + camera.y)

    def world_to_screen(self, pos, camera):
        return int(pos.x - camera.x), int(pos.y - camera.y)

    def _rgb(self, color):
        return hex_color(color)[:3]

    def _blend(self, color, target, amount):
        base = self._rgb(color)
        target = self._rgb(target)
        return tuple(int(base[i] + (target[i] - base[i]) * amount) for i in range(3))

    def _draw_soft_circle(self, center, radius, color, alpha=80, rings=3):
        draw_soft_circle(self.screen, center, radius, color, self._rgb, alpha=alpha, rings=rings, cache=self.effect_cache)

    def _get_shadow_offset(self, game, entity_pos, max_offset=12.0):
        if getattr(game, "light_level", 1.0) >= 1.0:
            return Vector2(0, 0)
        emitters = []
        for p in game.players:
            if not getattr(p, "is_down", False):
                emitters.append(p.pos)
        for c in getattr(game, "player_constructs", []):
            if c.kind == "torch":
                emitters.append(c.pos)
        if not emitters:
            return Vector2(0, 0)
        closest_pos = min(emitters, key=lambda p: entity_pos.distance_to(p))
        diff = entity_pos - closest_pos
        dist = diff.length()
        if dist <= 0.01:
            return Vector2(0, 0)
        offset_magnitude = min(max_offset, (180.0 / max(1.0, dist)) * 4.0)
        return diff.normalize() * offset_magnitude

    def _draw_shadow(self, center, radius, alpha=92, y_scale=0.36, offset=None):
        if offset is not None:
            center = (center[0] + offset[0], center[1] + offset[1])
        draw_shadow(self.screen, center, radius, alpha=alpha, y_scale=y_scale, cache=self.effect_cache)

    def _draw_star(self, center, outer, inner, color, points=5, angle_offset=-math.pi / 2):
        draw_star(self.screen, center, outer, inner, color, points=points, angle_offset=angle_offset)

    def _collect_light_sources(self, game, camera):
        lights = []
        
        # 1. Players
        for p in game.players:
            if not getattr(p, "is_down", False):
                px, py = self.world_to_screen(p.pos, camera)
                # Aura Luminosa do Sobrevivente (Fase 2)
                # Outer radius: 180, inner radius: 80.
                lights.append((px, py, 180.0, 1.0, 1.0, 1.0, 0.9))

        # 2. Constructs (turrets, barriers, torches)
        time_val = game.time_alive
        for c in getattr(game, "player_constructs", []):
            cx, cy = self.world_to_screen(c.pos, camera)
            if c.kind == "torch":
                glow_pulse = 1.0 + 0.08 * math.sin(time_val * 15.0 + math.cos(time_val * 6.0))
                lights.append((cx, cy, 160.0 * glow_pulse, 1.0, 0.98, 0.57, 0.23))
            elif c.kind == "turret":
                lights.append((cx, cy, 90.0, 1.0, 0.98, 0.75, 0.14))
            elif c.kind == "barrier":
                lights.append((cx, cy, 70.0, 1.0, 0.22, 0.74, 0.97))
            elif c.kind == "robo_minion":
                lights.append((cx, cy, 78.0, 1.0, 0.98, 0.86, 0.28))

        if getattr(game, "light_level", 1.0) < 0.35:
            for light in getattr(game.world, "iter_visible_static_lights", lambda *args: [])(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
                lx, ly = self.world_to_screen(light.pos, camera)
                if light.kind == "lamp":
                    lights.append((lx, ly, light.radius, 1.0, 0.98, 0.76, 0.25))
                else:
                    lights.append((lx, ly, light.radius, 1.0, 0.34, 0.83, 0.98))

        # 3. Fire Hazards
        focus = camera + Vector2(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5)
        for hazard in getattr(game.world, "nearby_hazards", lambda x, y, r: [])(focus.x, focus.y, 900):
            if hazard.kind == "fire":
                hx, hy = self.world_to_screen(hazard.rect.center, camera)
                glow_pulse = 1.0 + 0.1 * math.sin(time_val * 18.0)
                lights.append((hx, hy, 85.0 * glow_pulse, 1.0, 0.93, 0.26, 0.26))

        # 4. Active Altars
        for altar in getattr(game, "altars", []):
            if getattr(altar, "active", False):
                ax, ay = self.world_to_screen(altar.pos, camera)
                lights.append((ax, ay, 130.0, 1.0, 0.65, 0.54, 0.98))

        # 5. Projectiles
        for proj in getattr(game, "projectiles", []):
            px, py = self.world_to_screen(proj.pos, camera)
            if getattr(proj, "color", ""):
                rgb = hex_color(proj.color)
                color = tuple(channel / 255.0 for channel in rgb)
            else:
                owner = getattr(proj, "owner", 0)
                p_obj = game.get_player(owner)
                if p_obj and getattr(p_obj, "char_class", "") == "cryogenic":
                    color = (0.73, 0.9, 0.99)
                elif p_obj and getattr(p_obj, "char_class", "") == "vanguard":
                    color = (0.98, 0.57, 0.23)
                else:
                    color = (0.99, 0.94, 0.54)
            lights.append((px, py, proj.radius + 10.0, 0.9, *color))

        # 6. Drops
        for drop in getattr(game, "drops", []):
            dx, dy = self.world_to_screen(drop.pos, camera)
            if getattr(drop, "kind", "") == "coin":
                color = (0.99, 0.88, 0.28)
            else:
                color = (0.75, 0.52, 0.99)
            lights.append((dx, dy, 25.0, 1.0, *color))

        return lights

    def _apply_day_night_lighting_cpu(self, game, camera, lights):
        ambient_r, ambient_g, ambient_b = game.light_color
        
        light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        light_mask.fill((ambient_r, ambient_g, ambient_b))

        for x, y, radius, intensity, r, g, b in lights:
            color_rgb = (int(r * 255), int(g * 255), int(b * 255))
            for i in range(12):
                frac = i / 11.0
                ring_r = int(radius * (1.0 - frac))
                if ring_r <= 0:
                    continue
                curr_r = int(ambient_r * (1.0 - frac) + color_rgb[0] * frac)
                curr_g = int(ambient_g * (1.0 - frac) + color_rgb[1] * frac)
                curr_b = int(ambient_b * (1.0 - frac) + color_rgb[2] * frac)
                pygame.draw.circle(light_mask, (curr_r, curr_g, curr_b), (x, y), ring_r)

        self.screen.blit(light_mask, (0, 0), special_flags=pygame.BLEND_MULT)

    def _apply_day_night_lighting(self, game, camera):
        if self.ctx:
            return
        if getattr(game, "light_level", 1.0) >= 1.0:
            return
        lights = self._collect_light_sources(game, camera)
        self._apply_day_night_lighting_cpu(game, camera, lights)

    def _draw_miniboss_arena(self, game, camera):
        center = getattr(game, "miniboss_arena_center", None)
        if center is None:
            return
        scr_pos = self.world_to_screen(center, camera)
        radius = getattr(game, "miniboss_arena_radius", 520.0)
        
        import time
        t = time.time()
        pulse = 0.85 + 0.15 * math.sin(t * 8.0)
        
        glow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (239, 68, 68, int(35 * pulse)), scr_pos, int(radius), 18)
        pygame.draw.circle(glow_surf, (239, 68, 68, int(70 * pulse)), scr_pos, int(radius), 4)
        pygame.draw.circle(glow_surf, (248, 113, 113, int(120 * pulse)), scr_pos, int(radius), 2)
        
        for i in range(12):
            angle = (t * 0.35 + i * (math.tau / 12.0)) % math.tau
            spark_x = scr_pos[0] + math.cos(angle) * radius
            spark_y = scr_pos[1] + math.sin(angle) * radius
            pygame.draw.circle(glow_surf, (254, 240, 138, 180), (int(spark_x), int(spark_y)), 3)
            pygame.draw.circle(glow_surf, (239, 68, 68, 90), (int(spark_x), int(spark_y)), 7)
            
        self.screen.blit(glow_surf, (0, 0))

    def render_game(self, game, mouse_pos, dt=0.016, flip=True, aim_from_joystick=False, p2_aim_pos=None, draw_gui=True):
        self.animation_manager.update(dt)
        self.particle_manager.update(dt)
        self.gui_manager.update(dt)
        for event in game.particle_events:
            self.particle_manager.emit(event["pos"], count=event.get("count", 10), color=event.get("color", "#FFFFFF"), speed=event.get("speed", 50), lifetime=event.get("lifetime", 0.5), size=event.get("size", 4))
        game.particle_events.clear()

        camera = Vector2(game.camera)
        if game.screen_shake > 0:
            shake = math.sin(game.time_alive * 72) * game.screen_shake
            camera.x += shake
            camera.y += math.cos(game.time_alive * 61) * game.screen_shake * 0.6

        # Draw to offscreen surface
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_terrain(game, camera)
        self._draw_hazards(game, camera)
        self._draw_world_objects(game, camera)
        self._draw_altars(game, camera)
        self._draw_drops(game, camera)
        self._draw_projectiles(game, camera)
        self._draw_item_events(game, camera)
        self._draw_constructs(game, camera)
        self._draw_enemies(game, camera)
        self._draw_slashes(game, camera)
        self._draw_escort_event(game, camera)
        self._draw_players(game, camera, mouse_pos, aim_from_joystick, p2_aim_pos)
        self._draw_special_blast(game, camera)
        self.particle_manager.render(self.screen, camera)
        self._apply_day_night_lighting(game, camera)
        self._draw_miniboss_arena(game, camera)

        # Draw Mascot Drones with soft cyan neon glow!
        for drone in getattr(game, "drones", []):
            if "pos" in drone:
                dx, dy = self.world_to_screen(drone["pos"], camera)
                pulse = 0.85 + 0.15 * math.sin(game.time_alive * 8.0 + drone["angle"])
                
                glow_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
                radius = int(12 + pulse * 3)
                pygame.draw.circle(glow_surf, (34, 211, 238, 48), (18, 18), radius)
                pygame.draw.circle(glow_surf, (34, 211, 238, 96), (18, 18), int(radius * 0.6))
                self.screen.blit(glow_surf, (dx - 18, dy - 18))
                
                pygame.draw.circle(self.screen, (34, 211, 238), (dx, dy), 5)
                pygame.draw.circle(self.screen, (255, 255, 255), (dx, dy), 2)

        self._draw_floaters(game, camera)
        self._draw_hud(game)
        self._draw_minimap(game)
        
        # Draw slow-motion Bullet Time vignette
        if game.time_scale < 0.95:
            vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(vignette, (15, 23, 42, 70), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 70)
            pygame.draw.rect(vignette, (139, 92, 246, 30), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 45)
            pygame.draw.rect(vignette, (245, 158, 11, 20), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 25)
            
            pulse_alpha = int(140 + 70 * math.sin(game.time_alive * 6.0))
            font_title = self.font_title
            if font_title:
                txt = "--- TEMPO DESACELERADO ---"
                font_title.render_to(vignette, (SCREEN_WIDTH // 2 - font_title.get_rect(txt, size=18).width // 2, 25), txt, (245, 158, 11, pulse_alpha), size=18)
            self.screen.blit(vignette, (0, 0))
            
        # Draw Pocket Dimension vignette and countdown
        if getattr(game, "current_dimension", "main") == "pocket":
            vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(vignette, (147, 51, 234, 45), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 70)
            pygame.draw.rect(vignette, (168, 85, 247, 30), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 30)
            
            pulse_alpha = int(170 + 60 * math.sin(game.time_alive * 7.0))
            font_title = self.font_title
            if font_title:
                if game.pocket_dimension_timer > 90000.0:
                    txt = "--- DERROTE O ARAUTO SOMBRIO ---"
                else:
                    txt = f"--- DIMENSAO DE BOLSO: {max(0.0, game.pocket_dimension_timer):.1f}s ---"
                font_title.render_to(vignette, (SCREEN_WIDTH // 2 - font_title.get_rect(txt, size=18).width // 2, 25), txt, (192, 132, 252, pulse_alpha), size=18)
            self.screen.blit(vignette, (0, 0))

        # Draw Olympus Dimension vignette and distortion warnings
        if getattr(game, "current_dimension", "main") == "olympus":
            vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            # Golden divine border glow
            pygame.draw.rect(vignette, (218, 165, 32, 50), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 70)
            pygame.draw.rect(vignette, (255, 215, 0, 30), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 35)

            pulse_alpha = int(170 + 60 * math.sin(game.time_alive * 5.0))
            font_title = self.font_title
            if font_title:
                txt = "--- OLIMPO: ENFRENTE O DEUS ---"
                font_title.render_to(vignette, (SCREEN_WIDTH // 2 - font_title.get_rect(txt, size=18).width // 2, 25), txt, (255, 215, 0, pulse_alpha), size=18)

            # Distortion warning text
            distortion = getattr(game, "olympus_distortion_type", "")
            if distortion:
                warn_pulse = int(200 + 55 * math.sin(game.time_alive * 12.0))
                distortion_labels = {
                    "invert_mouse": "⚡ MOUSE INVERTIDO ⚡",
                    "invert_keyboard": "⚡ TECLADO INVERTIDO ⚡",
                    "flip_screen": "⚡ TELA INVERTIDA ⚡",
                }
                warn_txt = distortion_labels.get(distortion, "⚡ DISTORCAO DIVINA ⚡")
                if font_title:
                    w = font_title.get_rect(warn_txt, size=22).width
                    font_title.render_to(vignette, (SCREEN_WIDTH // 2 - w // 2, SCREEN_HEIGHT // 2 - 40), warn_txt, (255, 69, 0, warn_pulse), size=22)
                # Red flash overlay for distortion
                pygame.draw.rect(vignette, (255, 0, 0, 18), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

            self.screen.blit(vignette, (0, 0))

        surf_to_draw = self.game_surface
        if getattr(game, "olympus_distortion_type", "") == "flip_screen":
            surf_to_draw = pygame.transform.flip(surf_to_draw, False, True)
            
        if draw_gui:
            self.gui_manager.draw_ui(surf_to_draw)
        # Present via ModernGL if available, otherwise CPU blit
        if self.ctx:
            try:
                texture_data = pygame.image.tostring(surf_to_draw, 'RGBA', False)
                self.tex.write(texture_data)
                self.ctx.viewport = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
                self.ctx.clear(0.0, 0.0, 0.0)
                self.tex.use(0)
                self.prog['Texture'].value = 0
                
                # Pass lighting uniforms
                if getattr(game, "light_level", 1.0) >= 1.0:
                    self.prog['NumLights'].value = 0
                    self.prog['AmbientColor'].value = (1.0, 1.0, 1.0)
                    self.prog['ScreenResolution'].value = (SCREEN_WIDTH, SCREEN_HEIGHT)
                else:
                    lights = self._collect_light_sources(game, camera)
                    ambient_r, ambient_g, ambient_b = game.light_color
                    
                    lights_data = []
                    colors_data = []
                    for l in lights[:64]:
                        lights_data.extend(l[:4])
                        colors_data.extend(l[4:7])
                    num_lights = len(lights[:64])
                    remaining = 64 - num_lights
                    if remaining > 0:
                        lights_data.extend([0.0] * (remaining * 4))
                        colors_data.extend([0.0] * (remaining * 3))
                    
                    self.prog['NumLights'].value = num_lights
                    self.prog['Lights'].value = lights_data
                    self.prog['LightColors'].value = colors_data
                    self.prog['AmbientColor'].value = (ambient_r / 255.0, ambient_g / 255.0, ambient_b / 255.0)
                    self.prog['ScreenResolution'].value = (SCREEN_WIDTH, SCREEN_HEIGHT)
                
                self.vao.render(moderngl.TRIANGLES)
            except Exception as e:
                logger.error(f"Erro ModernGL: {e}")
                self.screen_original.blit(surf_to_draw, (0, 0))
        else:
            self.screen_original.blit(surf_to_draw, (0, 0))
        if flip:
            pygame.display.flip()

    def render_rng_result(self, game, mouse_pos):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 176))
        self.screen.blit(overlay, (0, 0))

        # Obter dados do RNG
        rng_data = getattr(game, "last_rng_result", {})
        res = rng_data.get("result", "falha")
        msg = rng_data.get("message", "Nenhum resultado registrado.")
        label = rng_data.get("label", "Upgrade")

        # Cores temáticas com base no resultado
        if res == "super":
            border_color = (250, 180, 50)  # Ouro
            title = "SUPER SUCESSO DO ALTAR!"
            title_color = (250, 180, 50)
        elif res == "sucesso":
            border_color = hex_color(COLORS["xp"])  # Verde/Azul
            title = "SUCESSO DO ALTAR"
            title_color = hex_color(COLORS["xp"])
        elif res == "parcial":
            border_color = hex_color(COLORS["upgrade"])  # Laranja
            title = "SUCESSO PARCIAL DO ALTAR"
            title_color = hex_color(COLORS["upgrade"])
        else:
            border_color = hex_color(COLORS["danger"])  # Vermelho
            title = "FALHA DO ALTAR!"
            title_color = hex_color(COLORS["danger"])

        panel_h = 260
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - panel_h // 2, 500, panel_h)
        pygame.draw.rect(self.screen, (9, 15, 26), panel, border_radius=8)
        pygame.draw.rect(self.screen, border_color, panel, width=2, border_radius=8)

        self._center_text(title, self.font_title, panel.y + 24, title_color)

        # Mostrar a mensagem do resultado centralizada com quebra de linha
        y = panel.y + 75
        for line in self._wrap_text(msg, 44)[:4]:
            self._center_text(line, self.font, y, COLORS["text"])
            y += 24

        # Se houver reembolso ou custo, podemos detalhar de forma sutil
        if res == "parcial" and rng_data.get("refund", 0) > 0:
            refund_msg = f"(Reembolsado: {rng_data['refund']} pts)"
            self._center_text(refund_msg, self.font_small, y, COLORS["upgrade"])
            y += 20
        elif res == "super" and rng_data.get("spend", 0) > 0:
            discount_msg = f"(Gasto final: {rng_data['spend']} pts c/ 25% desc)"
            self._center_text(discount_msg, self.font_small, y, (250, 180, 50))
            y += 20

        buttons = []
        btn_y = panel.bottom - 60
        buttons.append(self._button(panel.centerx - 90, btn_y, 180, 40, "Continuar", "rng_result_ok", mouse_pos, COLORS["xp"]))

        return buttons
