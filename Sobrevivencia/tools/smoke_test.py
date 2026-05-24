import os
import sys
import threading
import time
import traceback
from pathlib import Path


def _prepare_import_path():
    project_dir = Path(__file__).resolve().parents[1]
    package_parent = project_dir.parent
    sys.path.insert(0, str(package_parent))


def _post_quit_after(seconds):
    import pygame

    time.sleep(seconds)
    pygame.event.post(pygame.event.Event(pygame.QUIT))


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    _prepare_import_path()

    from Sobrevivencia.main import main as game_main

    threading.Thread(target=_post_quit_after, args=(3.0,), daemon=True).start()
    try:
        game_main()
    except Exception:
        traceback.print_exc()
        return 1

    print("OK: jogo inicializou, processou alguns frames e fechou sem erro critico.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
