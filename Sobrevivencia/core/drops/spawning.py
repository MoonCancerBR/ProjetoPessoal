from pygame.math import Vector2

if __package__:
    from ..entities import Drop
else:
    from Sobrevivencia.core.entities import Drop


DROP_RADII = {
    "xp": 7,
    "ammo": 8,
    "heal": 10,
    "shield": 12,
    "item_box": 13,
    "stamp": 10,
    "portal": 24,
    "exit_portal": 24,
    "chalice": 15,
}


def spawn_drop(game, kind, pos, value=1):
    radius = DROP_RADII.get(kind, 8)
    ttl = 45.0 if kind in ("portal", "exit_portal") else 18.0
    if kind == "chalice":
        ttl = 9999.0
    game.drops.append(Drop(pos=Vector2(pos), kind=kind, value=value, radius=radius, ttl=ttl))

