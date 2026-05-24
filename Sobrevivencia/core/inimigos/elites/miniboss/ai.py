from pygame.math import Vector2
import math

if __package__:
    from .....data.constants import *
else:
    from Sobrevivencia.data.constants import *


def miniboss_velocity(game, enemy, direction, chase_speed, dt):
    enemy.summon_cooldown = max(0.0, enemy.summon_cooldown - dt)
    if enemy.action:
        enemy.action_timer -= dt
        if enemy.action_timer <= 0:
            resolve_miniboss_action(game, enemy, direction)
            enemy.action = ""
            enemy.special_timer = game.random.uniform(3.2, 5.2)
        return Vector2(0, 0)

    enemy.special_timer -= dt
    target = game._nearest_alive_player(enemy.pos)
    if enemy.special_timer <= 0 and enemy.pos.distance_squared_to(target.pos) < (900 * 900):
        choose_miniboss_action(game, enemy)
        return Vector2(0, 0)

    return direction * chase_speed


def resolve_miniboss_action(game, enemy, direction):
    if enemy.action == "leap_warn":
        landing = Vector2(enemy.target_pos)
        enemy.pos = game.world.move_circle(landing, enemy.radius, Vector2(0, 0), include_destructibles=False)
        game._apply_area_damage(landing, MINIBOSS_LEAP_RADIUS, MINIBOSS_LEAP_DAMAGE, "miniboss", ignore_enemy=enemy)
        game.item_events.append({
            "type": "explosion",
            "pos": landing,
            "radius": MINIBOSS_LEAP_RADIUS,
            "damage": 0,
            "age": 0.0,
            "duration": 0.28,
        })
        game.emit_particles(landing, count=28, color=COLORS["danger"], speed=230, lifetime=0.38, size=6)
        game.screen_shake = max(game.screen_shake, 13.0)
    elif enemy.action == "laser_warn":
        start = Vector2(enemy.pos)
        end = Vector2(enemy.target_pos)
        game._apply_laser_damage(start, end, MINIBOSS_LASER_WIDTH, MINIBOSS_LASER_DAMAGE, ignore_enemy=enemy)
        game.item_events.append({
            "type": "laser",
            "start": start,
            "end": end,
            "width": MINIBOSS_LASER_WIDTH,
            "age": 0.0,
            "duration": 0.22,
            "color": "#F97316",
        })
        game.screen_shake = max(game.screen_shake, 8.0)
    elif enemy.action == "shockwave_warn":
        center = Vector2(enemy.pos)
        game._apply_area_damage(center, 220, 36, "miniboss", ignore_enemy=enemy)
        game.item_events.append({
            "type": "explosion",
            "pos": center,
            "radius": 220,
            "damage": 0,
            "age": 0.0,
            "duration": 0.34,
        })
        game.emit_particles(center, count=30, color="#C4B5FD", speed=220, lifetime=0.42, size=5)
        game.screen_shake = max(game.screen_shake, 12.0)
    elif enemy.action == "charge_warn":
        start = Vector2(enemy.pos)
        target = Vector2(enemy.target_pos)
        direction_charge = target - start
        if direction_charge.length_squared() <= 0.001:
            direction_charge = direction
        direction_charge = direction_charge.normalize()
        end = start + direction_charge * 420
        enemy.pos = game.world.move_circle(enemy.pos, enemy.radius, direction_charge * 420, include_destructibles=False)
        game._apply_laser_damage(start, end, 74, 24, ignore_enemy=enemy)
        game.emit_particles(enemy.pos, count=22, color=COLORS["danger"], speed=210)
        game.screen_shake = max(game.screen_shake, 11.0)


