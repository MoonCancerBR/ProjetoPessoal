import pygame
from ..data.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS

try:
    import pygame_menu
except ImportError:
    pygame_menu = None

def hex_to_rgb(hex_str):
    if isinstance(hex_str, tuple): return hex_str
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

class MenuManager:
    """
    Manager for pygame-menu integration.
    Provides professional menus for start, settings, and pause screens.
    """
    def __init__(self, screen):
        self.screen = screen
        self.theme = self._create_theme()
        self.menus = {}
        self.active_menu = None

    def _create_theme(self):
        if pygame_menu is None:
            return None
        theme = pygame_menu.Theme()
        theme.title_font_size = 48
        theme.title_font_color = hex_to_rgb(COLORS["upgrade"])
        theme.title_background_color = hex_to_rgb(COLORS["panel"])
        theme.background_color = (*hex_to_rgb(COLORS["bg"]), 210) 
        theme.widget_font_size = 32
        theme.widget_font_color = hex_to_rgb(COLORS["text"])
        theme.widget_alignment = pygame_menu.locals.ALIGN_CENTER
        theme.widget_selection_effect = pygame_menu.widgets.RightArrowSelection(
            arrow_size=(20, 30)
        )
        theme.widget_margin = (0, 15)
        return theme

    def create_start_menu(self, on_start, on_commands, on_settings, on_quit, on_encyclopedia=None):
        if pygame_menu is None:
            menu = {
                "title": "SOBREVIVENCIA",
                "subtitle": "Top-down Survival Evolved",
                "selected": 0,
                "buttons": [
                    ("INICIAR JOGO", on_start),
                    ("ENCICLOPEDIA", on_encyclopedia or on_commands),
                    ("COMANDOS", on_commands),
                    ("CONFIGURACOES", on_settings),
                    ("SAIR", on_quit),
                ],
                "rects": [],
            }
            self.menus['start'] = menu
            return menu

        menu = pygame_menu.Menu(
            'SOBREVIVENCIA', SCREEN_WIDTH, SCREEN_HEIGHT,
            theme=self.theme
        )
        menu.add.label('Top-down Survival Evolved', font_size=20, font_color=hex_to_rgb(COLORS["muted"]))
        menu.add.vertical_margin(40)
        menu.add.button('INICIAR JOGO', on_start, background_color=hex_to_rgb(COLORS["xp"]), font_color=(10, 20, 30))
        menu.add.button('ENCICLOPEDIA', on_encyclopedia or on_commands)
        menu.add.button('COMANDOS', on_commands)
        menu.add.button('CONFIGURACOES', on_settings)
        menu.add.button('SAIR', on_quit, font_color=hex_to_rgb(COLORS["danger"]))
        self.menus['start'] = menu
        return menu

    def create_pause_menu(self, on_resume, on_inventory, on_skills, on_settings, on_quit, on_encyclopedia=None):
        if pygame_menu is None:
            menu = {
                "title": "PAUSADO",
                "subtitle": "",
                "selected": 0,
                "buttons": [
                    ("CONTINUAR", on_resume),
                    ("INVENTARIO", on_inventory),
                    ("SKILLS", on_skills),
                    ("ENCICLOPEDIA", on_encyclopedia or on_resume),
                    ("CONFIGURACOES", on_settings),
                    ("SAIR PARA MENU", on_quit),
                ],
                "rects": [],
            }
            self.menus['pause'] = menu
            return menu

        menu = pygame_menu.Menu(
            'PAUSADO', SCREEN_WIDTH, SCREEN_HEIGHT,
            theme=self.theme
        )
        menu.add.button('CONTINUAR', on_resume, background_color=hex_to_rgb(COLORS["xp"]), font_color=(10, 20, 30))
        menu.add.button('INVENTARIO', on_inventory)
        menu.add.button('SKILLS', on_skills)
        if on_encyclopedia:
            menu.add.button('ENCICLOPEDIA', on_encyclopedia)
        menu.add.button('CONFIGURACOES', on_settings)
        menu.add.button('SAIR PARA MENU', on_quit, font_color=hex_to_rgb(COLORS["danger"]))
        self.menus['pause'] = menu
        return menu

    def set_active(self, menu_key):
        new_menu = self.menus.get(menu_key)
        if pygame_menu is None:
            self.active_menu = new_menu
            return
        if new_menu and self.active_menu != new_menu:
            self.active_menu = new_menu
            self.active_menu.enable()
        elif not new_menu:
            self.active_menu = None

    def update(self, events):
        if pygame_menu is None:
            if not self.active_menu:
                return
            buttons = self.active_menu["buttons"]
            if not buttons:
                return
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.active_menu["selected"] = (self.active_menu["selected"] - 1) % len(buttons)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.active_menu["selected"] = (self.active_menu["selected"] + 1) % len(buttons)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        buttons[self.active_menu["selected"]][1]()
                elif event.type == pygame.MOUSEMOTION:
                    for index, rect in enumerate(self.active_menu["rects"]):
                        if rect.collidepoint(event.pos):
                            self.active_menu["selected"] = index
                            break
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for index, rect in enumerate(self.active_menu["rects"]):
                        if rect.collidepoint(event.pos):
                            self.active_menu["selected"] = index
                            buttons[index][1]()
                            break
            return

        if self.active_menu and self.active_menu.is_enabled():
            self.active_menu.update(events)

    def draw(self):
        if pygame_menu is None:
            if not self.active_menu:
                return
            title_font = pygame.font.SysFont("Consolas", 48, bold=True)
            subtitle_font = pygame.font.SysFont("Consolas", 20)
            button_font = pygame.font.SysFont("Consolas", 30, bold=True)
            title = title_font.render(self.active_menu["title"], True, hex_to_rgb(COLORS["upgrade"]))
            self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 140)))
            if self.active_menu["subtitle"]:
                subtitle = subtitle_font.render(self.active_menu["subtitle"], True, hex_to_rgb(COLORS["muted"]))
                self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 190)))

            self.active_menu["rects"] = []
            start_y = 260
            for index, (label, _callback) in enumerate(self.active_menu["buttons"]):
                rect = pygame.Rect(0, 0, 360, 52)
                rect.center = (SCREEN_WIDTH // 2, start_y + index * 66)
                selected = index == self.active_menu["selected"]
                bg = hex_to_rgb(COLORS["xp"] if selected else COLORS["panel"])
                fg = (10, 20, 30) if selected else hex_to_rgb(COLORS["text"])
                pygame.draw.rect(self.screen, bg, rect, border_radius=8)
                pygame.draw.rect(self.screen, hex_to_rgb(COLORS["muted_2"]), rect, 2, border_radius=8)
                text = button_font.render(label, True, fg)
                self.screen.blit(text, text.get_rect(center=rect.center))
                self.active_menu["rects"].append(rect)
            return

        if self.active_menu and self.active_menu.is_enabled():
            self.active_menu.draw(self.screen)
