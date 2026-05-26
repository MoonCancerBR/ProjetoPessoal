from pygame.math import Vector2
import math

if __package__:
    from ...data.constants import *
    from ..entities import EscortNPC
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import EscortNPC


def update_world_timers(game, dt):
    for chunk in game.world.chunks.values():
        for item in chunk["destructibles"]:
            item.hit_flash = max(0, item.hit_flash - dt)
    if not game.escort_event_active:
        game.next_escort_timer = getattr(game, "next_escort_timer", 180.0) - dt
        if game.next_escort_timer <= 0.0:
            trigger_escort_event(game)
    else:
        update_escort_event(game, dt)


def trigger_escort_event(game):
    game.escort_event_active = True
    game.escort_state = "seeking_spawn"
    angle = game.random.uniform(0, 2 * math.pi)
    spawn_dist = 900.0
    game.escort_spawn_pos = game.player.pos + Vector2(math.cos(angle), math.sin(angle)) * spawn_dist
    extract_angle = game.random.uniform(0, 2 * math.pi)
    extract_dist = 1600.0
    game.escort_extract_pos = game.escort_spawn_pos + Vector2(math.cos(extract_angle), math.sin(extract_angle)) * extract_dist
    game.escort_npcs = []
    game.message = "MISSAO DE ESCOLTA: Encontre os aliados!"


def update_escort_event(game, dt):
    if game.escort_state == "seeking_spawn":
        if any(player.pos.distance_to(game.escort_spawn_pos) <= 150.0 for player in game.alive_players()):
            game.escort_state = "escorting"
            game.escort_npcs = [
                EscortNPC(pos=Vector2(game.escort_spawn_pos) + Vector2(-15, -15), hp=120.0, max_hp=120.0, speed=85.0, kind="soldier"),
                EscortNPC(pos=Vector2(game.escort_spawn_pos) + Vector2(15, 15), hp=150.0, max_hp=150.0, speed=80.0, kind="executive"),
            ]
            game.message = "MISSAO DE ESCOLTA: Proteja os aliados ate o ponto de extracao!"
        return
    if game.escort_state == "escorting":
        npcs_alive = 0
        reached_extract = 0
        for npc in game.escort_npcs:
            if npc.hp <= 0:
                continue
            npcs_alive += 1
            npc.hit_flash = max(0, npc.hit_flash - dt)
            to_extract = game.escort_extract_pos - npc.pos
            if to_extract.length() > 50.0:
                npc.pos += to_extract.normalize() * npc.speed * dt
            else:
                reached_extract += 1
        if npcs_alive == 0:
            game.escort_state = "failed"
            game.message = "MISSAO FALHOU: Todos os aliados morreram."
            game.escort_post_event_timer = 5.0
        elif reached_extract == npcs_alive:
            game.escort_state = "completed"
            game.escort_post_event_timer = 5.0
            game.completed_escorts = getattr(game, "completed_escorts", 0) + 1
            if game.completed_escorts >= 4:
                game.grant_chalice_fragment("escort_4", game.escort_extract_pos)
        return
    if game.escort_state in ("completed", "failed"):
        game.escort_post_event_timer = getattr(game, "escort_post_event_timer", 5.0) - dt
        if game.escort_post_event_timer <= 0.0:
            game.escort_event_active = False
            game.escort_state = None
            game.escort_npcs = []
            game.next_escort_timer = 240.0
