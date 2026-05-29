import json
from pathlib import Path


META_PATH = Path(__file__).resolve().parents[1] / "data" / "meta_progress.json"
DEFAULT_UNLOCKED_CHARACTERS = ("vanguard",)
CHARACTER_PRICES = {
    "vanguard": 0,
    "huntress": 250,
    "engineer": 400,
    "reaper": 650,
}
UPGRADE_LEVEL_MIN = 0
UPGRADE_LEVEL_BASE = 1
UPGRADE_LEVEL_MAX = 10
CHARACTER_UPGRADES = {
    "max_health": {"label": "Vida maxima", "unit": "%", "base_cost": 80, "cost_growth": 42, "step": 0.030, "kind": "percent"},
    "defense": {"label": "Defesa", "unit": "%", "base_cost": 95, "cost_growth": 48, "step": 0.018, "kind": "percent"},
    "speed": {"label": "Velocidade maxima", "unit": "%", "base_cost": 90, "cost_growth": 46, "step": 0.014, "kind": "percent"},
    "attack_rate": {"label": "Cadencia de tiros", "unit": "%", "base_cost": 100, "cost_growth": 52, "step": 0.014, "kind": "percent"},
    "damage": {"label": "Dano maximo", "unit": "%", "base_cost": 110, "cost_growth": 58, "step": 0.017, "kind": "percent"},
    "vampirism": {"label": "Vampirismo", "unit": " cura", "base_cost": 125, "cost_growth": 62, "step": 0.22, "kind": "flat"},
    "magazine": {"label": "Cartucho inicial", "unit": " mun", "base_cost": 85, "cost_growth": 44, "step": 1.0, "kind": "integer"},
    "ammo_reserve": {"label": "Reserva inicial", "unit": " mun", "base_cost": 75, "cost_growth": 38, "step": 6.0, "kind": "integer"},
}


def load_meta_progress():
    try:
        data = json.loads(META_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    unlocked = data.get("unlocked_characters", DEFAULT_UNLOCKED_CHARACTERS)
    if not isinstance(unlocked, list):
        unlocked = list(DEFAULT_UNLOCKED_CHARACTERS)
    clean_unlocked = []
    for key in [*DEFAULT_UNLOCKED_CHARACTERS, *unlocked]:
        if isinstance(key, str) and key not in clean_unlocked:
            clean_unlocked.append(key)
    upgrades = _normalize_character_upgrades(data.get("character_upgrades", {}))
    return {
        "coins": int(data.get("coins", 0)),
        "unlocked_characters": clean_unlocked,
        "character_upgrades": upgrades,
    }


def save_meta_progress(data):
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    unlocked = data.get("unlocked_characters", DEFAULT_UNLOCKED_CHARACTERS)
    if not isinstance(unlocked, list):
        unlocked = list(DEFAULT_UNLOCKED_CHARACTERS)
    clean_unlocked = []
    for key in [*DEFAULT_UNLOCKED_CHARACTERS, *unlocked]:
        if isinstance(key, str) and key not in clean_unlocked:
            clean_unlocked.append(key)
    clean = {
        "coins": max(0, int(data.get("coins", 0))),
        "unlocked_characters": clean_unlocked,
        "character_upgrades": _normalize_character_upgrades(data.get("character_upgrades", {})),
    }
    META_PATH.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return clean


def coin_balance():
    return load_meta_progress()["coins"]


def add_coins(amount):
    data = load_meta_progress()
    data["coins"] = max(0, int(data.get("coins", 0)) + int(amount))
    return save_meta_progress(data)["coins"]


def unlocked_characters():
    return tuple(load_meta_progress()["unlocked_characters"])


def is_character_unlocked(character_key):
    return character_key in load_meta_progress()["unlocked_characters"]


def character_price(character_key):
    return int(CHARACTER_PRICES.get(character_key, 500))


def unlock_character(character_key):
    data = load_meta_progress()
    unlocked = data["unlocked_characters"]
    if character_key in unlocked:
        return True, "Personagem ja desbloqueado.", data["coins"]
    price = character_price(character_key)
    if data["coins"] < price:
        return False, "Moedas insuficientes.", data["coins"]
    data["coins"] -= price
    unlocked.append(character_key)
    saved = save_meta_progress(data)
    return True, "Personagem desbloqueado.", saved["coins"]


def _normalize_character_upgrades(raw):
    raw = raw if isinstance(raw, dict) else {}
    clean = {}
    for key in CHARACTER_UPGRADES:
        current = raw.get(key, {}) if isinstance(raw.get(key, {}), dict) else {}
        purchased = int(current.get("purchased_level", UPGRADE_LEVEL_BASE))
        active = int(current.get("active_level", purchased))
        purchased = max(UPGRADE_LEVEL_BASE, min(UPGRADE_LEVEL_MAX, purchased))
        active = max(UPGRADE_LEVEL_MIN, min(purchased, active))
        clean[key] = {"purchased_level": purchased, "active_level": active}
    return clean


def character_upgrades():
    return load_meta_progress()["character_upgrades"]


def upgrade_cost(key, next_level):
    if key not in CHARACTER_UPGRADES or next_level <= UPGRADE_LEVEL_BASE:
        return 0
    next_level = min(UPGRADE_LEVEL_MAX, int(next_level))
    data = CHARACTER_UPGRADES[key]
    return int(data["base_cost"] + (next_level - 2) * data["cost_growth"] + (next_level - 2) ** 2 * 12)


def upgrade_effect_value(key, active_level):
    if key not in CHARACTER_UPGRADES:
        return 0.0
    active_level = max(UPGRADE_LEVEL_MIN, min(UPGRADE_LEVEL_MAX, int(active_level)))
    data = CHARACTER_UPGRADES[key]
    if active_level == UPGRADE_LEVEL_BASE:
        return 0.0
    sign = 1.0 if active_level > UPGRADE_LEVEL_BASE else -1.0
    steps = active_level - UPGRADE_LEVEL_BASE if active_level > UPGRADE_LEVEL_BASE else 1
    value = sum(data["step"] * (1.0 + index * 0.18) for index in range(steps))
    return sign * value


def set_active_upgrade_level(key, level):
    data = load_meta_progress()
    upgrades = data["character_upgrades"]
    if key not in upgrades:
        return False
    purchased = upgrades[key]["purchased_level"]
    upgrades[key]["active_level"] = max(UPGRADE_LEVEL_MIN, min(purchased, int(level)))
    save_meta_progress(data)
    return True


def save_active_upgrade_levels(levels):
    data = load_meta_progress()
    upgrades = data["character_upgrades"]
    for key, level in levels.items():
        if key not in upgrades:
            continue
        purchased = upgrades[key]["purchased_level"]
        upgrades[key]["active_level"] = max(UPGRADE_LEVEL_MIN, min(purchased, int(level)))
    return save_meta_progress(data)["character_upgrades"]


def purchase_upgrade_level(key):
    data = load_meta_progress()
    upgrades = data["character_upgrades"]
    if key not in upgrades:
        return False, "Melhoria invalida.", data["coins"]
    current = upgrades[key]["purchased_level"]
    if current >= UPGRADE_LEVEL_MAX:
        return False, "Melhoria ja esta no maximo.", data["coins"]
    next_level = current + 1
    cost = upgrade_cost(key, next_level)
    if data["coins"] < cost:
        return False, "Moedas insuficientes.", data["coins"]
    data["coins"] -= cost
    upgrades[key]["purchased_level"] = next_level
    upgrades[key]["active_level"] = next_level
    saved = save_meta_progress(data)
    return True, "Melhoria comprada.", saved["coins"]
