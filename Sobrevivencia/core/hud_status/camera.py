from pygame.math import Vector2

if __package__:
    from ...data.constants import *
else:
    from Sobrevivencia.data.constants import *


def camera_focus(game):
    if game.multiplayer and game.player2:
        alive = game.alive_players()
        if len(alive) == 2:
            return (alive[0].pos + alive[1].pos) * 0.5
        if len(alive) == 1:
            return alive[0].pos
        return game.players[0].pos

    player = game.get_player(game.camera_focus_index)
    if player.is_down and game.multiplayer:
        other = game.get_player(1 - game.camera_focus_index)
        if not other.is_down:
            return other.pos
    return player.pos


def update_camera(game, dt):
    focus_pos = game.camera_focus
    target = Vector2(
        focus_pos.x - SCREEN_WIDTH * 0.5,
        focus_pos.y - SCREEN_HEIGHT * 0.5,
    )

    if game.multiplayer and game.player2:
        alive = game.alive_players()
        if len(alive) == 2:
            distance = alive[0].pos.distance_to(alive[1].pos)
            scale = 1.0
            if distance > 300:
                t = min(1.0, (distance - 300) / (CAMERA_ZOOM_MAX_DISTANCE - 300))
                scale = 1.0 - t * (1.0 - CAMERA_ZOOM_MIN_SCALE)
            game.camera_zoom += (scale - game.camera_zoom) * dt * 2.0
        else:
            game.camera_zoom += (1.0 - game.camera_zoom) * dt * 2.0
    else:
        game.camera_zoom = 1.0

    game.camera += (target - game.camera) * min(1.0, CAMERA_SMOOTHING * dt)
