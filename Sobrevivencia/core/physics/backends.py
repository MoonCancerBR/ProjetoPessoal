import math

from pygame.math import Vector2


class SimplePhysicsBackend:
    """Pure Python collision backend used as the always-available fallback."""

    name = "simple"

    def circle_rect_overlap(self, cx, cy, radius, rect):
        closest_x = max(rect.left, min(cx, rect.right))
        closest_y = max(rect.top, min(cy, rect.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return dx * dx + dy * dy <= radius * radius

    def circle_rect_correction(self, pos, radius, rect):
        closest_x = max(rect.left, min(pos.x, rect.right))
        closest_y = max(rect.top, min(pos.y, rect.bottom))
        offset = Vector2(pos.x - closest_x, pos.y - closest_y)
        distance_sq = offset.length_squared()

        if distance_sq >= radius * radius:
            return Vector2(0, 0)
        if distance_sq > 0.0001:
            distance = math.sqrt(distance_sq)
            return offset * ((radius - distance + 0.05) / distance)

        distances = [
            (abs(pos.x - rect.left), Vector2(rect.left - radius - 0.05 - pos.x, 0)),
            (abs(rect.right - pos.x), Vector2(rect.right + radius + 0.05 - pos.x, 0)),
            (abs(pos.y - rect.top), Vector2(0, rect.top - radius - 0.05 - pos.y)),
            (abs(rect.bottom - pos.y), Vector2(0, rect.bottom + radius + 0.05 - pos.y)),
        ]
        return min(distances, key=lambda entry: entry[0])[1]

    def resolve_circle(self, pos, radius, rects, iterations=4):
        resolved = Vector2(pos)
        for _ in range(iterations):
            adjusted = False
            for rect in rects:
                correction = self.circle_rect_correction(resolved, radius, rect)
                if correction.length_squared() <= 0:
                    continue
                resolved += correction
                adjusted = True
            if not adjusted:
                break
        return resolved


class PymunkPhysicsBackend(SimplePhysicsBackend):
    """Optional pymunk-backed broadphase with the simple backend as exact fallback."""

    name = "pymunk"

    def __init__(self):
        try:
            import pymunk
        except ImportError as exc:
            raise RuntimeError("pymunk is not available") from exc
        self.pymunk = pymunk

    def circle_rect_overlap(self, cx, cy, radius, rect):
        circle_bb = self.pymunk.BB(cx - radius, cy - radius, cx + radius, cy + radius)
        rect_bb = self.pymunk.BB(rect.left, rect.top, rect.right, rect.bottom)
        if not circle_bb.intersects(rect_bb):
            return False
        return super().circle_rect_overlap(cx, cy, radius, rect)


def create_physics_backend(prefer_pymunk=False):
    if prefer_pymunk:
        try:
            return PymunkPhysicsBackend()
        except RuntimeError:
            pass
    return SimplePhysicsBackend()
