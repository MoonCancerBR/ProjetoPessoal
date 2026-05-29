import math
import random

from pygame.math import Vector2

if __package__:
    from ..config.runtime import njit_or_python as njit, optional_import
    from ..data.constants import CHUNK_SIZE, ICE_SPEED_MULTIPLIER, TERRAIN_TYPES, VIEW_PADDING, WORLD_TILE_SIZE
    from .entities import Destructible, Hazard, RectBody, StaticLight
    from .physics import SimplePhysicsBackend
else:
    from Sobrevivencia.config.runtime import njit_or_python as njit, optional_import
    from Sobrevivencia.data.constants import CHUNK_SIZE, ICE_SPEED_MULTIPLIER, TERRAIN_TYPES, VIEW_PADDING, WORLD_TILE_SIZE
    from Sobrevivencia.core.entities import Destructible, Hazard, RectBody, StaticLight
    from Sobrevivencia.core.physics import SimplePhysicsBackend

pytmx = optional_import("pytmx")


@njit
def stable_hash(x, y, salt=0):
    value = (x * 374761393 + y * 668265263 + salt * 362437) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    return (value ^ (value >> 16)) & 0xFFFFFFFF


@njit
def unit_hash(x, y, salt=0):
    return stable_hash(x, y, salt) / 0xFFFFFFFF


@njit
def _circle_rect_overlap_math(cx, cy, radius, rect_left, rect_top, rect_right, rect_bottom):
    nearest_x = max(rect_left, min(cx, rect_right))
    nearest_y = max(rect_top, min(cy, rect_bottom))
    dx = cx - nearest_x
    dy = cy - nearest_y
    return dx * dx + dy * dy <= radius * radius


def circle_rect_overlap(cx, cy, radius, rect):
    return _circle_rect_overlap_math(cx, cy, radius, rect.left, rect.top, rect.right, rect.bottom)


