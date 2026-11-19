"""Backend routing based on asset semantics and real execution constraints."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from .spec import AssetSpec


@dataclass(frozen=True)
class Route:
    backend: str
    reason: str
    stages: tuple[str, ...]
    requires_human_retopology: bool
    requires_paid_consent: bool
    reference_review: bool

    def to_dict(self):
        return asdict(self)


def route(spec: AssetSpec) -> Route:
    spec.validate()
    if spec.backend != "auto":
        backend = spec.backend
        reason = "Explicit backend selected by user"
    elif spec.category in {"tree", "root", "foliage", "rock", "terrain"}:
        backend = "blender"
        reason = "Procedural control and variation are appropriate for nature"
    elif spec.category in {"creature", "animal", "human"}:
        backend = "blender"
        reason = "Controllable anatomy scaffold; AI can supply a separate reference candidate"
    elif spec.category in {"structure", "vehicle", "weapon"}:
        backend = "blender"
        reason = "Deterministic modular/hard-surface construction"
    else:
        backend = "blender"
        reason = "Default offline deterministic candidate; explicit cloud backend is opt-in"

    stages = [
        "reference_analysis",
        "primary_form",
        "silhouette_review",
        "secondary_detail",
        "runtime_mesh",
        "uv_review",
        "material_and_bake_review",
    ]
    if spec.animated:
        stages.extend(["authored_deformation_retopology", "rig_and_pose_tests"])
    else:
        stages.extend(["static_lods", "collision_review"])
    stages.extend(["technical_qc", "export", "unreal_import_and_profile"])

    return Route(
        backend=backend,
        reason=reason,
        stages=tuple(stages),
        requires_human_retopology=spec.animated,
        requires_paid_consent=backend == "meshy",
        reference_review=bool(spec.references),
    )
