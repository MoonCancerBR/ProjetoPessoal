if __package__:
    from ...data.constants import PROJECTILE_DAMAGE, SWORD_DAMAGE
else:
    from Sobrevivencia.data.constants import PROJECTILE_DAMAGE, SWORD_DAMAGE


ELITE_KINDS = {"miniboss", "harbinger", "reaper", "god"}
HEAVY_KINDS = {"brute", "bulwark", "golem", "necromancer", "chromatic"}


def enemy_difficulty_rating(game):
    time_factor = max(0.0, game.time_alive) / 92.0
    level_factor = max(0, highest_player_level(game) - 1) * 0.12
    power_factor = max(0.0, player_power_rating(game) - 1.0) * 0.72
    return 1.0 + time_factor + level_factor + power_factor


def highest_player_level(game):
    return max((getattr(player, "level", 1) for player in game.players), default=1)


def player_power_rating(game):
    ratings = [player_power_rating_for(game, player) for player in game.alive_players()]
    if not ratings:
        ratings = [player_power_rating_for(game, player) for player in game.players]
    return max(ratings, default=1.0)


def player_power_rating_for(game, player):
    inv = game.get_inventory(player.player_index)
    projectile_ratio = game.projectile_damage_for(player, inv) / max(1.0, PROJECTILE_DAMAGE)
    sword_ratio = game.sword_damage_for(player, inv) / max(1.0, SWORD_DAMAGE)
    damage_score = max(projectile_ratio, sword_ratio)
    attack_score = game.effective_attack_rate_multiplier_for(player, inv)
    speed_score = game.effective_speed_multiplier_for(player)
    passive_levels = sum(max(0, level) for level in player.passives.values())
    item_levels = sum(max(0, getattr(item, "level", 0)) for item in inv.active_items())
    gear_score = 1.0 + min(0.80, passive_levels * 0.018 + item_levels * 0.022)
    return max(
        1.0,
        damage_score * 0.42
        + attack_score * 0.20
        + speed_score * 0.12
        + gear_score * 0.26,
    )


def enemy_spawn_scales(kind, difficulty):
    pressure = max(0.0, difficulty - 1.0)
    if kind in ELITE_KINDS:
        return {
            "health": min(9.5, 1.0 + pressure * 0.34),
            "speed": min(1.85, 1.0 + pressure * 0.055),
            "damage": min(2.15, 1.0 + pressure * 0.055),
        }
    if kind in HEAVY_KINDS:
        return {
            "health": min(5.4, 1.0 + pressure * 0.25),
            "speed": min(2.05, 1.0 + pressure * 0.070),
            "damage": min(1.90, 1.0 + pressure * 0.050),
        }
    return {
        "health": min(4.4, 1.0 + pressure * 0.22),
        "speed": min(2.10, 1.0 + pressure * 0.075),
        "damage": min(1.75, 1.0 + pressure * 0.045),
    }


def active_spitter_cap(game):
    return min(4, 2 + int(max(0.0, game.time_alive - 180.0) // 180.0))

