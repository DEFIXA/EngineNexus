"""Guarded Meshy image-to-3D submission. Only candidate creation, never game-ready claim."""
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


def submit_image_candidate(spec: AssetSpec) -> dict:
    spec.validate()
    if not spec.references:
        raise ValueError("Meshy image-to-3D requires an approved reference image")
    token = os.environ.get("MESHY_API_KEY")
    if not token:
        raise RuntimeError("MESHY_API_KEY is not set")
    reference = spec.references[0]
    if reference.startswith(("https://", "http://")):
        if not reference.startswith("https://"):
            raise ValueError("Only HTTPS hosted references are allowed")
        image_url = reference
    else:
        path = Path(reference)
        data = path.read_bytes()
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError("Reference image exceeds configured upload limit")
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("Reference must be PNG, JPEG or WebP")
        image_url = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
    payload = {
        "image_url": image_url,
        "ai_model": os.environ.get("MESHY_MODEL", "meshy-7.1"),
        "should_texture": True,
        "enable_pbr": True,
        "should_remesh": True,
        "target_polycount": min(spec.target_triangles, 100000),
        "target_formats": ["glb"],
    }
    req = Request(API, data=json.dumps(payload).encode("utf-8"),
                  headers={"Authorization": f"Bearer {token}",
                           "Content-Type": "application/json"},
                  method="POST")
    with urlopen(req, timeout=120) as response:
        result = json.load(response)
    return {"provider": "meshy", "task": result, "status": "submitted_not_downloaded"}
