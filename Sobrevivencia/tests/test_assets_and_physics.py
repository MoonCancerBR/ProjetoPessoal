import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_PARENT))


def test_asset_registry_loads_existing_item_icons():
    import pygame

    from Sobrevivencia.presentation.rendering.assets import AssetRegistry

    pygame.init()
    pygame.display.set_mode((1, 1))
    registry = AssetRegistry()
    icons = registry.load_item_icons(["storm_core", "guardian_plate"], size=(24, 24))
    pygame.quit()

    assert set(icons) == {"storm_core", "guardian_plate"}
    assert all(surface.get_size() == (24, 24) for surface in icons.values())


def test_asset_registry_reuses_scaled_item_icon_cache():
    import pygame

    from Sobrevivencia.presentation.rendering.assets import AssetRegistry

    pygame.init()
    pygame.display.set_mode((1, 1))
    registry = AssetRegistry()
    first = registry.item_icon("storm_core", size=(28, 28))
    second = registry.item_icon("storm_core", size=(28, 28))
    pygame.quit()

    assert first is second


def test_asset_registry_loads_vanguard_character_atlas():
    import pygame

    from Sobrevivencia.presentation.rendering.assets import AssetRegistry

    pygame.init()
    pygame.display.set_mode((1, 1))
    registry = AssetRegistry()
    atlas = registry.character_atlas("vanguard")
    frame = atlas.frame("idle_0")
    pygame.quit()

    assert frame.get_size() == (64, 64)


def test_effect_surface_cache_reuses_glow_surfaces():
    import pygame

    from Sobrevivencia.presentation.effects.primitives import EffectSurfaceCache

    pygame.init()
    cache = EffectSurfaceCache()
    first = cache.soft_circle(12, (255, 255, 255), 80, 3)
    second = cache.soft_circle(12, (255, 255, 255), 80, 3)
    pygame.quit()

    assert first is second


def test_sprite_atlas_loads_named_frames(tmp_path):
    import json

    import pygame

    from Sobrevivencia.presentation.rendering.atlas import SpriteAtlas

    pygame.init()
    pygame.display.set_mode((1, 1))

    image_path = tmp_path / "atlas.png"
    metadata_path = tmp_path / "atlas.json"
    sheet = pygame.Surface((8, 4), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))
    pygame.draw.rect(sheet, (255, 0, 0, 255), (0, 0, 4, 4))
    pygame.draw.rect(sheet, (0, 255, 0, 255), (4, 0, 4, 4))
    pygame.image.save(sheet, image_path)
    metadata_path.write_text(
        json.dumps(
            {
                "frames": {
                    "idle_0": {"frame": {"x": 0, "y": 0, "w": 4, "h": 4}, "duration": 0.12},
                    "idle_1": {"frame": {"x": 4, "y": 0, "w": 4, "h": 4}, "duration": 0.12},
                }
            }
        ),
        encoding="utf-8",
    )

    atlas = SpriteAtlas.load(image_path, metadata_path)
    frame = atlas.frame("idle_0")
    animation = atlas.animation("idle_")
    pygame.quit()

    assert frame.get_size() == (4, 4)
    assert len(animation) == 2


def test_simple_physics_resolves_circle_outside_rect():
    from pygame.math import Vector2

    from Sobrevivencia.core.entities import RectBody
    from Sobrevivencia.core.physics import SimplePhysicsBackend

    backend = SimplePhysicsBackend()
    rect = RectBody(0, 0, 20, 20)
    resolved = backend.resolve_circle(Vector2(10, 10), 6, [rect])

    assert not backend.circle_rect_overlap(resolved.x, resolved.y, 6, rect)


def test_pymunk_backend_matches_simple_overlap_when_available():
    from Sobrevivencia.core.entities import RectBody
    from Sobrevivencia.core.physics import PymunkPhysicsBackend, SimplePhysicsBackend

    rect = RectBody(0, 0, 20, 20)
    simple = SimplePhysicsBackend()
    try:
        pymunk_backend = PymunkPhysicsBackend()
    except RuntimeError:
        return

    assert pymunk_backend.circle_rect_overlap(10, 10, 6, rect) == simple.circle_rect_overlap(10, 10, 6, rect)
    assert pymunk_backend.circle_rect_overlap(80, 80, 6, rect) == simple.circle_rect_overlap(80, 80, 6, rect)


def test_physics_factory_keeps_safe_fallback():
    from Sobrevivencia.core.physics import create_physics_backend

    backend = create_physics_backend(prefer_pymunk=True)

    assert backend.name in {"simple", "pymunk"}
