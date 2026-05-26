from pygame.math import Vector2

if __package__:
    from ....data.constants import CHALICE_COMBO_TARGET, CHALICE_FRAGMENTS, CHALICE_KILL_TARGET, CHALICE_TIME_TARGET
    from .. import system as omni_kernel
else:
    from Sobrevivencia.data.constants import CHALICE_COMBO_TARGET, CHALICE_FRAGMENTS, CHALICE_KILL_TARGET, CHALICE_TIME_TARGET
    from Sobrevivencia.core.omni_kernel import system as omni_kernel


def grant_fragment(game, key, pos=None):
    if key not in getattr(game, "chalice_fragments", {}) or game.chalice_fragments[key]:
        return False
    game.chalice_fragments[key] = True
    entry = next((item for item in CHALICE_FRAGMENTS if item["key"] == key), None)
    name = entry["name"] if entry else key
    pos = Vector2(pos if pos is not None else game.player.pos)
    game.emit_particles(pos, count=46, color="#FACC15", speed=220, lifetime=0.55, size=5)
    game.screen_shake = max(game.screen_shake, 9.0)
    game.message = f"Fragmento do Calice coletado: {name}."
    if all(game.chalice_fragments.values()) and not game.omni_kernel_active:
        game._activate_omni_kernel(pos)
    return True


def update_progress(game, dt):
    if not game.chalice_fragments.get("world_hidden", False):
        if game.player.pos.distance_squared_to(game.chalice_hidden_pos) < 90 * 90:
            game.spawn_drop("chalice", game.chalice_hidden_pos, "world_hidden")
            game.chalice_hidden_pos = Vector2(999999, 999999)
    total_kills = sum(player.kills for player in game.players)
    if total_kills >= CHALICE_KILL_TARGET or getattr(game, "combo_count", 0) >= CHALICE_COMBO_TARGET:
        game.grant_chalice_fragment("combat_mark", game.player.pos)
    if game.time_alive >= CHALICE_TIME_TARGET:
        game.grant_chalice_fragment("time_mark", game.player.pos)
    omni_kernel.update_runtime(game, dt)

