import math

from pygame.math import Vector2

if __package__:
    from ...data.constants import *
else:
    from Sobrevivencia.data.constants import *


def active_ready(game):
    return game.omni_kernel_active and game.omni_active_cooldown <= 0.0


def time_freeze_active(game):
    return getattr(game, "omni_time_freeze_timer", 0.0) > 0.0


def time_freeze_multiplier(game):
    if not time_freeze_active(game):
        return 1.0
    return OMNI_TIME_FREEZE_ENEMY_MULTIPLIER


def active_charge_ratio(game):
    if not game.omni_kernel_active:
        return 0.0
    if time_freeze_active(game):
        return 1.0
    if game.omni_active_cooldown <= 0.0:
        return 1.0
    return max(0.0, 1.0 - game.omni_active_cooldown / OMNI_TIME_FREEZE_COOLDOWN)


def active_status(game):
    if not game.omni_kernel_active:
        return "TRAVADO"
    if time_freeze_active(game):
        return f"{game.omni_time_freeze_timer:.0f}s"
    if game.omni_active_cooldown <= 0.0:
        return "PRONTO"
    return f"{game.omni_active_cooldown:.0f}s"


def update_runtime(game, dt):
    if game.omni_active_cooldown > 0:
        was_cooling = game.omni_active_cooldown
        game.omni_active_cooldown = max(0.0, game.omni_active_cooldown - dt)
        if was_cooling > 0 and game.omni_active_cooldown <= 0:
            for player in game.alive_players():
                game.add_alert(player.pos, "OMNI PRONTO", "#FACC15")
            game.message = "Omni-Kernel recarregado."
    if game.omni_time_freeze_timer > 0:
        game.omni_time_freeze_timer = max(0.0, game.omni_time_freeze_timer - dt)
    if game.omni_kernel_active:
        game.omni_orbital_timer -= dt
        if game.omni_orbital_timer <= 0:
            fire_orbital_laser(game)
            game.omni_orbital_timer = OMNI_ORBITAL_COOLDOWN


def activate(game, pos):
    game.omni_kernel_active = True
    for player in game.players:
        player.max_health += 120
        player.health = player.max_health
        player.damage_bonus += 0.60
        player.attack_rate_bonus += 0.45
        player.speed_bonus += 0.35
        player.sword_range_bonus += 0.45
        player.special_gain_bonus += 1.0
        player.vampirism += 8.0
    game.item_events.append({"type": "explosion", "pos": Vector2(pos), "radius": 360, "damage": 0, "age": 0.0, "duration": 0.7, "owner": 0})
    game.item_events.append({"type": "omni_burst", "pos": Vector2(pos), "radius": 280, "age": 0.0, "duration": 1.0, "color": "#FACC15"})
    game.emit_particles(pos, count=120, color="#FACC15", speed=390, lifetime=0.9, size=7)
    game.screen_shake = max(game.screen_shake, 24.0)
    for player in game.players:
        game.add_alert(player.pos, "OMNI PRONTO", "#FACC15")
    game.message = "OMNI-KERNEL desperto: o Calice da Singularidade esta completo!"


def fire_orbital_laser(game):
    center = Vector2(game.camera_focus)
    angle = game.random.uniform(-0.7, 0.7)
    direction = Vector2(math.cos(angle), math.sin(angle))
    start = center - direction * 720 + direction.rotate(90) * game.random.uniform(-260, 260)
    end = start + direction * 1500
    game._apply_laser_damage(start, end, 74, 155, damage_player=False, killer_index=0, knockback=520)
    game.item_events.append({"type": "laser", "start": start, "end": end, "width": 74, "age": 0.0, "duration": 0.32, "color": "#FACC15"})
    game.screen_shake = max(game.screen_shake, 10.0)


def try_active(game):
    if not game.omni_kernel_active:
        return False
    if game.omni_active_cooldown > 0:
        game.message = f"Parada temporal recarregando: {game.omni_active_cooldown:.0f}s."
        return False
    game.omni_time_freeze_timer = OMNI_TIME_FREEZE_DURATION
    game.omni_active_cooldown = OMNI_TIME_FREEZE_COOLDOWN
    for player in game.alive_players():
        game.item_events.append({
            "type": "omni_burst",
            "pos": Vector2(player.pos),
            "radius": 220,
            "age": 0.0,
            "duration": 1.1,
            "color": "#BAE6FD",
        })
        game.add_alert(player.pos, "TEMPO CONGELADO", "#BAE6FD")
    game.emit_particles(game.camera_focus, count=90, color="#BAE6FD", speed=260, lifetime=0.65, size=5)
    game.screen_shake = max(game.screen_shake, 18.0)
    game.message = "Omni-Kernel: o tempo dos inimigos foi quebrado!"
    return True

