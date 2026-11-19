"""Guarded Meshy image-to-3D candidate creation; no paid request without explicit CLI consent."""
from __future__ import annotations
import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib.request import Request, urlopen
from .spec import AssetSpec

API = "https://api.meshy.ai/openapi/v1/image-to-3d"
MAX_IMAGE_BYTES = 12 * 1024 * 1024


def _reference_data_uri(reference: str) -> str:
    if reference.startswith("https://"):
        return reference
    if reference.startswith("http://"):
        raise ValueError("Reference URL must use HTTPS")
    path = Path(reference)
    data = path.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Reference image exceeds configured upload limit")
    mime = mimetypes.guess_type(path.name)[0]
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise ValueError("Reference must be PNG, JPEG or WebP")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def build_payload(spec: AssetSpec, image_url: str) -> dict:
    """Model-specific fields follow documented Meshy image-to-3D CLI/API variants."""
    if spec.animated or spec.category in {"creature", "animal", "human"}:
        # Smart topology helps but DOES NOT replace reviewed deformation retopology.
        return {
            "image_url": image_url,
            "ai_model": "meshy-t2.5",
            "model_type": "smart-topology",
            "target_polycount": max(100, min(30000, spec.target_triangles)),
            "texture_model": "meshy-n1",
            "should_texture": True,
            "pose_mode": "a-pose" if spec.category == "human" else None,
            "target_formats": ["glb"],
        }
    if spec.category in {"prop", "weapon", "vehicle"}:
        return {
            "image_url": image_url,
            "ai_model": "meshy-t2",
            "model_type": "smart-topology",
            "target_polycount": max(100, min(15000, spec.target_triangles)),
            "texture_model": "meshy-n1",
            "should_texture": True,
            "target_formats": ["glb"],
        }
    return {
        "image_url": image_url,
        "ai_model": "meshy-7.1",
        "model_type": "standard",
        "texture_model": "meshy-7",
        "should_texture": True,
        "enable_pbr": True,
        "target_formats": ["glb"],
    }


def submit_image_candidate(spec: AssetSpec) -> dict:
    spec.validate()
    if not spec.references:
        raise ValueError("Meshy image-to-3D requires an approved reference image")
    token = os.environ.get("MESHY_API_KEY")
    if not token:
        raise RuntimeError("MESHY_API_KEY is not set")
    payload = {k: v for k, v in build_payload(
        spec, _reference_data_uri(spec.references[0])).items() if v is not None}
    req = Request(API, data=json.dumps(payload).encode("utf-8"),
                  headers={"Authorization": f"Bearer {token}",
                           "Content-Type": "application/json"},
                  method="POST")
    with urlopen(req, timeout=120) as response:
        result = json.load(response)
    return {"provider": "meshy", "task": result, "status": "submitted_not_downloaded"}
