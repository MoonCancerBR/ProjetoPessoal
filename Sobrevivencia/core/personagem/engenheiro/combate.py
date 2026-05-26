from pygame.math import Vector2
import math

if __package__:
    from ....data.constants import *
    from ...entities import PlayerConstruct, Slash
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import PlayerConstruct, Slash


def cast_ultimate(game, aim_world, player):
    center = Vector2(aim_world)
    cast_magnetic_implosion(game, center, multiplier=1.35, player=player, silent=True)
    for idx, angle in enumerate((0, math.tau / 3, math.tau * 2 / 3)):
        pos = player.pos + Vector2(math.cos(angle), math.sin(angle)) * 86
        spawn_construct(game, pos, "turret" if idx != 1 else "laser_turret", player.player_index, level=2, duration=18.0)
    for _ in range(4):
        pos = player.pos + game.random_offset(110)
        spawn_construct(game, pos, "drone", player.player_index, level=1, duration=15.0)
    game.emit_particles(player.pos, count=70, color="#EAB308", speed=300, lifetime=0.55, size=5)
    game.message = "Ultimate: Fabrica Ragnarok!"


def spawn_construct(game, pos, kind, owner, level=1, duration=12.0):
    hp = 85.0 + level * 35.0
    radius = 14.0 if kind != "drone" else 9.0
    construct = PlayerConstruct(
        pos=Vector2(pos),
        kind=kind,
        hp=hp,
        max_hp=hp,
        radius=radius,
        duration=duration,
        owner=owner,
        level=level,
    )
    game.player_constructs.append(construct)
    return construct


def cast_turret_grid(game, aim_world, player=None):
    if player is None:
        player = game.player
    direction = Vector2(aim_world) - player.pos
    if direction.length_squared() <= 0.01:
        direction = player.last_move_dir
    direction = direction.normalize()
    side = direction.rotate(90)
    base = player.pos + direction * 86
    spawn_construct(game, base - side * 42, "turret", player.player_index, level=1, duration=16.0)
    spawn_construct(game, base + side * 42, "laser_turret", player.player_index, level=1, duration=13.0)
    game.emit_particles(base, count=24, color="#EAB308", speed=170, lifetime=0.35, size=4)
    game.message = "Engenheiro: grade de torretas implantada."


def cast_magnetic_implosion(game, aim_world, multiplier=1.0, player=None, silent=False):
    if player is None:
        player = game.player
    center = Vector2(aim_world)
    radius = 285
    damage = game.special_damage_for(player) * 0.95 * multiplier
    pulled = 0
    for enemy in list(game.enemies):
        diff = center - enemy.pos
        dist = diff.length()
        if dist <= radius + enemy.radius:
            if diff.length_squared() > 0:
                enemy.pos += diff.normalize() * min(150, max(35, dist * 0.42))
                enemy.knockback += diff.normalize() * 180
            pulled += 1
    burst = damage * (1.0 + min(0.55, pulled * 0.045))
    for enemy in list(game.enemies):
        if enemy.pos.distance_squared_to(center) <= (145 + enemy.radius) ** 2:
            game.damage_enemy(enemy, burst, source="special", killer_index=player.player_index)
    game.item_events.append({
        "type": "explosion",
        "pos": center,
        "radius": radius,
        "damage": 0,
        "age": 0.0,
        "duration": 0.34,
        "owner": player.player_index,
    })
    game.emit_particles(center, count=40, color="#A78BFA", speed=260, lifetime=0.45, size=5)
    if not silent:
        game.message = "Engenheiro: singularidade magnetica detonada."


def fire_primary(game, player, direction, inv):
    cooldown = (PROJECTILE_COOLDOWN * 1.04) / game.effective_attack_rate_multiplier_for(player, inv)
    if player.shoot_timer > 0:
        return
    if not game._consume_ranged_ammo_for(player):
        return
    game._flag_ranged_attack_for_quest()

    start = Vector2(player.pos) + direction * (player.radius + 10)
    end = start + direction * 470
    damage = game.projectile_damage_for(player, inv) * 0.92
    plasma_aoe = player.passives.get("plasma_aoe", 0)
    supercharge = player.passives.get("supercharge", 0)
    hit_enemies = game._segment_enemies(start, end, 24 + supercharge * 2)

    for index, (_, enemy) in enumerate(hit_enemies):
        shot_damage = damage * max(0.62, 1.0 - index * 0.10)
        if player.buffs.get("freeze", 0) > 0:
            enemy.frozen_timer = max(enemy.frozen_timer, FREEZE_DURATION * 0.65)
        if supercharge > 0 and game.random.random() < min(0.7, 0.16 + supercharge * 0.06):
            enemy.frozen_timer = max(enemy.frozen_timer, 0.45 + supercharge * 0.08)
            game.add_floater(enemy.pos, "CURTO!", "#93C5FD")
        enemy.knockback += direction * (42 + supercharge * 10)
        game.damage_enemy(enemy, shot_damage, source="laser", killer_index=player.player_index)
        game._apply_stamp_on_hit(enemy, shot_damage, "weapon_1", player.player_index)
        if plasma_aoe > 0 and index == 0:
            game.item_events.append({
                "type": "explosion",
                "pos": Vector2(enemy.pos),
                "radius": 34 + plasma_aoe * 10,
                "damage": shot_damage * (0.22 + plasma_aoe * 0.05),
                "age": 0.0,
                "duration": 0.18,
                "owner": player.player_index,
            })

    game.item_events.append({
        "type": "laser",
        "start": start,
        "end": end,
        "width": 16 + supercharge * 2,
        "age": 0.0,
        "duration": 0.12,
        "color": "#38BDF8",
    })
    game.emit_particles(start, count=8, color="#38BDF8", speed=160, lifetime=0.16, size=3)
    player.shoot_timer = cooldown


def swing_melee(game, player, direction, inv):
    cooldown = (SWORD_COOLDOWN * 0.78) / game.effective_attack_rate_multiplier_for(player, inv)
    if player.sword_timer > 0:
        return
    heavy_alloy = player.passives.get("heavy_alloy", 0)
    magnetic_pull = player.passives.get("magnetic_pull", 0)
    game.slashes.append(
        Slash(
            origin=Vector2(player.pos),
            direction=direction,
            radius=game.sword_radius_for(player, inv) * 0.82,
            arc=game.sword_arc_for(player) * 0.82,
            damage=game.sword_damage_for(player, inv) * (0.82 + heavy_alloy * 0.04),
            duration=SWORD_DURATION * 0.80,
            heavy_alloy_level=heavy_alloy,
            magnetic_pull_level=magnetic_pull,
            owner=player.player_index,
            style="engineer_wrench",
            color="#38BDF8",
            edge_color="#DBEAFE",
            knockback=70 + heavy_alloy * 18,
            pull_strength=140 + magnetic_pull * 28,
        )
    )
    player.sword_timer = cooldown
