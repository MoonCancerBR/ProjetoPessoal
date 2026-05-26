from pygame.math import Vector2

if __package__:
    from ....data.constants import *
    from ...entities import Projectile, Slash
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import Projectile, Slash


def cast_rosary(game, aim_world, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
    if player is None:
        player = game.player
    red_eclipse = player.passives.get("red_eclipse", 0)
    duration = 2.8 + red_eclipse * 0.14
    game.item_events.append({
        "type": "blood_zone",
        "pos": Vector2(aim_world),
        "timer": duration,
        "pulse_timer": 0.0,
        "age": 0.0,
        "duration": duration,
        "damage": game.special_damage_for(player) * (0.17 + red_eclipse * 0.008) * multiplier,
        "radius": game.special_radius_for(player) * 0.62 * radius_multiplier,
        "owner": player.player_index,
        "mark_bonus": 1 if red_eclipse >= 5 else 0,
    })
    game.emit_particles(aim_world, count=26, color="#991B1B", speed=170, lifetime=0.34, size=4)
    if not silent:
        game.message = "Rosario de Dor!"


def cast_harvest(game, aim_world, multiplier=1.0, silent=False, player=None):
    if player is None:
        player = game.player
    direction = Vector2(aim_world) - player.pos
    if direction.length_squared() <= 0.01:
        direction = player.last_move_dir
    if direction.length_squared() <= 0.01:
        direction = Vector2(1, 0)
    direction = direction.normalize()

    red_eclipse = player.passives.get("red_eclipse", 0)
    start = Vector2(player.pos)
    end = start + direction * (240 + red_eclipse * 8)
    hits = game._segment_enemies(start, end, 54 + red_eclipse * 2)
    consumed_total = 0
    for _, enemy in hits:
        consumed = game._consume_blood_mark(enemy, player, special_gain_scale=0.7)
        consumed_total += consumed
        enemy.bleed_timer = max(enemy.bleed_timer, 3.2 + red_eclipse * 0.12)
        enemy.bleed_dps = max(enemy.bleed_dps, 11.0 + red_eclipse * 1.8)
        enemy.knockback += direction * (150 + consumed * 36)
        damage = game.special_damage_for(player) * (0.56 + consumed * 0.16) * multiplier
        game.damage_enemy(enemy, damage, source="special", killer_index=player.player_index)
        if consumed <= 0:
            game._apply_blood_mark(enemy, player, bonus_duration=0.4)

    player.pos = game.world.move_circle(player.pos, player.radius, direction * (170 + red_eclipse * 4), include_destructibles=False)
    game.item_events.append({
        "type": "laser",
        "start": start,
        "end": end,
        "width": 34 + red_eclipse * 2,
        "age": 0.0,
        "duration": 0.18,
        "color": "#991B1B",
    })
    if consumed_total > 0:
        capacity = game.magazine_capacity_for(player)
        restored = min(capacity - player.ammo_magazine, consumed_total)
        if restored > 0:
            player.ammo_magazine += restored
            player.forced_reload = False
            game.add_floater(player.pos, f"+{restored} pente", "#FCA5A5")
        heal = min(player.max_health - player.health, consumed_total * (3.0 + player.passives.get("harvest_heal", 0) * 0.4))
        if heal > 0:
            player.health += heal
            game.add_floater(player.pos, f"+{heal:.0f}", COLORS["health"])
    game.emit_particles(player.pos, count=20, color="#7F1D1D", speed=220, lifetime=0.28, size=4)
    game.screen_shake = max(game.screen_shake, 11.0)
    if not silent:
        game.message = "Colheita Rubra!"


def cast_ultimate(game, aim_world, player):
    red_eclipse = player.passives.get("red_eclipse", 0)
    center = Vector2(player.pos)
    radius = game.special_radius_for(player) * (0.82 + red_eclipse * 0.012)
    player.activate_buff("reaper_frenzy")
    player.buffs["reaper_frenzy"] = max(player.buffs.get("reaper_frenzy", 0.0), 5.2 + red_eclipse * 0.30)
    player.invulnerable_timer = max(player.invulnerable_timer, 0.55)

    for enemy in list(game.enemies):
        if enemy.pos.distance_squared_to(center) > (radius + enemy.radius) ** 2:
            continue
        game._apply_blood_mark(enemy, player, bonus_duration=1.0, level_bonus=1)
        enemy.bleed_timer = max(enemy.bleed_timer, 5.0 + red_eclipse * 0.15)
        enemy.bleed_dps = max(enemy.bleed_dps, 15.0 + red_eclipse * 2.0)
        diff = enemy.pos - center
        if diff.length_squared() > 0:
            enemy.knockback += diff.normalize() * (220 + red_eclipse * 8)
        damage = game.special_damage_for(player) * (0.52 + max(0.0, 1.0 - enemy.pos.distance_to(center) / max(1.0, radius)) * 0.24)
        game.damage_enemy(enemy, damage, source="special", killer_index=player.player_index)

    game.item_events.append({
        "type": "blood_zone",
        "pos": center,
        "timer": 3.2 + red_eclipse * 0.16,
        "pulse_timer": 0.0,
        "age": 0.0,
        "duration": 3.2 + red_eclipse * 0.16,
        "damage": game.special_damage_for(player) * (0.11 + red_eclipse * 0.006),
        "radius": radius * 0.72,
        "owner": player.player_index,
        "mark_bonus": 1,
    })
    game.item_events.append({
        "type": "explosion",
        "pos": center,
        "radius": radius,
        "damage": 0,
        "age": 0.0,
        "duration": 0.42,
        "owner": player.player_index,
    })
    game.emit_particles(center, count=64, color="#DC2626", speed=300, lifetime=0.52, size=5)
    game.message = "Ultimate: Noite da Degola!"


def fire_primary(game, player, direction, inv):
    frenzy = player.buffs.get("reaper_frenzy", 0) > 0
    cooldown = (PROJECTILE_COOLDOWN * (0.98 if frenzy else 1.10)) / game.effective_attack_rate_multiplier_for(player, inv)
    if player.shoot_timer > 0 or len(game.projectiles) >= MAX_PROJECTILES:
        return
    if not game._consume_ranged_ammo_for(player):
        return
    game._flag_ranged_attack_for_quest()

    count = game.ranged_projectiles_per_salvo(player)
    center = (count - 1) * 0.5
    side = direction.rotate(90)
    mourning_pierce = player.passives.get("mourning_pierce", 0)
    extra_bounce = 1 if frenzy else 0
    for index in range(count):
        spread = (index - center) * 4.0
        shot_dir = direction.rotate(spread)
        offset = side * ((index - center) * 6.0)
        extra = abs(index - center) > 0.01
        damage_scale = (0.68 if not extra else 0.52) * (1.08 if frenzy else 1.0)
        created = game._append_projectile_if_room(
            Projectile(
                pos=Vector2(player.pos) + shot_dir * (player.radius + 9) + offset,
                vel=shot_dir * (PROJECTILE_SPEED * (1.34 if frenzy else 1.22)),
                damage=game.projectile_damage_for(player, inv) * damage_scale,
                radius=game.projectile_radius_for(player, PROJECTILE_RADIUS * 0.78),
                life=PROJECTILE_LIFE * (1.12 if frenzy else 1.02),
                bounces_left=extra_bounce,
                pierce=1 + mourning_pierce // 3,
                homing_level=1 if frenzy else 0,
                owner=player.player_index,
                style="reaper_needle",
                color="#991B1B",
                trail_scale=4.8,
                knockback=26,
                mark_level=1 + player.passives.get("blood_mark", 0) // 4,
                mark_duration=2.0 + player.passives.get("funeral_volley", 0) * 0.06,
            )
        )
        if not created:
            break

    game.emit_particles(player.pos + direction * 12, count=7, color="#B91C1C", speed=140, lifetime=0.20, size=3)
    player.shoot_timer = cooldown


def swing_melee(game, player, direction, inv):
    frenzy = player.buffs.get("reaper_frenzy", 0) > 0
    cooldown = (SWORD_COOLDOWN * (0.62 if frenzy else 0.72)) / game.effective_attack_rate_multiplier_for(player, inv)
    if player.sword_timer > 0:
        return
    game.slashes.append(
        Slash(
            origin=Vector2(player.pos),
            direction=direction,
            radius=game.sword_radius_for(player, inv) * (0.92 if frenzy else 0.84),
            arc=game.sword_arc_for(player) * (0.98 if frenzy else 0.90),
            damage=game.sword_damage_for(player, inv) * (0.78 if frenzy else 0.70),
            duration=SWORD_DURATION * (0.74 if frenzy else 0.70),
            bleed_level=player.passives.get("hemorrhage", 0),
            owner=player.player_index,
            style="reaper_scythe",
            color="#991B1B",
            edge_color="#FECACA",
            knockback=210,
            consume_mark=True,
        )
    )
    player.sword_timer = cooldown
