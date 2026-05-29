import argparse
import os
import sys
from pathlib import Path


def _prepare_import_path():
    project_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_dir.parent))


def _save(surface, output_dir, name):
    import pygame

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.png"
    pygame.image.save(surface, str(path))
    print(f"OK snapshot: {path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gera screenshots headless das principais telas.")
    parser.add_argument("--output", default="scratch/snapshots")
    args = parser.parse_args(argv)

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    _prepare_import_path()

    import pygame
    from pygame.math import Vector2

    from Sobrevivencia.core.entities import Altar
    from Sobrevivencia.core.game_logic import GameLogic
    from Sobrevivencia.data.constants import PAUSE_OPTIONS, SCREEN_HEIGHT, SCREEN_WIDTH
    from Sobrevivencia.presentation.ui import UI

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = Path(__file__).resolve().parents[1] / output_dir

    ui = UI(screen)
    game = GameLogic()
    mouse_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    game.update(1 / 60, Vector2(0, 0), game.player.pos + Vector2(120, 0))

    ui.sync_menu_windows("start")
    ui.render_start(mouse_pos, 0)
    _save(ui.screen, output_dir, "start")

    ui.sync_menu_windows("playing")
    ui.render_game(game, mouse_pos, dt=1 / 60, flip=False)
    _save(ui.screen, output_dir, "gameplay")

    night_game = GameLogic()
    night_game.day_night_timer = 82.0
    night_game.light_level = 0.0
    night_game.altars = [
        Altar(pos=night_game.player.pos + Vector2(160, -80), kind="weapon_altar"),
        Altar(pos=night_game.player.pos + Vector2(260, 90), kind="skill_altar"),
        Altar(pos=night_game.player.pos + Vector2(-220, 80), kind="stamps_altar"),
    ]
    night_game.update(1 / 60, Vector2(0, 0), night_game.player.pos + Vector2(120, 0))
    ui.sync_menu_windows("playing")
    ui.render_game(night_game, mouse_pos, dt=1 / 60, flip=False)
    _save(ui.screen, output_dir, "gameplay_night_altars")

    ui.sync_menu_windows("paused")
    ui.render_pause(game, PAUSE_OPTIONS, 0, mouse_pos)
    _save(ui.screen, output_dir, "pause")

    game.level_up_pending = True
    game.level_up_player_index = 0
    game.upgrade_is_major = False
    game.upgrade_choices = game.generate_upgrade_choices(False, 0)
    ui.sync_menu_windows("upgrade")
    ui.render_upgrade(game, 0, mouse_pos)
    _save(ui.screen, output_dir, "upgrade")

    ui.sync_menu_windows("inventory")
    game.menu_player_index = 0
    ui.render_inventory_gui(game, 0, mouse_pos, "items")
    _save(ui.screen, output_dir, "inventory")

    ui.sync_menu_windows("skills")
    game.active_altar = Altar(pos=game.player.pos, kind="skill_altar")
    ui.render_skills(game, 0, mouse_pos)
    _save(ui.screen, output_dir, "skills")
    game.active_altar = None

    ui.sync_menu_windows("stat_shop")
    game.stat_shop_offers = [game._generate_stat_offer() for _ in range(3)]
    ui.render_stat_shop(game, 0, mouse_pos)
    _save(ui.screen, output_dir, "stat_shop")

    ui.sync_menu_windows("mode_select")
    ui.render_mode_select(mouse_pos, selected=0, joystick_count=1)
    _save(ui.screen, output_dir, "mode_select")

    ui.sync_menu_windows("character_select")
    ui.render_character_select("vanguard", mouse_pos)
    _save(ui.screen, output_dir, "character_select")

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
