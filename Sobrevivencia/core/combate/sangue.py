def is_blood_marked(enemy):
    return getattr(enemy, "blood_mark_timer", 0) > 0 and getattr(enemy, "blood_mark_level", 0) > 0


def apply_blood_mark(enemy, player, bonus_duration=0.0, level_bonus=0):
    base_level = 1 + player.passives.get("blood_mark", 0) // 4 + level_bonus
    base_duration = 2.25 + player.passives.get("blood_mark", 0) * 0.14 + player.passives.get("funeral_volley", 0) * 0.05 + bonus_duration
    enemy.blood_mark_timer = max(getattr(enemy, "blood_mark_timer", 0.0), base_duration)
    enemy.blood_mark_level = max(getattr(enemy, "blood_mark_level", 0), base_level)


def consume_blood_mark(game, enemy, player, special_gain_scale=1.0):
    if not is_blood_marked(enemy):
        return 0
    mark_level = max(1, getattr(enemy, "blood_mark_level", 1))
    harvest_value = max(getattr(enemy, "blood_harvest_value", 0), mark_level)
    enemy.blood_harvest_value = harvest_value
    enemy.blood_mark_timer = 0.0
    enemy.blood_mark_level = 0
    soul_tithe = player.passives.get("soul_tithe", 0)
    if soul_tithe > 0:
        player.add_special((1.15 + soul_tithe * 0.40) * special_gain_scale, "melee")
    return mark_level


def spread_blood_mark(game, center, player, radius, max_targets=2):
    applied = 0
    for enemy in sorted(list(game.enemies), key=lambda e: e.pos.distance_squared_to(center)):
        if applied >= max_targets:
            break
        if enemy.pos.distance_squared_to(center) <= radius ** 2:
            apply_blood_mark(enemy, player, bonus_duration=0.4)
            applied += 1
