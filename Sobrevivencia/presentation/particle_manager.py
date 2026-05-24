import random
import math
import pygame
from pygame.math import Vector2

try:
    import numpy as np
except ImportError:
    np = None


class ParticleManager:
    def __init__(self):
        if np is None:
            self.particles = []
            self.count = 0
            return
        self.count = 0
        self.pos = np.zeros((0, 2), dtype=np.float32)
        self.velocity = np.zeros((0, 2), dtype=np.float32)
        self.colors = np.zeros((0, 3), dtype=np.uint8)
        self.lifetime = np.zeros(0, dtype=np.float32)
        self.max_lifetime = np.zeros(0, dtype=np.float32)
        self.size = np.zeros(0, dtype=np.float32)

    def emit(self, pos, count=10, color="#FFFFFF", speed=50, lifetime=0.5, size=4):
        if np is None:
            color_value = pygame.Color(color)
            origin = Vector2(pos)
            for _ in range(count):
                angle = random.uniform(0, 2 * 3.141592653589793)
                direction = Vector2(math.cos(angle), math.sin(angle))
                particle_lifetime = random.uniform(lifetime * 0.5, lifetime * 1.2)
                self.particles.append({
                    "pos": Vector2(origin),
                    "velocity": direction * random.uniform(speed * 0.5, speed * 1.5),
                    "color": color_value,
                    "lifetime": particle_lifetime,
                    "max_lifetime": max(0.001, particle_lifetime),
                    "size": random.uniform(size * 0.5, size * 1.5),
                })
            self.count = len(self.particles)
            return

        new_count = self.count + count
        
        # New arrays
        new_pos = np.full((count, 2), pos, dtype=np.float32)
        
        angles = np.random.uniform(0, 2 * np.pi, count)
        directions = np.column_stack((np.cos(angles), np.sin(angles)))
        speeds = np.random.uniform(speed * 0.5, speed * 1.5, count)
        new_velocity = directions * speeds[:, np.newaxis]
        
        c = pygame.Color(color)
        new_colors = np.full((count, 3), [c.r, c.g, c.b], dtype=np.uint8)
        
        new_lifetime = np.random.uniform(lifetime * 0.5, lifetime * 1.2, count)
        new_max_lifetime = np.full(count, lifetime, dtype=np.float32)
        new_size = np.random.uniform(size * 0.5, size * 1.5, count)
        
        # Append to existing
        self.pos = np.vstack([self.pos, new_pos])
        self.velocity = np.vstack([self.velocity, new_velocity])
        self.colors = np.vstack([self.colors, new_colors])
        self.lifetime = np.concatenate([self.lifetime, new_lifetime])
        self.max_lifetime = np.concatenate([self.max_lifetime, new_max_lifetime])
        self.size = np.concatenate([self.size, new_size])
        
        self.count = new_count

    def update(self, dt):
        if self.count == 0:
            return

        if np is None:
            alive = []
            drag = max(0.0, 1.0 - 2.0 * dt)
            for particle in self.particles:
                particle["lifetime"] -= dt
                if particle["lifetime"] <= 0:
                    continue
                particle["pos"] += particle["velocity"] * dt
                particle["velocity"] *= drag
                alive.append(particle)
            self.particles = alive
            self.count = len(alive)
            return

        self.lifetime -= dt
        
        # Filter alive
        mask = self.lifetime > 0
        if not np.any(mask):
            self.__init__()
            return

        self.pos = self.pos[mask]
        self.velocity = self.velocity[mask]
        self.colors = self.colors[mask]
        self.lifetime = self.lifetime[mask]
        self.max_lifetime = self.max_lifetime[mask]
        self.size = self.size[mask]
        self.count = len(self.lifetime)

        # Physics
        self.pos += self.velocity * dt
        # Drag
        self.velocity *= max(0.0, 1.0 - 2.0 * dt)

    def render(self, surface, camera_offset):
        if self.count == 0:
            return

        if np is None:
            sw, sh = surface.get_size()
            for particle in self.particles:
                progress = max(0.0, particle["lifetime"] / particle["max_lifetime"])
                size = max(1, int(particle["size"] * progress))
                x = int(particle["pos"].x - camera_offset.x - size / 2)
                y = int(particle["pos"].y - camera_offset.y - size / 2)
                if -size <= x <= sw + size and -size <= y <= sh + size:
                    pygame.draw.circle(surface, particle["color"], (x + size // 2, y + size // 2), max(1, size // 2))
            return

        # Prepare screen positions
        render_pos = self.pos - [camera_offset.x, camera_offset.y]
        
        # Progress for size
        progress = self.lifetime / self.max_lifetime
        current_sizes = (self.size * progress).astype(np.int32)
        np.clip(current_sizes, 1, 100, out=current_sizes)

        # Frustum culling (basic)
        sw, sh = surface.get_size()
        on_screen = (render_pos[:, 0] > -current_sizes) & (render_pos[:, 0] < sw + current_sizes) & \
                    (render_pos[:, 1] > -current_sizes) & (render_pos[:, 1] < sh + current_sizes)
        
        # Use localized variables for drawing
        it = np.where(on_screen)[0]
        for i in it:
            sz = current_sizes[i]
            x = int(render_pos[i, 0] - sz / 2)
            y = int(render_pos[i, 1] - sz / 2)
            pygame.draw.circle(surface, self.colors[i], (x + sz // 2, y + sz // 2), max(1, sz // 2))
