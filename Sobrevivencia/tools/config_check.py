import importlib.util
import json
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PACKAGE_PARENT = PROJECT_DIR.parent

REQUIRED_CONFIGS = ("settings.json", "balance.json", "keybinds.json")
RECOMMENDED_MODULES = (
    "pygame",
    "pygame_gui",
    "pygame_menu",
    "pytweening",
    "loguru",
)
OPTIONAL_MODULES = (
    "numpy",
    "pymunk",
    "pytmx",
    "numba",
    "moderngl",
)


def _prepare_import_path():
    sys.path.insert(0, str(PACKAGE_PARENT))


def _check_json(filename):
    path = PROJECT_DIR / "config" / filename
    if not path.exists():
        return False, f"faltando: {path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"JSON invalido em {path}: {exc}"
    if not isinstance(data, dict):
        return False, f"{path} precisa conter um objeto JSON"
    return True, f"OK {filename}"


def _check_modules(module_names):
    return {name: importlib.util.find_spec(name) is not None for name in module_names}


def main():
    _prepare_import_path()
    failures = []

    print("Configs:")
    for filename in REQUIRED_CONFIGS:
        ok, message = _check_json(filename)
        print(f"  {message}")
        if not ok:
            failures.append(message)

    print("Keybinds:")
    try:
        from Sobrevivencia.input.input_manager import InputManager

        bindings = InputManager()._default_bindings()
        print(f"  OK {len(bindings)} acoes carregadas")
    except Exception as exc:
        message = f"falha ao carregar keybinds: {exc}"
        print(f"  {message}")
        failures.append(message)

    print("Modulos recomendados:")
    recommended = _check_modules(RECOMMENDED_MODULES)
    for name, available in recommended.items():
        print(f"  {name}: {'OK' if available else 'ausente'}")

    print("Modulos opcionais:")
    optional = _check_modules(OPTIONAL_MODULES)
    for name, available in optional.items():
        print(f"  {name}: {'OK' if available else 'ausente'}")

    if failures:
        print("Config check falhou.")
        return 1

    print("OK: configuracao carregavel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
