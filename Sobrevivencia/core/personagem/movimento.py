from pygame.math import Vector2

if __package__:
    from ...data.constants import DASH_SPEED
else:
    from Sobrevivencia.data.constants import DASH_SPEED


def move_player(game, dt, move_vector, aim_world):
    move_player_for(game, dt, move_vector, aim_world, game.player)


def move_player_for(game, dt, move_vector, aim_world, player):
    player.is_moving_input = move_vector.length_squared() > 0.01
    if move_vector.length_squared() > 0:
        move_vector = move_vector.normalize()
        player.last_move_dir = Vector2(move_vector)

    if player.dash_timer > 0:
        velocity = player.dash_dir * DASH_SPEED
    else:
        terrain_speed = game.world.speed_multiplier_at(player.pos.x, player.pos.y)
        speed = player.base_speed * game.effective_speed_multiplier_for(player) * terrain_speed
        velocity = move_vector * speed

    player.pos = game.world.move_circle(player.pos, player.radius, velocity * dt)
    enforce_miniboss_arena(game, player, dt)

    if player.body:
        player.body.position = player.pos.x, player.pos.y
        player.body.velocity = 0, 0
    if player.shield_timer > 0:
        game._repel_enemies(dt, player)


def enforce_miniboss_arena(game, player, dt):
    center = getattr(game, "miniboss_arena_center", None)
    if center is None:
        return
    trapped = getattr(game, "miniboss_trapped_player", None)
    is_trapped = trapped == player if trapped is not None else True
    radius = getattr(game, "miniboss_arena_radius", 520.0)
    dist = player.pos.distance_to(center)
    if is_trapped:
        if dist <= radius:
            return
        to_center = (center - player.pos).normalize()
        player.pos = center + (player.pos - center).normalize() * radius
        if hasattr(player, "knockback"):
            player.knockback += to_center * 150.0
        game._damage_player_direct(player, 6.0 * dt)
        game.message = "Fugindo da Arena do Miniboss! Sofrendo dano!"
        return
    if dist >= radius:
        return
    to_outside = (player.pos - center).normalize()
    player.pos = center + to_outside * radius
    if hasattr(player, "knockback"):
        player.knockback += to_outside * 150.0
    game._damage_player_direct(player, 6.0 * dt)
    game.message = "Impossivel entrar na Arena do Miniboss!"

