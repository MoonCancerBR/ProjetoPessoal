import json
from pathlib import Path

if __package__:
    from ..data.constants import CHARACTERS
    from ..data.items import get_item_tags, item_display_name
    from ..data.stamps import stamp_display_name
else:
    from Sobrevivencia.data.constants import CHARACTERS
    from Sobrevivencia.data.items import get_item_tags, item_display_name
    from Sobrevivencia.data.stamps import stamp_display_name


RECORD_LIMIT = 10
RECORDS_PATH = Path(__file__).resolve().parents[1] / "data" / "records.json"


def load_records():
    try:
        data = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    records = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        records.append({
            "name": str(entry.get("name", "???"))[:16],
            "score": int(entry.get("score", 0)),
            "time": float(entry.get("time", 0.0)),
            "build": str(entry.get("build", ""))[:180],
            "details": entry.get("details", {}),
        })
    return sorted(records, key=lambda item: item["score"], reverse=True)[:RECORD_LIMIT]


def save_records(records):
    RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(records, key=lambda item: item["score"], reverse=True)[:RECORD_LIMIT]
    RECORDS_PATH.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_record(index):
    records = load_records()
    if 0 <= index < len(records):
        records.pop(index)
        save_records(records)
        return True
    return False


def qualifies(score, records=None):
    records = load_records() if records is None else records
    return score > 0 and (len(records) < RECORD_LIMIT or score > records[-1]["score"])


def add_record(name, game):
    records = load_records()
    entry = build_record(name, game)
    records.append(entry)
    save_records(records)
    return entry


def build_record(name, game):
    return {
        "name": sanitize_name(name),
        "score": total_score(game),
        "time": float(getattr(game, "time_alive", 0.0)),
        "build": build_summary(game),
        "details": build_details(game),
    }


def sanitize_name(name):
    cleaned = "".join(ch for ch in str(name).strip() if ch.isalnum() or ch in " _-")
    return (cleaned or "JOGADOR")[:16]


def total_score(game):
    return int(sum(getattr(player, "score", 0) for player in getattr(game, "players", [])))


def build_summary(game):
    parts = []
    for player in getattr(game, "players", []):
        inv = game.get_inventory(player.player_index)
        char_name = CHARACTERS.get(player.char_class, {}).get("name", player.char_class)
        active_items = [item for item in inv.item_list() if inv.is_active(item.slot_key)]
        item_text = ", ".join(f"{item.key} Nv{item.level}" for item in active_items[:5]) or "sem itens"
        passives = [(key, level) for key, level in getattr(player, "passives", {}).items() if level > 0]
        passive_text = ", ".join(f"{key} {level}" for key, level in sorted(passives, key=lambda pair: pair[1], reverse=True)[:4]) or "sem passivas"
        stamps = []
        for weapon_key in ("weapon_1", "weapon_2"):
            stamps.extend(getattr(player, "weapon_stamps", {}).get(weapon_key, []))
        stamp_text = ", ".join(f"{stamp.key} Nv{stamp.level}" for stamp in stamps[:6]) or "sem selos"
        parts.append(f"J{player.player_index + 1} {char_name}: {item_text}; {passive_text}; {stamp_text}")
    return " | ".join(parts)


def build_details(game):
    players = []
    for player in getattr(game, "players", []):
        inv = game.get_inventory(player.player_index)
        char_data = CHARACTERS.get(player.char_class, {})
        active_items = [item for item in inv.item_list() if inv.is_active(item.slot_key)]
        items = [
            {
                "key": item.key,
                "name": item_display_name(item),
                "level": int(item.level),
                "rank": int(item.rank),
                "tags": get_item_tags(item),
                "sources": list(getattr(item, "hybrid_sources", ())),
            }
            for item in active_items
        ]
        stamps = {}
        for weapon_key in ("weapon_1", "weapon_2"):
            stamps[weapon_key] = [
                {"key": stamp.key, "name": stamp_display_name(stamp), "level": int(stamp.level)}
                for stamp in getattr(player, "weapon_stamps", {}).get(weapon_key, [])
            ]
        passives = [
            {"key": key, "title": _passive_title(player.char_class, key), "level": int(level)}
            for key, level in getattr(player, "passives", {}).items()
            if level > 0
        ]
        players.append({
            "player": int(player.player_index + 1),
            "class": player.char_class,
            "class_name": char_data.get("name", player.char_class),
            "level": int(getattr(player, "level", 1)),
            "kills": int(getattr(player, "kills", 0)),
            "score": int(getattr(player, "score", 0)),
            "items": items,
            "stamps": stamps,
            "passives": passives,
            "synergies": list(inv.get_active_synergies()),
            "stats": _player_stats(game, player, inv),
        })
    return {
        "players": players,
        "time": float(getattr(game, "time_alive", 0.0)),
        "kills": int(sum(getattr(player, "kills", 0) for player in getattr(game, "players", []))),
        "kill_counts": dict(getattr(game, "kill_counts", {})),
        "omni": {
            "fragments": dict(getattr(game, "chalice_fragments", {})),
            "escorts": int(getattr(game, "completed_escorts", 0)),
            "quests": int(getattr(game, "completed_quick_quests", 0)),
            "miniboss_kills": int(getattr(game, "miniboss_kills", 0)),
            "active": bool(getattr(game, "omni_kernel_active", False)),
        },
        "score": total_score(game),
        "dimension": getattr(game, "current_dimension", "main"),
    }


def _passive_title(char_class, key):
    return CHARACTERS.get(char_class, {}).get("passives", {}).get(key, {}).get("title", key)


def _player_stats(game, player, inv):
    speed = player.base_speed * game.effective_speed_multiplier_for(player)
    attack_rate = game.effective_attack_rate_multiplier_for(player, inv)
    projectile_damage = game.projectile_damage_for(player, inv)
    sword_damage = game.sword_damage_for(player, inv)
    defense = getattr(player, "item_guardian_reduction", 0.0)
    return {
        "max_health": round(float(getattr(player, "max_health", 0.0)), 1),
        "speed": round(float(speed), 1),
        "attack_rate": round(float(attack_rate), 2),
        "projectile_damage": round(float(projectile_damage), 1),
        "sword_damage": round(float(sword_damage), 1),
        "defense": round(float(defense * 100.0), 1),
        "vampirism": round(float(getattr(player, "vampirism", 0.0)), 1),
        "magazine": int(getattr(player, "ammo_magazine", 0) + getattr(player, "magazine_bonus", 0)),
    }
