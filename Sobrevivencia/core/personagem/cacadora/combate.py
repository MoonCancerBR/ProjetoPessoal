from pygame.math import Vector2
import math

if __package__:
    from ....data.constants import *
    from ...entities import Projectile, Slash
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import Projectile, Slash


def cast_ultimate(game, aim_world, player):
    center = Vector2(aim_world)
    radius = game.special_radius_for(player) * 0.95
    marked = []
    for enemy in list(game.enemies):
        if enemy.pos.distance_squared_to(center) <= (radius + enemy.radius) ** 2:
            marked.append(enemy)
            enemy.bleed_timer = max(enemy.bleed_timer, 7.0)
            enemy.bleed_dps = max(enemy.bleed_dps, 34.0)
            enemy.hit_flash = 0.22
    for idx, enemy in enumerate(list(marked)):
        if enemy not in game.enemies:
            continue
        start = center + Vector2(math.cos(idx * 2.399), math.sin(idx * 2.399)) * radius
        game._apply_laser_damage(start, enemy.pos, 22, game.special_damage_for(player) * 0.34, damage_player=False, killer_index=player.player_index)
        game.item_events.append({
            "type": "laser",
            "start": start,
            "end": Vector2(enemy.pos),
            "width": 22,
            "age": 0.0,
            "duration": 0.24,
            "color": "#F97316",
        })
        if enemy.health <= enemy.max_health * 0.22:
            game.damage_enemy(enemy, enemy.max_health * 0.45, source="special", killer_index=player.player_index)
    game.emit_particles(center, count=54, color="#F97316", speed=260, lifetime=0.5, size=5)
    game.message = "Ultimate: Eclipse da Predadora!"


def cast_arrow_rain(game, aim_world, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
    if player is None:
        player = game.player
    storm_eye = player.passives.get("storm_eye", 0)
    duration = (2.0 + storm_eye * 0.12) * (1.0 + (multiplier - 1.0) * 0.5)
    game.item_events.append({
        "type": "arrow_rain",
        "pos": Vector2(aim_world),
        "timer": duration,
        "age": 0.0,
        "duration": duration,
        "damage": game.special_damage_for(player) * (0.18 + storm_eye * 0.006) * multiplier,
        "radius": game.special_radius_for(player) * 0.8 * radius_multiplier,
        "owner": player.player_index,
    })
    if not silent:
        game.message = "Chuva de Flechas!"


def cast_dagger_dance(game, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
    if player is None:
        player = game.player
    radius = 260 * radius_multiplier
    damage = game.special_damage_for(player) * 0.72 * multiplier
    for enemy in list(game.enemies):
        if enemy.pos.distance_squared_to(player.pos) <= (radius + enemy.radius) ** 2:
            enemy.bleed_timer = max(enemy.bleed_timer, 4.0)
            enemy.bleed_dps = max(enemy.bleed_dps, 18.0 * multiplier)
            push = enemy.pos - player.pos
            if push.length_squared() > 0:
                enemy.knockback += push.normalize() * 260
            game.damage_enemy(enemy, damage, source="special", killer_index=player.player_index)
    game.item_events.append({
        "type": "explosion",
        "pos": Vector2(player.pos),
        "radius": radius,
        "damage": 0,
        "age": 0.0,
        "duration": 0.32,
        "owner": player.player_index,
    })
    game.emit_particles(player.pos, count=24, color=COLORS["sword"], speed=190, lifetime=0.38, size=4)
    player.invulnerable_timer = max(player.invulnerable_timer, 0.65)
    game.screen_shake = max(game.screen_shake, 10.0)
    if not silent:
        game.message = "Danca das Adagas!"


def fire_primary(game, player, direction, inv):
    cooldown = (PROJECTILE_COOLDOWN * 0.92) / game.effective_attack_rate_multiplier_for(player, inv)
    if player.shoot_timer > 0 or len(game.projectiles) >= MAX_PROJECTILES:
        return
    if not game._consume_ranged_ammo_for(player):
        return
    game._flag_ranged_attack_for_quest()

    split_level = player.passives.get("splinter_arrows", 0)
    angles = [-3.0, 0.0, 3.0]
    side_pairs = 0 if split_level <= 0 else 1 + split_level // 6
    for pair in range(1, side_pairs + 1):
        side_angle = 8.0 + pair * 5.0
        angles.extend((side_angle, -side_angle))

    for angle in angles:
        shot_dir = direction.rotate(angle)
        extra = abs(angle) > 3.1
        damage_scale = 0.40 if not extra else 0.23 + split_level * 0.018
        created = game._append_projectile_if_room(
            Projectile(
                pos=Vector2(player.pos) + shot_dir * (player.radius + 10),
                vel=shot_dir * (PROJECTILE_SPEED * 1.58),
                damage=game.projectile_damage_for(player, inv) * damage_scale,
                radius=game.projectile_radius_for(player, PROJECTILE_RADIUS * (0.85 if extra else 0.92)),
                life=PROJECTILE_LIFE * (1.10 if not extra else 0.95),
                freeze=player.buffs.get("freeze", 0) > 0,
                pierce=1 if not extra else max(0, split_level // 5),
                explosive_level=player.passives.get("explosive", 0),
                homing_level=player.passives.get("homing", 0),
                owner=player.player_index,
                style="huntress_burst",
                color="#FACC15",
                trail_scale=4.5,
                knockback=38,
            )
        )
        if not created:
            break

    game.emit_particles(player.pos + direction * 14, count=6, color="#FACC15", speed=170, lifetime=0.15, size=3)
    player.shoot_timer = cooldown


def swing_melee(game, player, direction, inv):
    cooldown = (SWORD_COOLDOWN * 0.40) / game.effective_attack_rate_multiplier_for(player, inv)
    if player.sword_timer > 0:
        return
    for angle in (-12, 12):
        game.slashes.append(
            Slash(
                origin=Vector2(player.pos),
                direction=direction.rotate(angle),
                radius=game.sword_radius_for(player, inv) * 0.60,
                arc=game.dagger_arc_for(player) * 0.92,
                damage=game.sword_damage_for(player, inv) * 0.32,
                duration=SWORD_DURATION * 0.46,
                prey_mark_level=player.passives.get("prey_mark", 0),
                bleed_level=player.passives.get("bleeding_blades", 0),
                shadow_lunge_level=player.passives.get("shadow_lunge", 0),
                owner=player.player_index,
                style="huntress_combo",
                color="#FDE047",
                edge_color="#FEF3C7",
                knockback=165,
            )
        )
    player.sword_timer = cooldown
