"""Meshy CLI orchestration: one paid create, resume by task ID, wait, download GLB.

Requires meshy-cli >= 0.8.5, Node.js 22.12+, and meshy auth login.
User explicitly authorizes costs and cloud reference uploads via --allow-paid.
"""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from .spec import AssetSpec

TAIL = ["--async", "--format", "json", "--no-update-check"]


def _call(cmd: list[str], timeout=900) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=timeout, check=True)
    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Meshy CLI did not return its expected JSON envelope") from exc
    if not isinstance(envelope, dict):
        raise RuntimeError("Unexpected Meshy CLI envelope")
    return envelope


def _task_id(envelope: dict) -> str:
    result = envelope.get("result", {})
    submission = result.get("submission", {}) if isinstance(result, dict) else {}
    task_id = submission.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise RuntimeError("Meshy did not provide a task ID; do not resubmit blindly")
    return task_id


def _create_command(spec: AssetSpec, executable: str) -> tuple[str, list[str]]:
    common = ["--target-formats", "glb"]
    smart = spec.animated or spec.category in {"creature", "animal", "human", "prop", "weapon"}
    if smart:
        limit = 30000 if spec.category in {"creature", "animal", "human"} else 15000
        topology = ["--model-type", "smart-topology", "--target-polycount",
                    str(max(100, min(limit, spec.target_triangles)))]
    else:
        topology = ["--model-type", "standard"]

    if len(spec.references) > 1:
        # All images must depict the SAME object, front first.
        resource = "multi-image-to-3d"
        images = json.dumps({"image_urls": spec.references})
        cmd = [executable, resource, "create", "--data", images]
        cmd += ["--should-texture", "true", "--texture-model", "meshy-7",
                "--enable-pbr", "true"] + common + TAIL
    elif spec.references:
        resource = "image-to-3d"
        cmd = [executable, resource, "create", "--image-url", spec.references[0]]
        cmd += topology
        if smart:
            cmd += ["--texture-model", "meshy-n1"]
            if spec.category == "human":
                cmd += ["--pose-mode", "a-pose"]
        else:
            cmd += ["--texture-model", "meshy-7", "--enable-pbr", "true"]
        cmd += common + TAIL
    else:
        resource = "text-to-3d"
        cmd = [executable, resource, "create", "--mode", "preview",
               "--prompt", spec.prompt]
        cmd += topology + common + TAIL
    return resource, cmd


def generate_candidate(spec: AssetSpec, output: Path, *, executable="meshy") -> dict:
    spec.validate()
    if not shutil.which(executable) and not Path(executable).exists():
        raise RuntimeError("Meshy CLI missing; install meshy-cli >=0.8.5 and authenticate")
    output.mkdir(parents=True, exist_ok=True)
    fingerprint = hashlib.sha256(
        json.dumps(spec.to_dict(), sort_keys=True).encode("utf-8")).hexdigest()
    state_file = output / "meshy_task.json"
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if state.get("fingerprint") != fingerprint:
            raise RuntimeError("Existing paid task belongs to a different spec; use a new asset_id")
        resource = state["resource"]
        task_id = state["task_id"]
    else:
        resource, cmd = _create_command(spec, executable)
        created = _call(cmd, timeout=180)
        task_id = _task_id(created)
        state = {"fingerprint": fingerprint, "resource": resource, "task_id": task_id,
                 "status": "submitted"}
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    _call([executable, resource, "wait", task_id, "--timeout", "600",
           "--format", "json", "--no-update-check"], timeout=660)
    asset = output / "asset.glb"
    _call([executable, resource, "get", task_id, "-o", str(asset),
           "--workspace", str(output.resolve()), "--format", "json",
           "--no-update-check"], timeout=180)
    if not asset.exists() or asset.stat().st_size == 0:
        raise RuntimeError("Meshy completed but no GLB was delivered; inspect task state")
    state["status"] = "downloaded_unvalidated"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return {"provider": "meshy-cli", "resource": resource, "task_id": task_id,
            "model_path": str(asset), "status": "downloaded_unvalidated"}
