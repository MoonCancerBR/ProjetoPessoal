from pygame.math import Vector2
import math

if __package__:
    from .....data.constants import *
else:
    from Sobrevivencia.data.constants import *


def apply_reaper_presence(game, enemy, dt):
    game.heat_level = max(getattr(game, "heat_level", 0.0), 100.0)
    for player in game.alive_players():
        if enemy.pos.distance_squared_to(player.pos) > REAPER_AURA_RADIUS * REAPER_AURA_RADIUS:
            continue
        debuff = game.player_debuffs.setdefault(player.player_index, {})
        debuff["movement_slow_timer"] = max(debuff.get("movement_slow_timer", 0.0), 0.35)
        debuff["movement_slow_multiplier"] = 0.58
        if player.invulnerable_timer <= 0:
            game._damage_player_direct(player, REAPER_AURA_DPS * dt, source="reaper")


def reaper_velocity(game, enemy, direction, chase_speed, dt):
    target = game._nearest_alive_player(enemy.pos)
    distance = enemy.pos.distance_to(target.pos)
    if enemy.action:
        return resolve_reaper_action(game, enemy, direction, chase_speed, dt)

    enemy.special_timer -= dt
    if enemy.special_timer <= 0 and distance < 980:
        roll = game.random.random()
        if distance > 230 and roll < 0.38:
            start_reaper_blink(game, enemy, target)
            return Vector2(0, 0)
        if roll < 0.66:
            start_reaper_dash(game, enemy, target)
            return Vector2(0, 0)
        start_reaper_doom(game, enemy, target)
        return Vector2(0, 0)

    side = direction.rotate(90 if math.sin(enemy.phase * 2.1 + enemy.id) > 0 else -90)
    if distance > 460:
        desired = direction * 1.55 + side * 0.16
    elif distance < 120:
        desired = direction * 0.92 + side * 0.55
    else:
        desired = direction * 1.18 + side * 0.32
    return desired.normalize() * chase_speed


def resolve_reaper_action(game, enemy, direction, chase_speed, dt):
    enemy.action_timer -= dt
    if enemy.action == "reaper_dash":
        if enemy.action_timer <= 0:
            start = Vector2(getattr(enemy, "dash_start", enemy.pos))
            end = Vector2(enemy.pos)
            game._apply_laser_damage(start, end, 78, enemy.damage * 0.85, ignore_enemy=enemy)
            game.item_events.append({
                "type": "laser",
                "start": start,
                "end": end,
                "width": 78,
                "age": 0.0,
                "duration": 0.24,
                "color": "#991B1B",
            })
            game.screen_shake = max(game.screen_shake, 14.0)
            enemy.action = ""
            enemy.special_timer = game.random.uniform(2.0, 3.2)
            return Vector2(0, 0)
        return Vector2(getattr(enemy, "dash_dir", direction)) * chase_speed * 3.2

    if enemy.action_timer <= 0:
        if enemy.action == "reaper_blink":
            landing = game.world.move_circle(Vector2(enemy.target_pos), enemy.radius, Vector2(0, 0), include_destructibles=False)
            enemy.pos = landing
            if enemy.body:
                enemy.body.position = landing.x, landing.y
            game._apply_area_damage(landing, 150, enemy.damage * 1.05, "reaper", ignore_enemy=enemy)
            game.item_events.append({
                "type": "explosion",
                "pos": landing,
                "radius": 150,
                "damage": 0,
                "age": 0.0,
                "duration": 0.30,
            })
            game.emit_particles(landing, count=28, color="#DC2626", speed=220, lifetime=0.44, size=6)
            game.screen_shake = max(game.screen_shake, 12.0)
        elif enemy.action == "reaper_doom":
            center = Vector2(enemy.target_pos)
            game._apply_area_damage(center, REAPER_DOOM_RADIUS, enemy.damage * 1.22, "reaper", ignore_enemy=enemy)
            game.item_events.append({
                "type": "explosion",
                "pos": center,
                "radius": REAPER_DOOM_RADIUS,
                "damage": 0,
                "age": 0.0,
                "duration": 0.34,
            })
            game.emit_particles(center, count=34, color="#7F1D1D", speed=210, lifetime=0.50, size=7)
            game.screen_shake = max(game.screen_shake, 16.0)
        enemy.action = ""
        enemy.special_timer = game.random.uniform(2.8, 4.4)
    return Vector2(0, 0)


def start_reaper_blink(game, enemy, target):
    target_dir = Vector2(getattr(target, "last_move_dir", Vector2(1, 0)))
    if target_dir.length_squared() <= 0.001:
        target_dir = Vector2(1, 0)
    target_dir = target_dir.normalize()
    landing = Vector2(target.pos) - target_dir * 110 + game.random_offset(36)
    enemy.target_pos = landing
    enemy.action = "reaper_blink"
    enemy.action_timer = REAPER_BLINK_WARNING
    game.item_events.append({
        "type": "danger_circle",
        "pos": landing,
        "radius": 150,
        "age": 0.0,
        "duration": REAPER_BLINK_WARNING,
        "color": "#7F1D1D",
    })
    game.message = "O Ceifador rasga o espaco ao seu redor."


def start_reaper_dash(game, enemy, target):
    dash_dir = target.pos - enemy.pos
    if dash_dir.length_squared() <= 0.001:
        dash_dir = Vector2(1, 0)
    dash_dir = dash_dir.normalize()
    enemy.dash_dir = Vector2(dash_dir)
    enemy.dash_start = Vector2(enemy.pos)
    enemy.target_pos = Vector2(enemy.pos) + dash_dir * REAPER_DASH_RANGE
    enemy.action = "reaper_dash"
    enemy.action_timer = REAPER_DASH_WARNING
    game.item_events.append({
        "type": "danger_line",
        "start": Vector2(enemy.pos),
        "end": Vector2(enemy.target_pos),
        "width": 88,
        "age": 0.0,
        "duration": REAPER_DASH_WARNING,
        "color": "#DC2626",
    })
    game.message = "O Ceifador prepara uma investida de execucao."


def start_reaper_doom(game, enemy, target):
    center = Vector2(target.pos) + game.random_offset(24)
    enemy.target_pos = center
    enemy.action = "reaper_doom"
    enemy.action_timer = REAPER_DOOM_WARNING
    game.item_events.append({
        "type": "danger_circle",
        "pos": center,
        "radius": REAPER_DOOM_RADIUS,
        "age": 0.0,
        "duration": REAPER_DOOM_WARNING,
        "color": "#991B1B",
    })
    game.message = "O Ceifador marcou o terreno com uma sentenca."

