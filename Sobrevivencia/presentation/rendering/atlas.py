import json
from dataclasses import dataclass
from pathlib import Path

import pygame


@dataclass(frozen=True)
class AtlasFrame:
    name: str
    rect: pygame.Rect
    duration: float = 0.1


class SpriteAtlas:
    """Loads PNG spritesheets with JSON frame metadata."""

    def __init__(self, image, frames):
        self.image = image
        self.frames = dict(frames)
        self._frame_cache = {}

    @classmethod
    def load(cls, image_path, metadata_path, alpha=True):
        image_path = Path(image_path)
        metadata_path = Path(metadata_path)
        image = pygame.image.load(str(image_path))
        try:
            image = image.convert_alpha() if alpha else image.convert()
        except pygame.error:
            if alpha:
                image = image.copy()

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        frames = {}
        for name, frame_data in _iter_frame_items(metadata):
            rect_data = frame_data.get("frame", frame_data)
            rect = pygame.Rect(
                int(rect_data["x"]),
                int(rect_data["y"]),
                int(rect_data["w"]),
                int(rect_data["h"]),
            )
            duration = float(frame_data.get("duration", metadata.get("default_duration", 0.1)))
            frames[name] = AtlasFrame(name=name, rect=rect, duration=duration)

        return cls(image, frames)

    def frame(self, name):
        if name in self._frame_cache:
            return self._frame_cache[name]
        frame = self.frames[name]
        surface = pygame.Surface(frame.rect.size, pygame.SRCALPHA)
        surface.blit(self.image, (0, 0), frame.rect)
        self._frame_cache[name] = surface
        return surface

    def animation(self, prefix):
        matching = [(name, frame) for name, frame in self.frames.items() if name.startswith(prefix)]
        return [self.frame(name) for name, _frame in sorted(matching)]


def _iter_frame_items(metadata):
    frames = metadata.get("frames", metadata)
    if isinstance(frames, list):
        for entry in frames:
            yield entry["name"], entry
    else:
        yield from frames.items()
