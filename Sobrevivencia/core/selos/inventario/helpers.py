if __package__:
    from ....data.stamps import STAMP_DEFINITIONS
else:
    from Sobrevivencia.data.stamps import STAMP_DEFINITIONS


def stamp_entries(player):
    entries = []
    for weapon_key in ("weapon_1", "weapon_2"):
        for index, stamp in enumerate(player.weapon_stamps.get(weapon_key, [])):
            entries.append((weapon_key, index, stamp))
    for index, stamp in enumerate(player.stamp_reserve):
        entries.append(("reserve", index, stamp))
    return entries


def auto_equip_passive_stamp(player, stamp):
    definition = STAMP_DEFINITIONS.get(stamp.key, {})
    if stamp.is_junk or not definition.get("on_equip", False):
        return None
    for weapon_key in ("weapon_1", "weapon_2"):
        equipped = player.weapon_stamps.setdefault(weapon_key, [])
        if len(equipped) < 3:
            equipped.append(stamp)
            return weapon_key
    return None

