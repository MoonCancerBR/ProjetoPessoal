import argparse
import random
import sys
import time
from pathlib import Path


def _prepare_import_path():
    project_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_dir.parent))


def _make_rects(count):
    from Sobrevivencia.core.entities import RectBody

    rng = random.Random(42)
    rects = []
    for _ in range(count):
        rects.append(
            RectBody(
                rng.uniform(-1800, 1800),
                rng.uniform(-1800, 1800),
                rng.uniform(24, 128),
                rng.uniform(24, 128),
            )
        )
    return rects


def _make_points(count):
    rng = random.Random(91)
    return [(rng.uniform(-1900, 1900), rng.uniform(-1900, 1900), rng.uniform(6, 28)) for _ in range(count)]


def _bench_backend(name, backend, rects, points, iterations):
    from pygame.math import Vector2

    start = time.perf_counter()
    hits = 0
    checksum = 0.0
    for index in range(iterations):
        cx, cy, radius = points[index % len(points)]
        rect = rects[(index * 17) % len(rects)]
        if backend.circle_rect_overlap(cx, cy, radius, rect):
            hits += 1
        resolved = backend.resolve_circle(Vector2(cx, cy), radius, [rect], iterations=2)
        checksum += resolved.x * 0.001 + resolved.y * 0.0001
    elapsed = time.perf_counter() - start
    print(f"{name}: {iterations} ops em {elapsed:.4f}s | {iterations / elapsed:.0f} ops/s | hits={hits} | checksum={checksum:.2f}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark controlado dos backends de fisica.")
    parser.add_argument("--rects", type=int, default=600)
    parser.add_argument("--points", type=int, default=1000)
    parser.add_argument("--iterations", type=int, default=40000)
    args = parser.parse_args(argv)

    _prepare_import_path()

    from Sobrevivencia.core.physics import PymunkPhysicsBackend, SimplePhysicsBackend

    rects = _make_rects(args.rects)
    points = _make_points(args.points)

    _bench_backend("simple", SimplePhysicsBackend(), rects, points, args.iterations)
    try:
        pymunk_backend = PymunkPhysicsBackend()
    except RuntimeError as exc:
        print(f"pymunk: indisponivel ({exc})")
        return 0
    _bench_backend("pymunk", pymunk_backend, rects, points, args.iterations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
