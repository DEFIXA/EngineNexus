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
    alternatives: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


def route(spec: AssetSpec) -> Route:
    spec.validate()
    if spec.backend != "auto":
        backend = spec.backend
        reason = "Explicit backend selected by user"
    elif spec.references and spec.category in {"creature", "animal", "human", "prop", "vehicle", "weapon"}:
        backend = "meshy"
        reason = "Reference-conditioned 3D candidate is preferred; paid-cloud consent is required"
    elif spec.category in {"tree", "root", "foliage", "rock", "terrain"}:
        backend = "blender"
        reason = "Procedural control and variation are appropriate for nature"
    elif spec.category in {"creature", "animal"} and "leg" in spec.prompt.lower():
        backend = "blender"
        reason = "Editable offline dragon-leg anatomy scaffold; artist review required"
    elif spec.category == "structure":
        backend = "blender"
        reason = "Deterministic modular/hard-surface building scaffold"
    else:
        backend = "meshy"
        reason = "No reliable built-in geometry builder for this arbitrary prompt; cloud candidate requires explicit paid consent"

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

    if spec.category in {"creature", "animal", "human"}:
        alternatives = ("meshy", "external_ai", "blender")
    elif spec.category in {"tree", "root", "foliage", "rock", "terrain"}:
        alternatives = ("infinigen", "blender", "meshy")
    elif spec.category in {"structure", "vehicle", "weapon"}:
        alternatives = ("blender", "meshy", "external_ai")
    else:
        alternatives = ("meshy", "blender", "external_ai")

    return Route(
        backend=backend,
        reason=reason,
        stages=tuple(stages),
        requires_human_retopology=spec.animated,
        requires_paid_consent=backend == "meshy",
        reference_review=bool(spec.references),
        alternatives=alternatives,
    )