class World:
    def __init__(self, physics_backend=None):
        self.chunks = {}
        self.tmx_data = None
        self.use_tmx = False
        self.physics = physics_backend or SimplePhysicsBackend()

    def load_tmx(self, filename):
        if pytmx is None:
            return False
        try:
            self.tmx_data = pytmx.load_pygame(filename, pixelalpha=True)
            self.use_tmx = True
            return True
        except Exception as e:
            print(f"Erro ao carregar TMX: {e}")
            return False

    def chunk_coords(self, x, y):
        return math.floor(x / CHUNK_SIZE), math.floor(y / CHUNK_SIZE)

    def ensure_chunk(self, cx, cy, safe_center=None, safe_radius=0):
        key = (cx, cy)
        if key not in self.chunks:
            self.chunks[key] = self._generate_chunk(cx, cy)
            if safe_center is not None and safe_radius > 0:
                self._clear_chunk_safe_area(self.chunks[key], safe_center, safe_radius)
        return self.chunks[key]

    def ensure_area(self, center, radius=2):
        cx, cy = self.chunk_coords(center.x, center.y)
        for oy in range(-radius, radius + 1):
            for ox in range(-radius, radius + 1):
                self.ensure_chunk(cx + ox, cy + oy, safe_center=center, safe_radius=220)

    def _clear_chunk_safe_area(self, chunk, center, radius):
        chunk["obstacles"] = [
            rect for rect in chunk["obstacles"]
            if not circle_rect_overlap(center.x, center.y, radius, rect)
        ]
        chunk["destructibles"] = [
            item for item in chunk["destructibles"]
            if not circle_rect_overlap(center.x, center.y, radius, item.rect)
        ]
        chunk["hazards"] = [
            hazard for hazard in chunk["hazards"]
            if not circle_rect_overlap(center.x, center.y, radius, hazard.rect)
        ]

    def _generate_chunk(self, cx, cy):
        rng = random.Random(stable_hash(cx, cy, 91))
        base_x = cx * CHUNK_SIZE
        base_y = cy * CHUNK_SIZE
        obstacles = []
        destructibles = []
        hazards = []
        static_lights = []

        obstacle_count = 3 + rng.randint(0, 4)
        for index in range(obstacle_count):
            wide = rng.random() < 0.58
            width = rng.randint(96, 210) if wide else rng.randint(44, 86)
            height = rng.randint(42, 90) if wide else rng.randint(90, 190)
            rect = RectBody(
                base_x + rng.randint(44, CHUNK_SIZE - width - 44),
                base_y + rng.randint(44, CHUNK_SIZE - height - 44),
                width,
                height,
            )
            if rect.center.length() < 330:
                continue
            if any(rect.intersects(existing, padding=32) for existing in obstacles):
                continue
            obstacles.append(rect)

        destructible_count = 4 + rng.randint(0, 5)
        for index in range(destructible_count):
            size = rng.randint(28, 42)
            rect = RectBody(
                base_x + rng.randint(35, CHUNK_SIZE - size - 35),
                base_y + rng.randint(35, CHUNK_SIZE - size - 35),
                size,
                size,
            )
            if rect.center.length() < 250:
                continue
            if any(rect.intersects(obstacle, padding=20) for obstacle in obstacles):
                continue
            roll = rng.random()
            if roll < 0.10:
                kind = "special"
            elif roll < 0.28:
                kind = "cache"
            else:
                kind = "crate"
            hp = 44 if kind == "special" else 35 if kind == "cache" else 24
            destructibles.append(
                Destructible(
                    id=f"{cx}:{cy}:{index}",
                    rect=rect,
                    hp=hp,
                    max_hp=hp,
                    kind=kind,
                    chunk=(cx, cy),
                )
            )

        hazard_count = 2 + rng.randint(0, 3)
        for index in range(hazard_count):
            roll = rng.random()
            if roll < 0.34:
                kind = "mine"
                width = height = rng.randint(28, 36)
            elif roll < 0.66:
                kind = "fire"
                width = rng.randint(92, 148)
                height = rng.randint(72, 118)
            else:
                kind = "ice"
                width = rng.randint(116, 178)
                height = rng.randint(82, 138)

            rect = RectBody(
                base_x + rng.randint(40, CHUNK_SIZE - width - 40),
                base_y + rng.randint(40, CHUNK_SIZE - height - 40),
                width,
                height,
            )
            if rect.center.length() < 300:
                continue
            if any(rect.intersects(obstacle, padding=18) for obstacle in obstacles):
                continue
            if any(rect.intersects(item.rect, padding=14) for item in destructibles):
                continue
            if any(rect.intersects(hazard.rect, padding=24) for hazard in hazards):
                continue
            hazards.append(Hazard(id=f"{cx}:{cy}:h{index}", rect=rect, kind=kind, chunk=(cx, cy)))

        if rng.random() < 0.62:
            for index in range(1 + (1 if rng.random() < 0.22 else 0)):
                radius = rng.randint(125, 190)
                pos = Vector2(
                    base_x + rng.randint(70, CHUNK_SIZE - 70),
                    base_y + rng.randint(70, CHUNK_SIZE - 70),
                )
                if pos.length() < 360:
                    continue
                if any(circle_rect_overlap(pos.x, pos.y, 30, obstacle) for obstacle in obstacles):
                    continue
                static_lights.append(
                    StaticLight(
                        id=f"{cx}:{cy}:l{index}",
                        pos=pos,
                        kind="crystal" if rng.random() < 0.5 else "lamp",
                        radius=radius,
                        chunk=(cx, cy),
                    )
                )

        return {"obstacles": obstacles, "destructibles": destructibles, "hazards": hazards, "static_lights": static_lights}

    def terrain_at(self, x, y):
        tile_x = math.floor(x / WORLD_TILE_SIZE)
        tile_y = math.floor(y / WORLD_TILE_SIZE)
        region_x = math.floor(tile_x / 4)
        region_y = math.floor(tile_y / 4)
        base = unit_hash(region_x, region_y, 11)
        variation = unit_hash(tile_x, tile_y, 23)
        value = (base * 0.78) + (variation * 0.22)

        if value < 0.15:
            return "sand"
        if value < 0.27:
            return "mud"
        if value > 0.86:
            return "stone"
        return "grass"

    def speed_multiplier_at(self, x, y):
        return TERRAIN_TYPES[self.terrain_at(x, y)]["speed"] * self.hazard_speed_multiplier_at(x, y)

    def hazard_speed_multiplier_at(self, x, y):
        multiplier = 1.0
        for hazard in self.nearby_hazards(x, y, 8):
            if hazard.kind == "ice" and circle_rect_overlap(x, y, 6, hazard.rect):
                multiplier = max(multiplier, ICE_SPEED_MULTIPLIER)
        return multiplier

    def iter_visible_terrain(self, camera_x, camera_y, width, height):
        start_x = math.floor((camera_x - VIEW_PADDING) / WORLD_TILE_SIZE)
        end_x = math.ceil((camera_x + width + VIEW_PADDING) / WORLD_TILE_SIZE)
        start_y = math.floor((camera_y - VIEW_PADDING) / WORLD_TILE_SIZE)
        end_y = math.ceil((camera_y + height + VIEW_PADDING) / WORLD_TILE_SIZE)

        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                kind = self.terrain_at(tx * WORLD_TILE_SIZE, ty * WORLD_TILE_SIZE)
                yield tx * WORLD_TILE_SIZE, ty * WORLD_TILE_SIZE, WORLD_TILE_SIZE, kind, unit_hash(tx, ty, 41)

    def _chunks_in_rect(self, left, top, right, bottom):
        start_cx = math.floor(left / CHUNK_SIZE)
        end_cx = math.floor(right / CHUNK_SIZE)
        start_cy = math.floor(top / CHUNK_SIZE)
        end_cy = math.floor(bottom / CHUNK_SIZE)
        for cy in range(start_cy, end_cy + 1):
            for cx in range(start_cx, end_cx + 1):
                yield self.ensure_chunk(cx, cy)

    def iter_visible_obstacles(self, camera_x, camera_y, width, height):
        left = camera_x - VIEW_PADDING
        top = camera_y - VIEW_PADDING
        right = camera_x + width + VIEW_PADDING
        bottom = camera_y + height + VIEW_PADDING
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for rect in chunk["obstacles"]:
                if not (rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom):
                    yield rect

    def iter_visible_destructibles(self, camera_x, camera_y, width, height):
        left = camera_x - VIEW_PADDING
        top = camera_y - VIEW_PADDING
        right = camera_x + width + VIEW_PADDING
        bottom = camera_y + height + VIEW_PADDING
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for item in chunk["destructibles"]:
                rect = item.rect
                if not (rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom):
                    yield item

    def iter_visible_hazards(self, camera_x, camera_y, width, height):
        left = camera_x - VIEW_PADDING
        top = camera_y - VIEW_PADDING
        right = camera_x + width + VIEW_PADDING
        bottom = camera_y + height + VIEW_PADDING
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for hazard in chunk["hazards"]:
                rect = hazard.rect
                if not (rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom):
                    yield hazard

    def iter_visible_static_lights(self, camera_x, camera_y, width, height):
        left = camera_x - VIEW_PADDING
        top = camera_y - VIEW_PADDING
        right = camera_x + width + VIEW_PADDING
        bottom = camera_y + height + VIEW_PADDING
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for light in chunk.get("static_lights", []):
                if not (light.pos.x + light.radius < left or light.pos.x - light.radius > right or light.pos.y + light.radius < top or light.pos.y - light.radius > bottom):
                    yield light

    def nearby_solid_rects(self, x, y, radius, include_destructibles=True):
        left = x - radius - 96
        top = y - radius - 96
        right = x + radius + 96
        bottom = y + radius + 96
        rects = []
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            rects.extend(chunk["obstacles"])
            if include_destructibles:
                rects.extend(item.rect for item in chunk["destructibles"])
        return rects

    def nearby_destructibles(self, x, y, radius):
        left = x - radius
        top = y - radius
        right = x + radius
        bottom = y + radius
        items = []
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for item in chunk["destructibles"]:
                rect = item.rect
                if not (rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom):
                    items.append(item)
        return items

    def nearby_hazards(self, x, y, radius):
        left = x - radius
        top = y - radius
        right = x + radius
        bottom = y + radius
        hazards = []
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for hazard in chunk["hazards"]:
                rect = hazard.rect
                if not (rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom):
                    hazards.append(hazard)
        return hazards

    def move_circle(self, pos, radius, delta, include_destructibles=True):
        new_pos = Vector2(pos)
        if delta.length_squared() <= 0:
            return self._resolve_circle_collisions(new_pos, radius, include_destructibles)

        max_step = max(6.0, radius * 0.45)
        steps = max(1, math.ceil(delta.length() / max_step))
        step = delta / steps
        for _ in range(steps):
            new_pos += step
            new_pos = self._resolve_circle_collisions(new_pos, radius, include_destructibles)
        return new_pos

    def _resolve_circle_collisions(self, pos, radius, include_destructibles=True):
        resolved = Vector2(pos)
        for _ in range(4):
            adjusted = False
            for rect in self.nearby_solid_rects(resolved.x, resolved.y, radius, include_destructibles):
                correction = self._circle_rect_correction(resolved, radius, rect)
                if correction.length_squared() <= 0:
                    continue
                resolved += correction
                adjusted = True
            if not adjusted:
                break
        return resolved

    def _circle_rect_correction(self, pos, radius, rect):
        return self.physics.circle_rect_correction(pos, radius, rect)

    def circle_hits_wall(self, pos, radius, include_destructibles=True):
        return any(
            self.physics.circle_rect_overlap(pos.x, pos.y, radius, rect)
            for rect in self.nearby_solid_rects(pos.x, pos.y, radius, include_destructibles)
        )

    def remove_destructible(self, item):
        chunk = self.ensure_chunk(*item.chunk)
        chunk["destructibles"] = [entry for entry in chunk["destructibles"] if entry.id != item.id]

    def remove_hazard(self, hazard):
        chunk = self.ensure_chunk(*hazard.chunk)
        chunk["hazards"] = [entry for entry in chunk["hazards"] if entry.id != hazard.id]
