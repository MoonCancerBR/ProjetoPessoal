from pygame.math import Vector2
import math

if __package__:
    from ...data.constants import *
    from ..entities import Enemy
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import Enemy


def spawn_enemies(game, dt):
    if getattr(game, "current_dimension", "main") == "olympus":
        return
    heat_multiplier = 1.0 + getattr(game, "heat_level", 0.0) / 100.0 * 0.75
    difficulty = game._enemy_difficulty_rating() * heat_multiplier
    game._update_special_spawns(dt, difficulty)

    if len(game.enemies) >= MAX_ENEMIES:
        return

    delay = max(SPAWN_MIN_DELAY, SPAWN_START_DELAY / difficulty)
    game.spawn_timer -= dt
    if game.spawn_timer > 0:
        return

    game.spawn_timer = delay
    amount = 1
    if game.time_alive > 80 and game.random.random() < 0.28:
        amount += 1
    if game.time_alive > 170 and game.random.random() < 0.18:
        amount += 1
    for _ in range(amount):
        game._spawn_one_enemy(difficulty)


def update_special_spawns(game, dt, difficulty):
    heat_factor = 1.0 + getattr(game, "heat_level", 0.0) / 100.0 * 1.5
    game.harbinger_spawn_timer = getattr(game, "harbinger_spawn_timer", HARBINGER_SPAWN_INTERVAL) - dt
    has_harbinger = any(enemy.kind == "harbinger" for enemy in game.enemies)
    if game.harbinger_spawn_timer <= 0 and not has_harbinger and len(game.enemies) < MAX_ENEMIES:
        if game._spawn_special_enemy("harbinger", difficulty):
            game.harbinger_spawn_timer = HARBINGER_SPAWN_INTERVAL

    game._update_reaper_spawn_pressure(dt)
    has_reaper = any(enemy.kind == "reaper" for enemy in game.enemies)
    if game.reaper_spawn_timer <= 0 and not has_reaper and len(game.enemies) < MAX_ENEMIES:
        if game.time_alive >= REAPER_MIN_SPAWN_TIME:
            if game._spawn_special_enemy("reaper", difficulty):
                game.reaper_spawn_timer = REAPER_SPAWN_INTERVAL
        else:
            game.reaper_spawn_timer = REAPER_SPAWN_INTERVAL

    game.chromatic_spawn_timer -= dt * heat_factor
    if game.chromatic_spawn_timer <= 0:
        if len(game.enemies) < MAX_ENEMIES:
            if game._spawn_special_enemy("chromatic", difficulty):
                game.chromatic_spawn_timer = game.random.uniform(CHROMATIC_SPAWN_MIN, CHROMATIC_SPAWN_MAX)
        else:
            game.chromatic_spawn_timer = game.random.uniform(CHROMATIC_SPAWN_MIN, CHROMATIC_SPAWN_MAX)

    game.miniboss_spawn_timer -= dt * (1.0 + getattr(game, "heat_level", 0.0) / 100.0 * 0.5)
    has_miniboss = any(enemy.kind == "miniboss" for enemy in game.enemies)
    has_boss = any(enemy.kind in ("reaper", "harbinger") for enemy in game.enemies)
    if game.miniboss_spawn_timer <= 0:
        if game.time_alive > 45 and not has_miniboss and not has_boss and len(game.enemies) < MAX_ENEMIES:
            if game._spawn_special_enemy("miniboss", difficulty):
                game.miniboss_spawn_timer = game.random.uniform(MINIBOSS_SPAWN_MIN, MINIBOSS_SPAWN_MAX)
        elif has_miniboss or has_boss or len(game.enemies) >= MAX_ENEMIES:
            game.miniboss_spawn_timer = game.random.uniform(MINIBOSS_SPAWN_MIN, MINIBOSS_SPAWN_MAX)


