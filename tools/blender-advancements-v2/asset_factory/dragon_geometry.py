"""Anatomy-first static dragon blockout geometry.

No texture, rig, sculpt-quality or reference-match claims. Uses overlapping
metaball masses plus solid membranes and spikes. The Blender worker fuses the
candidate with voxel remesh and checks for disconnected islands.
"""
import bpy
import math
import random
from mathutils import Vector


def _v(point):
    return Vector(point)


def _blob_chain(blobs, a, b, ra, rb, *, spacing=0.17):
    start, end = _v(a), _v(b)
    length = (end - start).length
    steps = max(1, math.ceil(length / spacing))
    for j in range(steps + 1):
        t = j / steps
        p = start.lerp(end, t)
        radius = ra * (1 - t) + rb * t
        blobs.append((tuple(p), radius))


def _metas(name, blobs, *, resolution=0.10):
    mb = bpy.data.metaballs.new(name + "_Volumes")
    mb.resolution = resolution
    mb.render_resolution = resolution
    mb.threshold = 0.6
    ob = bpy.data.objects.new(name, mb)
    bpy.context.collection.objects.link(ob)
    for point, radius in blobs:
        el = mb.elements.new(type="BALL")
        el.co = point
        el.radius = radius
        el.stiffness = 2.0
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target="MESH")
    return bpy.context.view_layer.objects.active


