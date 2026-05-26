import math

if __package__:
    from ...data.constants import BASE_MAGAZINE_CAPACITY, MAGAZINE_CAPACITY_PER_LEVEL, PROJECTILE_RADIUS, SCREEN_WIDTH, SPECIAL_DAMAGE, SPECIAL_RADIUS, STARTING_AMMO_RESERVE, SWORD_ARC
    from ...data.stamps import stamp_total_bonus
else:
    from Sobrevivencia.data.constants import BASE_MAGAZINE_CAPACITY, MAGAZINE_CAPACITY_PER_LEVEL, PROJECTILE_RADIUS, SCREEN_WIDTH, SPECIAL_DAMAGE, SPECIAL_RADIUS, STARTING_AMMO_RESERVE, SWORD_ARC
    from Sobrevivencia.data.stamps import stamp_total_bonus


def effective_speed_multiplier_for(game, player):
    inv = game.get_inventory(player.player_index)
    chrono = inv.active_effect_level("chrono_boots")
    debuff = game.player_debuffs.get(player.player_index, {})
    slow_mult = debuff.get("movement_slow_multiplier", 1.0) if debuff.get("movement_slow_timer", 0.0) > 0.0 else 1.0
    return player.speed_multiplier() * (1.0 + chrono * 0.015) * slow_mult


def effective_attack_rate_multiplier_for(game, player, inv):
    blade = inv.active_effect_level("blade_relay")
    hybrid = inv.active_hybrid_level()
    both_bonus = (
        player.passives.get("combat_drill", 0) * 0.01
        + player.passives.get("predator_focus", 0) * 0.012
        + player.passives.get("scarlet_reload", 0) * 0.004
    )
    stamp_bonus = stamp_total_bonus(player, player.mode, "haste")
    return player.attack_rate_multiplier() * (1.0 + blade * 0.012 + hybrid * 0.01 + both_bonus + stamp_bonus)


def projectile_damage_for(game, player, inv):
    storm = inv.active_effect_level("storm_core")
    stamp_bonus = stamp_total_bonus(player, "weapon_1", "impact")
    ranged_mult = (
        1.0
        + player.passives.get("combat_drill", 0) * 0.025
        + player.passives.get("predator_focus", 0) * 0.020
        + player.passives.get("piercing_rounds", 0) * 0.015
        + player.passives.get("mourning_pierce", 0) * 0.012
        + stamp_bonus
    )
    return player.projectile_damage() * (1.0 + storm * 0.01) * ranged_mult


def sword_damage_for(game, player, inv):
    blade = inv.active_effect_level("blade_relay")
    stamp_bonus = stamp_total_bonus(player, "weapon_2", "impact")
    melee_mult = (
        1.0
        + player.passives.get("combat_drill", 0) * 0.025
        + player.passives.get("predator_focus", 0) * 0.020
        + player.passives.get("fan_blades", 0) * 0.018
        + player.passives.get("harvest_heal", 0) * 0.010
        + stamp_bonus
    )
    return player.sword_damage() * (1.0 + blade * 0.012) * melee_mult


def projectile_radius_for(game, player, base_radius=PROJECTILE_RADIUS):
    caliber_bonus = stamp_total_bonus(player, "weapon_1", "caliber")
    return base_radius * (1.0 + caliber_bonus)


def sword_radius_for(game, player, inv):
    blade = inv.active_effect_level("blade_relay")
    hybrid = inv.active_hybrid_level()
    melee_bonus = (
        player.passives.get("wide_cleave", 0) * 0.030
        + player.passives.get("fan_blades", 0) * 0.028
        + player.passives.get("reaping_arc", 0) * 0.028
    )
    return player.sword_radius() * (1.0 + blade * 0.018 + hybrid * 0.018 + melee_bonus)


def sword_arc_for(player):
    return SWORD_ARC + math.radians(player.passives.get("wide_cleave", 0) * 2.4 + player.passives.get("reaping_arc", 0) * 2.2)


def dagger_arc_for(player):
    return SWORD_ARC * 0.6 + math.radians(player.passives.get("fan_blades", 0) * 2.8)


def special_damage_for(player):
    return SPECIAL_DAMAGE * (
        1.0
        + player.passives.get("reactor_blast", 0) * 0.055
        + player.passives.get("storm_eye", 0) * 0.040
        + player.passives.get("red_eclipse", 0) * 0.045
    )


def special_radius_for(player):
    return SPECIAL_RADIUS * (
        1.0
        + player.passives.get("reactor_blast", 0) * 0.030
        + player.passives.get("storm_eye", 0) * 0.025
        + player.passives.get("red_eclipse", 0) * 0.028
    )


def magazine_capacity_for(player):
    level_capacity = BASE_MAGAZINE_CAPACITY + max(0, player.level - 1) * MAGAZINE_CAPACITY_PER_LEVEL
    return level_capacity + player.magazine_bonus


def max_ammo_reserve_for(player):
    return STARTING_AMMO_RESERVE + max(0, player.level - 1) * 20

