import importlib
import logging


def optional_import(module_name):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def optional_from(module_name, attr_name):
    module = optional_import(module_name)
    if module is None:
        return None
    return getattr(module, attr_name, None)


def _create_std_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("Sobrevivencia")


logger = optional_from("loguru", "logger") or _create_std_logger()


def configure_file_logging(path="game.log", level="INFO"):
    if hasattr(logger, "add"):
        try:
            logger.add(path, rotation="5 MB", level=level)
        except OSError:
            logger.warning("Nao foi possivel abrir o arquivo de log: {}", path)
        return

    try:
        file_handler = logging.FileHandler(path, encoding="utf-8")
    except OSError:
        logger.warning("Nao foi possivel abrir o arquivo de log: %s", path)
        return
    file_handler.setLevel(getattr(logging, level, logging.INFO))
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(file_handler)


def njit_or_python(func=None, **_kwargs):
    numba = optional_import("numba")
    if numba is not None:
        return numba.njit(func, **_kwargs) if func is not None else numba.njit(**_kwargs)

    def decorator(inner):
        return inner

    return decorator(func) if func is not None else decorator


def ease_out_quad(progress):
    progress = max(0.0, min(1.0, progress))
    return 1.0 - (1.0 - progress) * (1.0 - progress)


def ease_in_quad(progress):
    progress = max(0.0, min(1.0, progress))
    return progress * progress


def ease_out_cubic(progress):
    progress = max(0.0, min(1.0, progress))
    return 1.0 - (1.0 - progress) ** 3


class TweeningFallback:
    easeOutQuad = staticmethod(ease_out_quad)
    easeInQuad = staticmethod(ease_in_quad)
    easeOutCubic = staticmethod(ease_out_cubic)


class NullGUIManager:
    def process_events(self, _event):
        return False

    def update(self, _dt):
        return None

    def draw_ui(self, _surface):
        return None