def choose_miniboss_action(game, enemy):
    roll = game.random.random()
    if not enemy.enraged and enemy.health <= enemy.max_health * 0.45:
        enemy.enraged = True
        enemy.speed *= 1.22
        enemy.damage *= 1.18
        game.message = "Mini-boss enfurecido!"
    if roll < 0.30 and enemy.summon_cooldown <= 0:
        start_miniboss_summon(game, enemy)
    elif roll < 0.52:
        start_miniboss_leap(game, enemy)
    elif roll < 0.64:
        start_miniboss_laser(game, enemy)
    elif roll < 0.84:
        start_miniboss_charge(game, enemy)
    else:
        start_miniboss_shockwave(game, enemy)


def start_miniboss_leap(game, enemy):
    leap_target = game._nearest_alive_player(enemy.pos)
    target = Vector2(leap_target.pos) + game.random_offset(70)
    enemy.target_pos = target
    enemy.action = "leap_warn"
    enemy.action_timer = MINIBOSS_LEAP_WARNING
    game.item_events.append({
        "type": "danger_circle",
        "pos": target,
        "radius": MINIBOSS_LEAP_RADIUS,
        "age": 0.0,
        "duration": MINIBOSS_LEAP_WARNING,
        "color": COLORS["danger"],
    })
    game.message = "Salto do mini-boss: saia do circulo vermelho."


def start_miniboss_laser(game, enemy):
    laser_target = game._nearest_alive_player(enemy.pos)
    direction = laser_target.pos - enemy.pos
    if direction.length_squared() <= 0.001:
        direction = Vector2(1, 0)
    direction = direction.normalize()
    start = Vector2(enemy.pos)
    end = start + direction * MINIBOSS_LASER_RANGE
    enemy.target_pos = end
    enemy.action = "laser_warn"
    enemy.action_timer = MINIBOSS_LASER_WARNING
    game.item_events.append({
        "type": "danger_line",
        "start": start,
        "end": end,
        "width": MINIBOSS_LASER_WIDTH,
        "age": 0.0,
        "duration": MINIBOSS_LASER_WARNING,
        "color": COLORS["danger"],
    })
    game.message = "Laser do mini-boss: fuja da faixa vermelha."


def start_miniboss_shockwave(game, enemy):
    enemy.action = "shockwave_warn"
    enemy.action_timer = 0.78
    game.item_events.append({
        "type": "danger_circle",
        "pos": Vector2(enemy.pos),
        "radius": 220,
        "age": 0.0,
        "duration": 0.78,
        "color": COLORS["danger"],
    })
    game.message = "Pulso do mini-boss: afaste-se."


def start_miniboss_charge(game, enemy):
    target = game._nearest_alive_player(enemy.pos)
    enemy.target_pos = Vector2(target.pos)
    enemy.action = "charge_warn"
    enemy.action_timer = 0.55
    game.item_events.append({
        "type": "danger_line",
        "start": Vector2(enemy.pos),
        "end": Vector2(target.pos),
        "width": 70,
        "age": 0.0,
        "duration": 0.55,
        "color": COLORS["danger"],
    })
    game.message = "Investida do mini-boss: saia da linha!"


def start_miniboss_summon(game, enemy):
    enemy.action = "summon"
    enemy.action_timer = MINIBOSS_SUMMON_DURATION
    enemy.summon_cooldown = game.random.uniform(MINIBOSS_SUMMON_COOLDOWN_MIN, MINIBOSS_SUMMON_COOLDOWN_MAX)
    count = game.random.randint(MINIBOSS_SUMMON_COUNT_MIN, MINIBOSS_SUMMON_COUNT_MAX)
    spawned = 0
    for _ in range(count * 4):
        if spawned >= count:
            break
        angle = game.random.random() * math.tau
        dist = game.random.uniform(60, 130)
        pos = enemy.pos + Vector2(math.cos(angle), math.sin(angle)) * dist
        if not game.world.circle_hits_wall(pos, 11):
            game._spawn_minion(pos)
            spawned += 1
    game.item_events.append({
        "type": "summon_pulse",
        "pos": Vector2(enemy.pos),
        "radius": 140,
        "age": 0.0,
        "duration": MINIBOSS_SUMMON_DURATION,
    })
    game.message = "Mini-boss invocou reforcos!"
