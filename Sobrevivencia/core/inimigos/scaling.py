if __package__:
    from ...data.constants import *
else:
    from Sobrevivencia.data.constants import *


ELITE_KINDS = {"miniboss", "harbinger", "reaper", "god"}
HEAVY_KINDS = {"brute", "bulwark", "golem", "necromancer", "chromatic"}
TIER_COLORS = {
    "veteran": "#F59E0B",
    "elite": "#F97316",
    "corrupted": "#A855F7",
    "champion": "#F43F5E",
}


def enemy_difficulty_rating(game):
    time_factor = max(0.0, game.time_alive) / 92.0
    level_factor = max(0, highest_player_level(game) - 1) * 0.12
    power_factor = max(0.0, player_power_rating(game) - 1.0) * POWER_SCORE_WEIGHT
    pressure_factor = getattr(game, "director_pressure", 0.0) * 0.85
    return 1.0 + time_factor + level_factor + power_factor + pressure_factor


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
    stamp_levels = 0
    for stamps in getattr(player, "weapon_stamps", {}).values():
        stamp_levels += sum(max(1, getattr(stamp, "level", 1)) for stamp in stamps)
    stamp_levels += sum(max(1, getattr(stamp, "level", 1)) for stamp in getattr(player, "stamp_reserve", [])) * 0.35
    relic_score = sum(1 for item in inv.active_items() if getattr(item, "is_relic", False)) * 0.18
    gear_score = 1.0 + min(1.35, passive_levels * 0.018 + item_levels * 0.024 + stamp_levels * 0.026 + relic_score)
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
        "health": min(5.2, 1.0 + pressure * 0.28),
        "speed": min(2.10, 1.0 + pressure * 0.075),
        "damage": min(1.90, 1.0 + pressure * 0.055),
    }


def active_spitter_cap(game):
    return min(4, 2 + int(max(0.0, game.time_alive - 180.0) // 180.0))


def choose_enemy_tier(game, kind, difficulty):
    if kind in ELITE_KINDS or game.time_alive < ELITE_TIER_START_TIME:
        return "common"
    pressure = max(0.0, difficulty - 2.0)
    heat = getattr(game, "heat_level", 0.0) / 100.0
    late = max(0.0, game.time_alive - LATE_GAME_START_TIME) / 600.0
    roll = game.random.random()
    champion = min(0.08, 0.005 + late * 0.020 + heat * 0.020)
    corrupted = min(0.16, 0.015 + pressure * 0.014 + heat * 0.030)
    elite = min(0.24, 0.035 + pressure * 0.020 + late * 0.030)
    veteran = min(0.34, 0.080 + pressure * 0.026 + heat * 0.035)
    if roll < champion:
        return "champion"
    if roll < champion + corrupted:
        return "corrupted"
    if roll < champion + corrupted + elite:
        return "elite"
    if roll < champion + corrupted + elite + veteran:
        return "veteran"
    return "common"


def apply_enemy_tier(enemy, tier):
    ranks = {"common": 0, "veteran": 1, "elite": 2, "corrupted": 3, "champion": 4}
    rank = ranks.get(tier, 0)
    enemy.tier = tier
    enemy.tier_rank = rank
    if rank <= 0:
        return enemy
    health_mult = [1.0, 1.35, 1.85, 2.35, 3.20][rank]
    damage_mult = [1.0, 1.08, 1.16, 1.24, 1.35][rank]
    speed_mult = [1.0, 1.04, 1.08, 1.12, 1.16][rank]
    enemy.max_health *= health_mult
    enemy.health *= health_mult
    enemy.damage *= damage_mult
    enemy.speed *= speed_mult
    enemy.xp_value = max(enemy.xp_value + rank, int(enemy.xp_value * (1.0 + rank * 0.22)))
    enemy.special_value *= 1.0 + rank * 0.12
    enemy.coin_chance = min(0.85, enemy.coin_chance + rank * 0.018)
    enemy.damage_resistance = min(0.32, 0.06 * rank)
    if tier in TIER_COLORS:
        enemy.color = TIER_COLORS[tier]
    if tier in ("corrupted", "champion"):
        enemy.immune_to_knockback = True
    return enemy
