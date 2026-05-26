import pygame

if __package__:
    from ..config.runtime import configure_file_logging, logger
    from ..data.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
    from .menu_manager import MenuManager
    from .ui import UI
else:
    from Sobrevivencia.config.runtime import configure_file_logging, logger
    from Sobrevivencia.data.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
    from Sobrevivencia.presentation.menu_manager import MenuManager
    from Sobrevivencia.presentation.ui import UI


def init_pygame_runtime(settings, set_display_mode):
    pygame.init()
    pygame.font.init()
    pygame.freetype.init()
    pygame.joystick.init()

    configure_file_logging("game.log", level="INFO")
    logger.info("Sistema inicializado. Iniciando SobrevivenciaGame...")
    pygame.display.set_caption("Sobrevivencia - Top Down Survival")

    fullscreen = bool(settings.get("fullscreen", False))
    screen, fullscreen = set_display_mode(fullscreen, None)
    clock = pygame.time.Clock()
    ui = UI(screen)
    menu_manager = MenuManager(screen)
    return screen, fullscreen, clock, ui, menu_manager


def attach_virtual_screen(app, ui, menu_manager):
    app.virtual_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    ui.screen = app.virtual_screen
    menu_manager.screen = app.virtual_screen
    return app.virtual_screen

