import math
from pygame.math import Vector2

if __package__:
    from ...data.constants import *
else:
    from Sobrevivencia.data.constants import *


MAX_ACTIVE_ALTARS = 2
ALTAR_FIRST_SPAWN_DELAY = 10.0
ALTAR_RESPAWN_DELAY = 35.0


def spawn_altar(game):
    active_altars = [altar for altar in getattr(game, "altars", []) if getattr(altar, "active", False)]
    if len(active_altars) >= MAX_ACTIVE_ALTARS:
        return False

    angle = game.random.random() * math.tau
    distance = game.random.uniform(400.0, 600.0)
    spawn_pos = game.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance
    spawn_pos = game.world.move_circle(spawn_pos, 24.0, Vector2(0, 0))
    kinds = ["weapon_altar", "stamps_altar", "skill_altar", "stat_altar", "black_market_altar"]
    active_kinds = {altar.kind for altar in active_altars}
    kinds = [kind for kind in kinds if kind not in active_kinds]
    if getattr(game, "black_market_cooldown", 0.0) > 0:
        kinds = [kind for kind in kinds if kind != "black_market_altar"]
    if not _has_upgradeable_passives(game) and "skill_altar" in kinds:
        kinds.remove("skill_altar")
    if not kinds:
        return False

    kind = game.random.choice(kinds)
    try:
        from ..entities import Altar
    except ImportError:
        from Sobrevivencia.core.entities import Altar
    game.altars.append(Altar(pos=spawn_pos, kind=kind))
    names = {
        "weapon_altar": "Armas (Inventario)",
        "stamps_altar": "Selos",
        "skill_altar": "Habilidades (Passivas)",
        "stat_altar": "Status",
        "black_market_altar": "Mercado Negro",
    }
    game.message = f"Um Altar de {names[kind]} se manifestou na arena!"
    game.add_floater(spawn_pos, "ALTAR", COLORS["special"])
    return True


def update_altars(game, dt):
    alive = []
    for altar in game.altars:
        altar.age += dt
        altar.hit_flash = max(0, altar.hit_flash - dt)
        if altar.kind == "skill_altar" and not _has_upgradeable_passives(game):
            altar.active = False
        if altar.active:
            alive.append(altar)
            if game.active_altar is None:
                for player in game.alive_players():
                    if player.pos.distance_to(altar.pos) <= player.radius + altar.radius:
                        game.active_altar = altar
                        game.time_scale = 0.2
                        game.menu_player_index = player.player_index
                        game.menu_just_opened_by_altar = altar.kind
                        game.message = "Altar ativado! Selecione seus aprimoramentos."
                        game.emit_particles(altar.pos, count=25, color="#F59E0B", speed=150)
                        break
        else:
            game.emit_particles(altar.pos, count=30, color="#EF4444", speed=200)
    game.altars = alive
    if getattr(game, "altar_spawn_timer", 0.0) > 0.0:
        game.altar_spawn_timer -= dt
        if game.altar_spawn_timer <= 0.0:
            spawn_altar(game)
            game.altar_spawn_timer = ALTAR_RESPAWN_DELAY


def _has_upgradeable_passives(game):
    for player in getattr(game, "players", []):
        passives = getattr(player, "passives", {})
        if any(level < 10 for level in passives.values()):
            return True
    return False


def finish_altar_interaction(game, destroy=True):
    altar = getattr(game, "active_altar", None)
    if altar is not None and destroy:
        if altar.kind == "black_market_altar":
            game.black_market_cooldown = 60.0
        altar.active = False
        game.emit_particles(altar.pos, count=36, color="#F59E0B", speed=220)
        game.screen_shake = max(game.screen_shake, 10.0)
    game.active_altar = None
    game.menu_just_opened_by_altar = None
    game.time_scale = 1.0
