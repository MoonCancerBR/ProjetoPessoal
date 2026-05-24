import json
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parent


def load_json_config(filename, default=None):
    path = CONFIG_DIR / filename
    if not path.exists():
        return {} if default is None else dict(default)
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {} if default is None else dict(default)
    return data if isinstance(data, dict) else ({} if default is None else dict(default))


def load_settings():
    return load_json_config("settings.json")


def load_keybinds():
    return load_json_config("keybinds.json")


def load_balance():
    return load_json_config("balance.json")


def apply_overrides(target_globals, overrides, allowed_keys=None):
    if not isinstance(overrides, dict):
        return []

    allowed = set(allowed_keys) if allowed_keys is not None else None
    changed = []
    for key, value in overrides.items():
        if allowed is not None and key not in allowed:
            continue
        if key not in target_globals:
            continue
        current = target_globals[key]
        if not isinstance(value, type(current)):
            if isinstance(current, float) and isinstance(value, (int, float)):
                value = float(value)
            elif isinstance(current, int) and isinstance(value, int):
                pass
            else:
                continue
        target_globals[key] = value
        changed.append(key)
    return changed