def _spike(name, base, tip, radius=0.10, sides=12):
    direction = _v(tip) - _v(base)
    length = direction.length
    if length < 0.001:
        return None
    mid = (_v(base) + _v(tip)) * 0.5
    bpy.ops.mesh.primitive_cone_add(
        vertices=sides, radius1=radius, radius2=0.001,
        depth=length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def _leg_blobs(blobs, hip, side, *, hind=False, scale=1.0):
    x, y, z = hip
    if hind:
        points = [
            (x, y, z), (x + 0.40, y + side * 0.10, z - 0.52),
            (x + 0.52, y + side * 0.14, z - 1.0),
            (x - 0.05, y + side * 0.18, z - 1.42),
            (x - 0.16, y + side * 0.20, 0.43),
            (x + 0.18, y + side * 0.20, 0.23),
        ]
        radii = [0.46, 0.51, 0.35, 0.26, 0.24, 0.34]
    else:
        points = [
            (x, y, z), (x + 0.22, y + side * 0.07, z - 0.45),
            (x + 0.42, y + side * 0.10, z - 1.05),
            (x + 0.10, y + side * 0.10, 0.46),
            (x + 0.30, y + side * 0.12, 0.21),
        ]
        radii = [0.36, 0.32, 0.23, 0.23, 0.33]
    for i in range(len(points) - 1):
        _blob_chain(blobs, points[i], points[i + 1],
                    radii[i] * scale, radii[i + 1] * scale)
    palm = _v(points[-1])
    toes = []
    for i in range(4):
        lateral = (i - 1.5) * 0.21 * scale
        a = palm + Vector((0.08, lateral, -0.03))
        b = palm + Vector((0.48, lateral * 1.35, -0.06))
        c = palm + Vector((0.43, lateral * 1.35, -0.06))
        _blob_chain(blobs, a, b, 0.19 * scale, 0.14 * scale, spacing=0.09)
        toes.append((tuple(c), tuple(c + Vector((0.28, lateral * 0.12, -0.045)))))
    return toes


def make_leg(seed):
    """One complete connected anatomical hind-leg *blockout*."""
    blobs = []
    toes = _leg_blobs(blobs, (0, 0, 3.0), 1, hind=True)
    # Broad thigh/hip muscle and tapering Achilles tendon.
    blobs += [((0.03, 0, 2.85), 0.58),
              ((0.38, -0.05, 2.48), 0.47),
              ((-0.10, 0, 0.67), 0.22)]
    parts = [_metas("HindLeg_AnatomicalMass", blobs, resolution=0.075)]
    for i, (base, tip) in enumerate(toes):
        parts.append(_spike("Claw_%d" % i, base, tip, radius=0.11))
    # Plates grow out of the skin; no isolated floating decorations.
    rng = random.Random(seed)
    for i in range(22):
        t = i / 21
        z = 0.7 + t * 1.7
        if z < 1.4:
            x = -0.13 + 0.13 * (z - 0.7)
        elif z < 2.1:
            x = -0.04 + 0.74 * (z - 1.4)
        else:
            x = 0.48 - 0.28 * (z - 2.1)
        # Bury every scute root inside the actual anatomical mass.
        base = (x, 0.0, z)
        tip = (x - 0.10 + rng.uniform(-0.04, 0.04),
               0.27, z + 0.12)
        parts.append(_spike("LimbScute_%02d" % i, base, tip, 0.08))
    # Staggered armor plates embedded through thigh, hock and shin.
    for side in (-1, 1):
        for row in range(20):
            z = 0.75 + row * 0.105
            if z < 1.4:
                x, reach = -0.13 + 0.13 * (z - 0.7), 0.23
            elif z < 2.1:
                x, reach = -0.04 + 0.74 * (z - 1.4), 0.33
            else:
                x, reach = 0.48 - 0.28 * (z - 2.1), 0.46
            for band in range(3):
                offset = (band - 1) * 0.15
                parts.append(_spike(
                    "HindPlate_%s_%02d_%d" % (side, row, band),
                    (x, side * 0.06, z + offset * 0.25),
                    (x + reach * (0.7 + 0.1 * band),
                     side * (reach + 0.10 * band),
                     z + 0.10 + offset * 0.3),
                    radius=0.072 + 0.012 * band, sides=9))
    return [p for p in parts if p is not None]


def _wing_membrane(name, root, elbow, wrist, fingers, side):
    """Cambered subdivided scalloped wing, not a flat polygon fan."""
    root, elbow, wrist = map(_v, (root, elbow, wrist))
    fingers = [_v(p) for p in fingers]
    border = [elbow, wrist, fingers[0]]
    for left, right in zip(fingers, fingers[1:]):
        notch = left.lerp(right, 0.5).lerp(wrist, 0.18)
        notch.z -= 0.20
        border.extend([notch, right])
    border.append(root + Vector((-1.35, -side * 0.30, -0.65)))
    vertices, faces = [], []
    n = 9
    for panel, (left, right) in enumerate(zip(border, border[1:])):
        indices = {}
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                p = root * (1 - u - v) + left * u + right * v
                fold = math.sin(math.pi * u) * math.sin(math.pi * v)
                p.z += (0.15 + 0.045 * (panel % 3)) * fold
                p.x += 0.08 * fold
                indices[(i, j)] = len(vertices)
                vertices.append(tuple(p))
        for i in range(n):
            for j in range(n - i):
                faces.append((indices[(i, j)], indices[(i + 1, j)],
                              indices[(i, j + 1)]))
                if j < n - i - 1:
                    faces.append((indices[(i + 1, j)],
                                  indices[(i + 1, j + 1)],
                                  indices[(i, j + 1)]))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    solid = ob.modifiers.new("MembraneVolume", "SOLIDIFY")
    solid.thickness = 0.14
    bpy.ops.object.modifier_apply(modifier=solid.name)
    for face in ob.data.polygons:
        face.use_smooth = True
    return ob


def make_full_dragon(seed):
    """Quadruped dragon with complete torso, four feet, head, tail and two wings."""
    rng = random.Random(seed)
    blobs = []
    # Torso: barrel, pelvis, chest, arched neck and skull.
    for x, r, z in [
        (-1.8, 0.72, 2.35), (-1.3, 0.91, 2.35),
        (-0.7, 0.99, 2.35), (0.0, 0.93, 2.35),
        (0.65, 0.85, 2.43), (1.18, 0.69, 2.53)]:
        blobs.append(((x, 0, z), r))
    _blob_chain(blobs, (1.0, 0, 2.55), (2.40, 0, 2.98), 0.62, 0.38)
    _blob_chain(blobs, (2.40, 0, 2.98), (3.18, 0, 3.12), 0.42, 0.45)
    _blob_chain(blobs, (3.10, 0, 3.13), (4.25, 0, 3.05), 0.37, 0.22)
    _blob_chain(blobs, (3.16, 0, 2.69), (4.05, 0, 2.46), 0.25, 0.12)
    # Brow shelves and cheek pads blend into the skull.
    for side in (-1, 1):
        _blob_chain(blobs, (2.96, side * 0.27, 3.30),
                    (3.60, side * 0.28, 3.24), 0.19, 0.12)
        _blob_chain(blobs, (2.80, side * 0.26, 2.93),
                    (3.28, side * 0.28, 2.88), 0.20, 0.12)
    # Long tapered tail, not a chain of disconnected spheres.
    tail = [
        (-1.8, 0, 2.31, 0.63), (-2.5, 0, 2.17, 0.48),
        (-3.3, 0, 1.96, 0.37), (-4.1, 0, 1.74, 0.29),
        (-5.0, 0, 1.51, 0.21), (-5.9, 0, 1.35, 0.15),
        (-6.8, 0, 1.27, 0.08)]
    for a, b in zip(tail, tail[1:]):
        _blob_chain(blobs, a[:3], b[:3], a[3], b[3], spacing=0.14)
    toes = []
    for side in (-1, 1):
        toes += _leg_blobs(blobs, (-1.55, side * 0.67, 2.25), side, hind=True)
        toes += _leg_blobs(blobs, (0.92, side * 0.66, 2.30), side, hind=False)
    # Wing bones blend into shoulders and membranes.
    wing_configs = []
    for side in (-1, 1):
        root = (0.10, side * 0.64, 2.95)
        elbow = (-0.45, side * 1.65, 3.72)
        wrist = (-0.95, side * 3.1, 4.08)
        fingers = [
            (-2.10, side * 5.25, 4.25),
            (-3.05, side * 4.80, 3.55),
            (-3.60, side * 3.85, 2.95),
            (-3.45, side * 2.75, 2.40)]
        for a, b, ra, rb in [
            (root, elbow, 0.29, 0.22),
            (elbow, wrist, 0.23, 0.17),
            (wrist, fingers[0], 0.17, 0.06),
            (wrist, fingers[1], 0.16, 0.055),
            (wrist, fingers[2], 0.15, 0.055),
            (wrist, fingers[3], 0.14, 0.052)]:
            _blob_chain(blobs, a, b, ra, rb, spacing=0.20)
        wing_configs.append((root, elbow, wrist, fingers, side))
    parts = [_metas("Dragon_Core_Anatomy", blobs, resolution=0.095)]
    for i, (base, tip) in enumerate(toes):
        parts.append(_spike("Talons_%02d" % i, base, tip, 0.11))
    for side in (-1, 1):
        # Horn roots intersect the skull.
        parts.append(_spike("CrownHorn_%s" % side,
                            (2.90, side * 0.33, 3.35),
                            (2.35, side * 0.70, 4.17), 0.24))
        parts.append(_spike("CheekHorn_%s" % side,
                            (3.32, side * 0.33, 3.04),
                            (2.87, side * 0.76, 3.24), 0.17))
        parts.append(_spike("BrowHorn_%s" % side,
                            (3.65, side * 0.28, 3.26),
                            (3.50, side * 0.48, 3.65), 0.12))
    for i, (root, elbow, wrist, fingers, side) in enumerate(wing_configs):
        parts.append(_wing_membrane("Wing_Membrane_%d" % i,
                                    root, elbow, wrist, fingers, side))
    # Layered dorsal spines following neck, torso and tail.
    for i in range(51):
        x = -6.3 + i * 0.18
        if x < -2.2:
            z = 1.27 + (x + 6.8) * 0.20
            radius = 0.09
            height = 0.15 + 0.12 * (x + 6.3) / 4.1
        elif x < 1.2:
            z = 3.10 + 0.06 * math.cos(x * 2)
            radius = 0.13
            height = 0.38 + 0.12 * math.sin(i * 1.4)
        else:
            z = 3.02 + (x - 1.2) * 0.12
            radius = 0.12
            height = 0.24 + 0.12 * math.sin(i * 1.4)
        parts.append(_spike("DorsalSpike_%02d" % i,
                           (x, 0, z - 0.14),
                           (x - 0.18, 0, z + height), radius))
    # Shallow overlapping geometric scutes: actual mesh relief, no textures.
    # Roots are embedded well inside the torso so every plate fuses to the skin.
    for side in (-1, 1):
        for ix in range(20):
            x = -1.65 + ix * 0.145
            for iz in range(7):
                z = 1.92 + iz * 0.14 + (ix % 2) * 0.065
                y0 = side * 0.50
                y1 = side * (0.80 + 0.025 * math.sin(ix * 2.1 + iz))
                parts.append(_spike("BodyScale_%s_%02d_%02d" % (side, ix, iz),
                           (x, y0, z),
                           (x - 0.07, y1, z + 0.08),
                           radius=0.072, sides=9))
        for ix in range(14):
            x = 1.35 + ix * 0.085
            z = 2.88 + 0.035 * math.sin(ix * 1.3)
            parts.append(_spike("NeckScale_%s_%02d" % (side, ix),
                       (x, side * 0.23, z),
                       (x - 0.045, side * 0.47, z + 0.075),
                       radius=0.06, sides=9))
        for ix in range(15):
            x = -1.7 + 0.1 * math.sin(ix * 0.8)
            z = 1.25 + ix * 0.07
            parts.append(_spike("HindThighPlate_%s_%02d" % (side, ix),
                       (x, side * 0.77, z),
                       (x - 0.09, side * 1.05, z + 0.08),
                       radius=0.075, sides=9))
    # Real geometric teeth rooted into upper and lower jaws.
    for side in (-1, 1):
        for i in range(8):
            x = 3.30 + i * 0.105
            parts.append(_spike("UpperTooth_%s_%02d" % (side, i),
                (x, side * 0.18, 3.01), (x + 0.04, side * 0.20, 2.76),
                radius=0.055, sides=9))
            parts.append(_spike("LowerTooth_%s_%02d" % (side, i),
                (x, side * 0.14, 2.58), (x - 0.03, side * 0.18, 2.76),
                radius=0.046, sides=9))
    # Brow and jaw ridge scales create geometry without texture maps.
    for side in (-1, 1):
        for i in range(10):
            x = 2.9 + i * 0.12
            parts.append(_spike("FacialScute_%s_%02d" % (side, i),
                       (x, side * 0.29, 3.23 - 0.03 * i),
                       (x - 0.04, side * 0.37, 3.37 - 0.03 * i), 0.065))
    return [p for p in parts if p is not None]
