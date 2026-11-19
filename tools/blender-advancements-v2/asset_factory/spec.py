"""Validated, serializable specification for a 3D game asset."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import json
import re

CATEGORIES = {
    "creature", "human", "animal", "tree", "foliage", "root",
    "rock", "terrain", "structure", "prop", "vehicle", "weapon", "other"
}
BACKENDS = {"auto", "blender", "infinigen", "meshy", "external_ai"}
PLATFORMS = {"pc", "console", "mobile", "vr"}
_SAFE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")


@dataclass
class AssetSpec:
    asset_id: str
    prompt: str
    category: str
    references: list[str] = field(default_factory=list)
    animated: bool = False
    backend: str = "auto"
    platform: str = "pc"
    target_triangles: int = 40000
    texture_size: int = 2048
    seed: int = 42
    target_engine: str = "UE5"
    style: str = "realistic_dark_fantasy"
    notes: str = ""
    license_notes: str = ""
    output_root: str = "work"
    max_lod_count: int = 3
    require_human_review: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> "AssetSpec":
        if not _SAFE_ID.fullmatch(self.asset_id):
            raise ValueError("asset_id must be a simple safe identifier")
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if self.category not in CATEGORIES:
            raise ValueError(f"Unknown category: {self.category}")
        if self.backend not in BACKENDS:
            raise ValueError(f"Unknown backend: {self.backend}")
        if self.platform not in PLATFORMS:
            raise ValueError(f"Unknown platform: {self.platform}")
        if not 100 <= self.target_triangles <= 200_000:
            raise ValueError("target_triangles out of supported range")
        if self.texture_size not in {512, 1024, 2048, 4096, 8192}:
            raise ValueError("texture_size must be a power-of-two production size")
        if not 0 <= self.max_lod_count <= 5:
            raise ValueError("max_lod_count must be 0..5")
        if not isinstance(self.references, list) or not all(isinstance(r, str) for r in self.references):
            raise ValueError("references must be a list of paths")
        if not isinstance(self.seed, int):
            raise ValueError("seed must be an integer")
        return self

    @classmethod
    def load(cls, filename: str | Path) -> "AssetSpec":
        data = json.loads(Path(filename).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Asset specification must be a JSON object")
        allowed = set(cls.__dataclass_fields__)
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"Unknown asset spec keys: {sorted(unknown)}")
        return cls(**data).validate()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, filename: str | Path) -> None:
        self.validate()
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