def update_reaper_spawn_pressure(game, dt):
    if any(enemy.kind == "reaper" for enemy in game.enemies):
        game.reaper_area_anchor = Vector2(game.camera_focus)
        game.reaper_area_linger = 0.0
        game.reaper_pressure_level = 0.0
        return
    focus = Vector2(game.camera_focus)
    anchor = getattr(game, "reaper_area_anchor", None)
    if anchor is None:
        game.reaper_area_anchor = Vector2(focus)
        game.reaper_area_linger = 0.0
        game.reaper_pressure_level = 0.0
        return
    if focus.distance_to(anchor) > REAPER_STALL_RADIUS:
        game.reaper_area_anchor = Vector2(focus)
        game.reaper_area_linger = 0.0
        game.reaper_pressure_level = 0.0
    else:
        game.reaper_area_linger = min(REAPER_SPAWN_INTERVAL, getattr(game, "reaper_area_linger", 0.0) + dt)
        linger_overflow = max(0.0, game.reaper_area_linger - REAPER_STALL_GRACE)
        game.reaper_pressure_level = min(1.0, linger_overflow / max(1.0, REAPER_STALL_GRACE * 1.35))
    pressure_factor = 1.0 + game.reaper_pressure_level * REAPER_STALL_ACCEL_MAX
    minimum_remaining = max(0.0, REAPER_MIN_SPAWN_TIME - game.time_alive)
    current_timer = getattr(game, "reaper_spawn_timer", REAPER_SPAWN_INTERVAL) - dt * pressure_factor
    game.reaper_spawn_timer = max(minimum_remaining, current_timer)


def spawn_special_enemy(game, kind, difficulty):
    angle = game.random.random() * math.tau
    if kind == "chromatic":
        distance = game.random.uniform(420, 610)
        scales = game._enemy_spawn_scales(kind, difficulty)
        health_scale = scales["health"]
        speed_scale = scales["speed"]
        damage_scale = scales["damage"]
        lifetime = CHROMATIC_LIFETIME
        message = "Um Erratico Cromatico apareceu perto da tela."
    elif kind == "harbinger":
        distance = game.random.uniform(780, 960)
        rank = getattr(game, "harbinger_defeats", 0)
        scales = game._enemy_spawn_scales(kind, difficulty)
        health_scale = (1.0 + rank * 0.55) * scales["health"]
        speed_scale = scales["speed"] + min(0.35, rank * 0.06)
        damage_scale = scales["damage"] + min(0.30, rank * 0.04)
        lifetime = -1
        message = "O ARAUTO DO FIM chegou. Fuja, kite ou prove que merece continuar."
    elif kind == "reaper":
        distance = game.random.uniform(560, 720)
        rank = getattr(game, "reaper_defeats", 0)
        scales = game._enemy_spawn_scales(kind, difficulty)
        health_scale = (1.05 + rank * 0.75) * scales["health"]
        speed_scale = scales["speed"] + min(0.40, rank * 0.07)
        damage_scale = scales["damage"] + min(0.35, rank * 0.05)
        lifetime = -1
        if getattr(game, "reaper_pressure_level", 0.0) >= 0.5:
            message = "O CEIFADOR da Margem sentiu sua demora. Mova-se ou seja executado."
        else:
            message = "O CEIFADOR da Margem chegou para encerrar a run."
    else:
        distance = game.random.uniform(650, 820)
        scales = game._enemy_spawn_scales(kind, difficulty)
        health_scale = scales["health"]
        speed_scale = scales["speed"]
        damage_scale = scales["damage"]
        lifetime = -1
        message = "Mini-boss avistado: fique longe dos avisos vermelhos."

    pos = game.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance
    data = ENEMY_TYPES[kind]
    enemy = Enemy(
        id=game.enemy_id,
        pos=pos,
        kind=kind,
        radius=data["radius"],
        speed=data["speed"] * speed_scale * game.director_speed,
        max_health=data["health"] * health_scale * game.director_health,
        health=data["health"] * health_scale * game.director_health,
        damage=data["damage"] * damage_scale * game.director_damage,
        xp_value=data["xp"],
        color=data["color"],
        special_value=data["special"],
        coin_chance=data["coin_chance"],
        lifetime=lifetime,
        phase=game.random.random() * math.tau,
        special_timer=game.random.uniform(2.2, 4.0),
    )
    if kind in ("miniboss", "harbinger", "reaper"):
        enemy.immune_to_knockback = True
    if kind == "harbinger":
        enemy.summon_cooldown = game.random.uniform(6.0, 8.0)
    elif kind == "reaper":
        enemy.special_timer = game.random.uniform(1.4, 2.2)
    game.enemy_id += 1
    game._setup_physics_entity(enemy)

    if not game.world.circle_hits_wall(enemy.pos, enemy.radius):
        game.enemies.append(enemy)
        game.message = message
        if kind == "miniboss":
            game.miniboss_arena_center = Vector2(enemy.pos)
            game.miniboss_arena_radius = 520.0
            trapped = min(game.alive_players(), key=lambda p: p.pos.distance_to(enemy.pos), default=game.player)
            game.miniboss_trapped_player = trapped
        elif kind == "reaper":
            game.reaper_area_anchor = Vector2(game.camera_focus)
            game.reaper_area_linger = 0.0
            game.reaper_pressure_level = 0.0
            game.emit_particles(enemy.pos, count=38, color="#DC2626", speed=170, lifetime=0.7, size=6)
        return True
    game._cleanup_physics_entity(enemy)
    return False


