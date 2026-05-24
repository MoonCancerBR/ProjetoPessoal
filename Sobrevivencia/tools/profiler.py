import argparse
import cProfile
import io
import os
import pstats
import sys
import time
from pathlib import Path


def _prepare_import_path():
    project_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_dir.parent))


def _profile_core(seconds, fixed_dt):
    from pygame.math import Vector2

    from Sobrevivencia.core.game_logic import GameLogic

    game = GameLogic()
    aim = game.player.pos + Vector2(120, 0)
    move = Vector2(0, 0)
    frames = max(1, int(seconds / fixed_dt))

    start = time.perf_counter()
    for _ in range(frames):
        game.update(fixed_dt, move, aim)
    elapsed = time.perf_counter() - start

    print(f"Core frames: {frames}")
    print(f"Core elapsed: {elapsed:.3f}s")
    print(f"Core simulated: {frames * fixed_dt:.3f}s")
    print(f"Core update FPS: {frames / elapsed:.1f}")


def _profile_ui(seconds, fixed_dt):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    import pygame
    from pygame.math import Vector2

    from Sobrevivencia.core.game_logic import GameLogic
    from Sobrevivencia.presentation.ui import UI

    pygame.init()
    screen = pygame.display.set_mode((1100, 720))
    game = GameLogic()
    ui = UI(screen)
    aim = (550, 360)
    move = Vector2(0, 0)
    aim_world = game.player.pos + Vector2(120, 0)
    frames = max(1, int(seconds / fixed_dt))

    start = time.perf_counter()
    for _ in range(frames):
        game.update(fixed_dt, move, aim_world)
        ui.render_game(game, aim, dt=fixed_dt, flip=False)
    elapsed = time.perf_counter() - start
    pygame.quit()

    print(f"UI frames: {frames}")
    print(f"UI elapsed: {elapsed:.3f}s")
    print(f"UI simulated: {frames * fixed_dt:.3f}s")
    print(f"UI render/update FPS: {frames / elapsed:.1f}")


def run_profile(mode, seconds, fixed_dt, output_path, sort_key, limit):
    _prepare_import_path()

    profiler = cProfile.Profile()
    profiler.enable()
    if mode == "core":
        _profile_core(seconds, fixed_dt)
    else:
        _profile_ui(seconds, fixed_dt)
    profiler.disable()

    stats_stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stats_stream).strip_dirs().sort_stats(sort_key)
    stats.print_stats(limit)

    report = stats_stream.getvalue()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Relatorio salvo em: {output_path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Profile headless do Sobrevivencia.")
    parser.add_argument("--mode", choices=("core", "ui"), default="core")
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument("--dt", type=float, default=1 / 60)
    parser.add_argument("--output", default="tools/profiler_report.txt")
    parser.add_argument("--sort", default="cumtime")
    parser.add_argument("--limit", type=int, default=40)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(__file__).resolve().parents[1] / output_path
    run_profile(args.mode, args.seconds, args.dt, output_path, args.sort, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
