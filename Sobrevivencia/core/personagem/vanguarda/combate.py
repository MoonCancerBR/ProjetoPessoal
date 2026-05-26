from pygame.math import Vector2
import math

if __package__:
    from ....data.constants import *
    from ...entities import Projectile, Slash
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import Projectile, Slash


def cast_ultimate(game, aim_world, player):
    center = Vector2(player.pos)
    radius = game.special_radius_for(player) * 1.05
    player.activate_shield()
    player.shield_timer = max(player.shield_timer, 5.0)
    for ring in range(3):
        game.item_events.append({
            "type": "explosion",
            "pos": center,
            "radius": radius * (0.45 + ring * 0.28),
            "damage": 0,
            "age": 0.0,
            "duration": 0.35 + ring * 0.08,
            "owner": player.player_index,
        })
    for enemy in list(game.enemies):
        dist = enemy.pos.distance_to(center)
        if dist <= radius + enemy.radius:
            direction = enemy.pos - center
            if direction.length_squared() > 0:
                enemy.knockback += direction.normalize() * (760 - min(520, dist))
            damage = game.special_damage_for(player) * (1.15 + max(0.0, 1.0 - dist / radius) * 0.75)
            game.damage_enemy(enemy, damage, source="special", killer_index=player.player_index)
    game.emit_particles(center, count=72, color="#38BDF8", speed=320, lifetime=0.55, size=6)
    game.message = "Ultimate: Bastiao de Ruptura!"


def cast_radial(game, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
    if player is None:
        player = game.player
    special_damage = game.special_damage_for(player) * multiplier
    special_radius = game.special_radius_for(player) * radius_multiplier
    game.special_blast_timer = 0.35
    game.screen_shake = max(game.screen_shake, 16.0)
    game.emit_particles(player.pos, count=34, color=COLORS["special"], speed=260, lifetime=0.44, size=6)
    if not silent:
        game.message = "Explosao radial liberada!"

    for enemy in list(game.enemies):
        distance = enemy.pos.distance_to(player.pos)
        if distance <= special_radius:
            direction = enemy.pos - player.pos
            if direction.length_squared() > 0:
                enemy.knockback += direction.normalize() * 520
            game.damage_enemy(enemy, special_damage, source="special", killer_index=player.player_index)

    for item in list(game.world.nearby_destructibles(player.pos.x, player.pos.y, special_radius * 0.75)):
        if item.rect.center.distance_to(player.pos) <= special_radius * 0.75:
            game.destroy_destructible(item)

    reactor = player.passives.get("reactor_blast", 0)
    if reactor > 0:
        restored = min(game.magazine_capacity_for(player) - player.ammo_magazine, 2 + reactor * 2)
        if restored > 0:
            player.ammo_magazine += restored
            player.forced_reload = False
            player.reload_timer = 0
            player.mode = "weapon_1"
            if not silent:
                game.message = "Explosao radial liberada! Pente reenergizado."


def cast_charge(game, aim_world, multiplier=1.0, silent=False, player=None):
    if player is None:
        player = game.player
    direction = Vector2(aim_world) - player.pos
    if direction.length_squared() <= 0.01:
        direction = player.last_move_dir
    if direction.length_squared() <= 0.01:
        direction = Vector2(1, 0)
    direction = direction.normalize()
    start = Vector2(player.pos)
    end = start + direction * 420
    width = 78
    damage = game.special_damage_for(player) * 0.88 * multiplier
    game._apply_laser_damage(start, end, width, damage, damage_player=False, killer_index=player.player_index)
    player.pos = game.world.move_circle(player.pos, player.radius, direction * 240, include_destructibles=False)
    game.item_events.append({
        "type": "laser",
        "start": start,
        "end": end,
        "width": width,
        "age": 0.0,
        "duration": 0.26,
        "color": COLORS["sword"],
    })
    game.emit_particles(player.pos, count=18, color=COLORS["sword"], speed=210, lifetime=0.30, size=5)
    game.screen_shake = max(game.screen_shake, 12.0)
    if not silent:
        game.message = "Carga Titanica!"


def fire_primary(game, player, direction, inv):
    cooldown = (PROJECTILE_COOLDOWN * 1.18) / game.effective_attack_rate_multiplier_for(player, inv)
    if player.shoot_timer > 0 or len(game.projectiles) >= MAX_PROJECTILES:
        return
    if not game._consume_ranged_ammo_for(player):
        return
    game._flag_ranged_attack_for_quest()

    pellet_count = game.ranged_projectiles_per_salvo(player)
    pellet_center = (pellet_count - 1) * 0.5
    pierce = player.passives.get("piercing_rounds", 0) // 3
    damage_scale = 0.54 + min(0.16, pellet_count * 0.015)
    life = 0.40 + min(0.18, pierce * 0.03)
    side = direction.rotate(90)
    for index in range(pellet_count):
        angle = (index - pellet_center) * 7.0
        shot_dir = direction.rotate(angle)
        offset = side * ((index - pellet_center) * 5.5)
        created = game._append_projectile_if_room(
            Projectile(
                pos=Vector2(player.pos) + shot_dir * (player.radius + 8) + offset,
                vel=shot_dir * (PROJECTILE_SPEED * 0.94),
                damage=game.projectile_damage_for(player, inv) * damage_scale,
                radius=game.projectile_radius_for(player, PROJECTILE_RADIUS * 0.88),
                life=life,
                freeze=player.buffs.get("freeze", 0) > 0,
                poison=player.passives.get("poison", 0) > 0,
                poison_dps=POISON_BASE_DPS * player.passives.get("poison", 0) * player.damage_multiplier(),
                bounces_left=player.passives.get("ricochet", 0),
                pierce=pierce,
                owner=player.player_index,
                style="vanguard_pellet",
                color="#EF4444",
                trail_scale=2.1,
                knockback=96 + player.passives.get("piercing_rounds", 0) * 9,
            )
        )
        if not created:
            break

    game.emit_particles(player.pos + direction * 10, count=8, color="#F87171", speed=120, lifetime=0.18, size=3)
    player.shoot_timer = cooldown


def swing_melee(game, player, direction, inv):
    cooldown = (SWORD_COOLDOWN * 1.08) / game.effective_attack_rate_multiplier_for(player, inv)
    if player.sword_timer > 0:
        return
    game.slashes.append(
        Slash(
            origin=Vector2(player.pos),
            direction=direction,
            radius=game.sword_radius_for(player, inv) * 1.05,
            arc=game.sword_arc_for(player) + math.radians(8),
            damage=game.sword_damage_for(player, inv) * 1.14,
            duration=SWORD_DURATION * 1.08,
            execute_level=player.passives.get("execution_edge", 0),
            shockwave_level=player.passives.get("shockwave", 0),
            owner=player.player_index,
            style="vanguard_cleave",
            color="#FB7185",
            edge_color="#FDE68A",
            knockback=430,
        )
    )
    player.sword_timer = cooldown
