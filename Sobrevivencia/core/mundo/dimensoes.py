from pygame.math import Vector2
import math

if __package__:
    from ...data.constants import *
    from ..world import World
    from ..entities import Enemy
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.world import World
    from Sobrevivencia.core.entities import Enemy


def save_dimension_state(game):
    return {
        "world": game.world,
        "camera": Vector2(game.camera),
        "enemies": game.enemies,
        "projectiles": game.projectiles,
        "slashes": game.slashes,
        "drops": game.drops,
        "altars": game.altars,
        "drones": game.drones,
        "constructs": game.player_constructs,
    }


def clear_runtime_lists(game):
    game.enemies = []
    game.projectiles = []
    game.slashes = []
    game.drops = []
    game.altars = []
    game.drones = []
    game.player_constructs = []
    game.miniboss_arena_center = None
    game.miniboss_trapped_player = None


def place_players_at_origin(game):
    base = Vector2(0, 0)
    for index, player in enumerate(game.alive_players()):
        player.pos = base + Vector2(index * 72, 0)
        if player.body:
            player.body.position = player.pos.x, player.pos.y
    game.world.ensure_area(base, 2)
    game.camera = Vector2(base.x - SCREEN_WIDTH * 0.5, base.y - SCREEN_HEIGHT * 0.5)
    return base


def enter_pocket_dimension(game):
    if getattr(game, "current_dimension", "main") == "pocket":
        game.pocket_dimension_timer = max(getattr(game, "pocket_dimension_timer", 0.0), 30.0)
        return
    for player in game.players:
        player.original_pos = Vector2(player.pos)
    game.pocket_dimension_state = save_dimension_state(game)
    game.main_world = game.world
    game.pocket_world = World()
    game.world = game.pocket_world
    clear_runtime_lists(game)
    game.current_dimension = "pocket"
    game.pocket_dimension_visits = getattr(game, "pocket_dimension_visits", 0) + 1
    place_players_at_origin(game)
    if not game.chalice_fragments.get("pocket_hidden", False):
        game.spawn_drop("chalice", game.pocket_chalice_pos, "pocket_hidden")
    if game.pocket_dimension_visits % 5 == 0:
        game.pocket_dimension_timer = 999999.0
        game.message = "O Vazio escurece. O Arauto Sombrio despertou!"
        heat_multiplier = 1.0 + getattr(game, "heat_level", 0.0) / 100.0 * 0.75
        difficulty = (1.0 + game.time_alive / 85.0 + (game.player.level - 1) * 0.09) * heat_multiplier
        if not game._spawn_special_enemy("harbinger", difficulty):
            force_spawn_pocket_harbinger(game, difficulty)
        game.harbinger_spawn_timer = HARBINGER_SPAWN_INTERVAL
    else:
        game.pocket_dimension_timer = 30.0
        game.message = "Dimensao de Bolso! Sobreviva ao HP Decay!"


def restore_main_dimension(game):
    state = getattr(game, "pocket_dimension_state", None)
    if state is None:
        game.current_dimension = "main"
        return None
    game.world = state["world"]
    game.main_world = game.world
    game.camera = Vector2(state["camera"])
    game.enemies = state["enemies"]
    game.projectiles = state["projectiles"]
    game.slashes = state["slashes"]
    game.drops = state["drops"]
    game.altars = state["altars"]
    game.drones = state["drones"]
    game.player_constructs = state["constructs"]
    game.current_dimension = "main"
    game.pocket_dimension_state = None
    game.miniboss_arena_center = None
    game.miniboss_trapped_player = None
    return state


def exit_pocket_dimension(game, reward=True):
    state = restore_main_dimension(game)
    if state is None:
        return
    game.pocket_world = None
    game.message = "Sobreviveu ao Vazio! Caixa Lendaria obtida!" if reward else "Saiu da Dimensao de Bolso."
    for player in game.alive_players():
        player.pos = Vector2(getattr(player, "original_pos", player.pos))
        if player.body:
            player.body.position = player.pos.x, player.pos.y
        if reward:
            game.spawn_drop("item_box", player.pos, 1)


def force_spawn_pocket_harbinger(game, difficulty):
    data = ENEMY_TYPES["harbinger"]
    rank = getattr(game, "harbinger_defeats", 0)
    scales = game._enemy_spawn_scales("harbinger", difficulty)
    health_scale = (1.0 + rank * 0.55) * scales["health"]
    speed_scale = scales["speed"] + min(0.35, rank * 0.06)
    damage_scale = scales["damage"] + min(0.30, rank * 0.04)
    pos = Vector2(0, -420)
    enemy = Enemy(
        id=game.enemy_id,
        pos=pos,
        kind="harbinger",
        radius=data["radius"],
        speed=data["speed"] * speed_scale * game.director_speed,
        max_health=data["health"] * health_scale * game.director_health,
        health=data["health"] * health_scale * game.director_health,
        damage=data["damage"] * damage_scale * game.director_damage,
        xp_value=data["xp"],
        color=data["color"],
        special_value=data["special"],
        coin_chance=data["coin_chance"],
        lifetime=-1,
        phase=game.random.random() * math.tau,
        special_timer=game.random.uniform(2.2, 4.0),
    )
    enemy.immune_to_knockback = True
    enemy.summon_cooldown = game.random.uniform(6.0, 8.0)
    game.enemy_id += 1
    game._setup_physics_entity(enemy)
    game.enemies.append(enemy)
    game.emit_particles(enemy.pos, count=44, color="#A855F7", speed=190, lifetime=0.8, size=6)


def enter_olympus_dimension(game):
    game.olympus_triggered = True
    for player in game.players:
        player.original_pos = Vector2(player.pos)
    game.pocket_dimension_state = save_dimension_state(game)
    game.main_world = game.world
    game.olympus_world = World()
    game.world = game.olympus_world
    clear_runtime_lists(game)
    game.current_dimension = "olympus"
    base = place_players_at_origin(game)
    game.message = "BEM-VINDO AO OLIMPO. PREPARE-SE PARA O DEUS."
    data = ENEMY_TYPES["god"]
    enemy = Enemy(
        id=game.enemy_id,
        pos=base + Vector2(0, -300),
        kind="god",
        radius=data["radius"],
        speed=data["speed"],
        max_health=data["health"],
        health=data["health"],
        damage=data["damage"],
        xp_value=data["xp"],
        color=data["color"],
        special_value=data["special"],
        coin_chance=data["coin_chance"],
        lifetime=-1,
        phase=game.random.random() * math.tau,
        special_timer=3.0,
    )
    enemy.immune_to_knockback = True
    enemy.summon_cooldown = 10.0
    game.enemy_id += 1
    game._setup_physics_entity(enemy)
    game.enemies.append(enemy)
    game.god_spawned = True
    game.olympus_distortion_timer = 0.0
    game.olympus_distortion_type = ""


def exit_olympus_dimension(game):
    state = restore_main_dimension(game)
    if state is None:
        return
    game.olympus_world = None
    game.message = "Voce destronou o Deus. A jornada continua."
    for player in game.alive_players():
        player.pos = Vector2(getattr(player, "original_pos", player.pos))
        if player.body:
            player.body.position = player.pos.x, player.pos.y
