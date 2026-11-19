"""Evaluate Blender-generated technical QC without claiming artistic validation."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class QualityDecision:
    technical_pass: bool
    visual_review_required: bool
    rig_review_required: bool
    engine_validation_required: bool
    visual_approved: bool
    failures: list[str]

    def to_dict(self):
        return asdict(self)


def decide(qc: dict, *, animated: bool, references: bool, triangle_budget: int, allow_open_mesh: bool = False, require_connected: bool = False, require_png: bool = False) -> QualityDecision:
    failures: list[str] = []
    if not qc.get("objects"):
        failures.append("No mesh objects were audited")
    for obj in qc.get("objects", []):
        name = obj.get("name", "<unnamed>")
        if obj.get("triangles", 0) <= 0:
            failures.append(f"{name}: empty mesh")
        if obj.get("loose_vertices", 0):
            failures.append(f"{name}: loose vertices")
        nonmanifold = obj.get("non_manifold_edges", 0)
        boundary = obj.get("boundary_edges", 0)
        if nonmanifold and not (allow_open_mesh and nonmanifold == boundary):
            failures.append(f"{name}: non-manifold edges")
        if not obj.get("has_uv", False):
            failures.append(f"{name}: no UV map")
        if obj.get("negative_scale", False):
            failures.append(f"{name}: negative scale")
        if require_connected and obj.get("connected_components", 0) != 1:
            failures.append(f"{name}: disconnected mesh with {obj.get('connected_components', 'unknown')} components")
        if require_connected and obj.get("largest_component_triangle_fraction", 0) < 0.999:
            failures.append(f"{name}: floating islands / incomplete anatomy")
    runtime_triangles = qc.get("runtime_triangles")
    if runtime_triangles is None:
        failures.append("Runtime triangle count not measured")
    elif runtime_triangles > triangle_budget:
        failures.append(f"Triangle budget exceeded: {runtime_triangles} > {triangle_budget}")
    required = {"clay_front.png", "clay_side.png", "clay_three_quarter.png"}
    if require_png and not required.issubset(set(qc.get("clay_render_files", []))):
        failures.append("Three actual Blender clay PNG views required")
    if qc.get("errors"):
        failures.extend(str(x) for x in qc["errors"])
    return QualityDecision(
        technical_pass=not failures,
        visual_review_required=references or require_png,
        rig_review_required=animated,
        engine_validation_required=True,
        visual_approved=False,
        failures=failures,
    )


def audit_file(path: str | Path, *, animated=False, references=False, triangle_budget=40000, allow_open_mesh=False, require_connected=False, require_png=False):
    qc = json.loads(Path(path).read_text(encoding="utf-8"))
    return decide(qc, animated=animated, references=references,
                  triangle_budget=triangle_budget, allow_open_mesh=allow_open_mesh,
                  require_connected=require_connected, require_png=require_png)
