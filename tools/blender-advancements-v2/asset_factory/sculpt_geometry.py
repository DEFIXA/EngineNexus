"""Deterministic real-geometry surface relief, not textures or normal maps."""
import math
from mathutils import Vector, noise


def _smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / max(1e-8, b - a)))
    return t * t * (3.0 - 2.0 * t)


def _gauss(distance, radius):
    return math.exp(-((distance / max(radius, 1e-5)) ** 2))


def sculpt_surface(obj, category, seed, *, full_creature=False):
    """Displace existing mesh vertices; no claim of hero sculpt fidelity."""
    if category not in {"creature", "animal", "tree", "root", "foliage", "rock", "terrain"}:
        return {"enabled": False, "vertices": 0}
    mesh = obj.data
    count = 0
    for vert in mesh.vertices:
        p = vert.co.copy()
        normal = vert.normal.copy()
        if normal.length_squared < 0.1:
            continue
        if category in {"creature", "animal"}:
            coarse = noise.noise(p * 5.0 + Vector((seed * 0.1, 0, 0)))
            fine = noise.noise(p * 13.0)
            micro = noise.noise(p * 24.0)
            relief = 0.024 * coarse + 0.012 * fine + 0.004 * micro
            cells = math.sin(16.0 * p.x + 1.9 * math.sin(4.5 * p.z))
            cells *= math.sin(18.0 * p.z + 2.1 * math.sin(4.0 * p.x))
            relief += 0.016 * max(0.0, cells) ** 3
            if full_creature:
                wing = _smooth(1.35, 2.20, abs(p.y)) * _smooth(2.4, 3.1, p.z)
                relief *= 1.0 - 0.90 * wing
                if p.x > 2.85:
                    for side in (-1, 1):
                        eye = Vector((3.44, side * 0.33, 3.26))
                        d = (p - eye).length
                        relief += 0.050 * _gauss(d - 0.19, 0.075)
                        relief -= 0.068 * _gauss(d, 0.10)
                        nostril = Vector((4.06, side * 0.17, 3.06))
                        relief -= 0.032 * _gauss((p - nostril).length, 0.085)
                    if 3.20 < p.x < 4.25:
                        relief -= 0.024 * _gauss(p.z - 2.87, 0.045)
            elif 1.45 < p.z < 2.8:
                relief += 0.024 * math.sin(12 * p.z + 2 * p.x)
        elif category in {"tree", "root", "foliage"}:
            grain = math.sin(23.0 * p.x + 17.0 * p.y + 1.2 * math.sin(4 * p.z))
            relief = 0.022 * grain + 0.024 * noise.noise(p * 7.5)
            relief += 0.009 * noise.noise(p * 19.0)
        elif category == "rock":
            relief = 0.046 * noise.noise(p * 4.0)
            relief += 0.019 * noise.noise(p * 11.0)
        else:
            relief = 0.020 * noise.noise(p * 3.0)
            relief += 0.008 * noise.noise(p * 9.0)
        vert.co = p + normal * relief
        count += 1
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = category != "rock"
    return {"enabled": True, "vertices": count, "mode": "real_vertex_displacement"}
