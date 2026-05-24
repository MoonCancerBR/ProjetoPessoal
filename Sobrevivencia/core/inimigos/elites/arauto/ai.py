import math

if __package__:
    from .....data.constants import MAX_ENEMIES
else:
    from Sobrevivencia.data.constants import MAX_ENEMIES


def harbinger_velocity(game, enemy, direction, chase_speed, dt):
    target = game._nearest_alive_player(enemy.pos)
    enemy.summon_cooldown -= dt
    distance = enemy.pos.distance_to(target.pos)
    if enemy.summon_cooldown <= 0:
        enemy.summon_cooldown = game.random.uniform(7.0, 10.0)
        for _ in range(5):
            pos = enemy.pos + game.random_offset(150)
            if len(game.enemies) < MAX_ENEMIES:
                kind = game.random.choice(["morcego_sombra", "necromancer"])
                game._spawn_minion(pos, kind=kind)
        game.add_alert(enemy.pos, "LEGIAO SOMBRIA", "#9333EA")
        game.emit_particles(enemy.pos, count=34, color="#9333EA", speed=180)

    side = direction.rotate(90 if math.sin(enemy.phase * 1.9) > 0 else -90)
    if distance < 150:
        desired = -direction * 0.4 + side * 0.65
    else:
        desired = direction * 1.15 + side * 0.22
    return desired.normalize() * chase_speed