def spawn_one_enemy(game, difficulty):
    angle = game.random.random() * math.tau
    distance = game.random.uniform(SPAWN_DISTANCE_MIN, SPAWN_DISTANCE_MAX)
    pos = game.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance

    kind = game._weighted_enemy_kind(pos)
    if kind == "spitter" and sum(1 for enemy in game.enemies if enemy.kind == "spitter") >= game._active_spitter_cap():
        kind = "runner" if game.time_alive > 25 else "basic"

    data = ENEMY_TYPES[kind]
    scales = game._enemy_spawn_scales(kind, difficulty)
    enemy = Enemy(
        id=game.enemy_id,
        pos=pos,
        kind=kind,
        radius=data["radius"],
        speed=data["speed"] * scales["speed"] * game.director_speed,
        max_health=data["health"] * scales["health"] * game.director_health,
        health=data["health"] * scales["health"] * game.director_health,
        damage=data["damage"] * scales["damage"] * game.director_damage,
        xp_value=data["xp"],
        color=data["color"],
        special_value=data["special"],
        coin_chance=data["coin_chance"],
    )
    game.enemy_id += 1
    game._setup_physics_entity(enemy)

    if not game.world.circle_hits_wall(enemy.pos, enemy.radius):
        game.enemies.append(enemy)


def weighted_enemy_kind(game, pos):
    is_night = getattr(game, "light_level", 1.0) < 0.15
    terrain = game.world.terrain_at(pos.x, pos.y)
    pocket = getattr(game, "current_dimension", "main") == "pocket"
    weights = {"basic": 38, "runner": 18 if game.time_alive > 25 else 6, "brute": 10 if game.time_alive > 75 else 0}
    if game.time_alive > 95:
        weights["spitter"] = 5
    if game.time_alive > 150:
        weights["bulwark"] = 8
    if game.time_alive > 190:
        weights["sapper"] = 7
    if terrain == "sand":
        weights["runner"] = weights.get("runner", 0) + 14
        weights["sapper"] = weights.get("sapper", 0) + 8
    elif terrain == "mud":
        weights["brute"] = weights.get("brute", 0) + 12
        weights["necromancer"] = weights.get("necromancer", 0) + 8
    elif terrain == "stone":
        weights["golem"] = 18
        weights["bulwark"] = weights.get("bulwark", 0) + 12
    else:
        weights["spitter"] = weights.get("spitter", 0) + 3
    active_spitters = sum(1 for enemy in game.enemies if enemy.kind == "spitter")
    if active_spitters >= game._active_spitter_cap():
        weights["spitter"] = 0
    if is_night:
        weights["morcego_sombra"] = weights.get("morcego_sombra", 0) + 30
        weights["lobo_infectado"] = weights.get("lobo_infectado", 0) + 24
        weights["phantom"] = weights.get("phantom", 0) + 12
        weights["basic"] = max(4, weights.get("basic", 0) // 2)
    if pocket:
        weights["morcego_sombra"] = weights.get("morcego_sombra", 0) + 34
        weights["lobo_infectado"] = weights.get("lobo_infectado", 0) + 30
        weights["necromancer"] = weights.get("necromancer", 0) + 12
    total = sum(max(0, value) for value in weights.values())
    roll = game.random.uniform(0, total)
    upto = 0
    for kind, value in weights.items():
        upto += max(0, value)
        if roll <= upto:
            return kind
    return "basic"

