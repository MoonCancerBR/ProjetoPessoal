from pathlib import Path

import pygame
import pygame.freetype

from .atlas import SpriteAtlas


class AssetRegistry:
    """Centralized cache for visual assets used by the presentation layer."""

    def __init__(self, project_root=None, ui_scale=1.0):
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parents[2]
        self.assets_dir = self.project_root / "assets"
        self.ui_scale = ui_scale
        self._images = {}
        self._scaled_images = {}
        self._atlases = {}
        self._fonts = {}

    @property
    def theme_path(self):
        return str(self.assets_dir / "theme.json")

    def font(self, name, point_size, bold=False, italic=False):
        pygame.freetype.init()
        scaled_size = max(1, int(point_size * self.ui_scale))
        key = (name, scaled_size, bool(bold), bool(italic))
        if key not in self._fonts:
            self._fonts[key] = pygame.freetype.SysFont(name, scaled_size, bold=bold, italic=italic)
        return self._fonts[key]

    def image(self, relative_path, alpha=True):
        key = (str(relative_path).replace("\\", "/"), bool(alpha))
        if key not in self._images:
            path = self.assets_dir / relative_path
            surface = pygame.image.load(str(path))
            try:
                surface = surface.convert_alpha() if alpha else surface.convert()
            except pygame.error:
                if alpha:
                    surface = surface.copy()
            self._images[key] = surface
        return self._images[key]

    def scaled_image(self, relative_path, size, alpha=True, smooth=True):
        size = (int(size[0]), int(size[1]))
        key = (str(relative_path).replace("\\", "/"), size, bool(alpha), bool(smooth))
        if key not in self._scaled_images:
            source = self.image(relative_path, alpha=alpha)
            scaler = pygame.transform.smoothscale if smooth else pygame.transform.scale
            self._scaled_images[key] = scaler(source, size)
        return self._scaled_images[key]

    def load_item_icons(self, keys, size=(32, 32)):
        icons = {}
        for key in keys:
            try:
                icons[key] = self.item_icon(key, size)
            except (FileNotFoundError, pygame.error):
                continue
        return icons

    def item_icon(self, key, size=(32, 32)):
        return self.scaled_image(Path("items") / f"{key}.png", size)

    def sprite_atlas(self, image_relative_path, metadata_relative_path):
        key = (
            str(image_relative_path).replace("\\", "/"),
            str(metadata_relative_path).replace("\\", "/"),
        )
        if key not in self._atlases:
            self._atlases[key] = SpriteAtlas.load(
                self.assets_dir / image_relative_path,
                self.assets_dir / metadata_relative_path,
            )
        return self._atlases[key]

    def character_atlas(self, character_key):
        base = Path("characters") / character_key
        return self.sprite_atlas(base / "atlas.png", base / "atlas.json")
