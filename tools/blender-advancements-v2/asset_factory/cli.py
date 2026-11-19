"""Command line controller. Runs Blender only when the user supplies a Blender executable."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from .spec import AssetSpec
from .router import route
from .quality import audit_file


def main(argv=None):
    p = argparse.ArgumentParser(description="Blender Advancements V2 asset controller")
    subs = p.add_subparsers(dest="command", required=True)
    for name in ("plan", "build", "audit"):
        s = subs.add_parser(name)
        s.add_argument("spec_or_qc")
        if name == "build":
            s.add_argument("--blender", required=False)
            s.add_argument("--allow-paid", action="store_true")
            s.add_argument("--meshy-cli", default="meshy")
    args = p.parse_args(argv)
    if args.command == "audit":
        print(json.dumps(audit_file(args.spec_or_qc).to_dict(), indent=2))
        return 0

    spec = AssetSpec.load(args.spec_or_qc)
    selected = route(spec)
    print(json.dumps({"asset": spec.asset_id, "route": selected.to_dict()}, indent=2))
    if args.command == "plan":
        return 0

    output = Path(spec.output_root).resolve() / spec.asset_id
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"asset_id": spec.asset_id, "spec": spec.to_dict(),
                "route": selected.to_dict(), "status": "planned"}
    (output / "spec.json").write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if selected.backend == "meshy":
        if not args.allow_paid:
            raise SystemExit("Meshy requires --allow-paid after user approves cloud upload and cost")
        from .meshy_cli import generate_candidate
        result = generate_candidate(spec, output, executable=args.meshy_cli)
        manifest.update(status="cloud_candidate_downloaded_unvalidated", meshy=result)
    elif selected.backend == "infinigen":
        from .infinigen import run_individual_asset
        result = run_individual_asset(spec, output)
        manifest.update(status="infinigen_candidate_generated", command=result)
    elif selected.backend == "external_ai":
        raise SystemExit("External AI requires a separately configured provider; no command is assumed")
    elif selected.backend == "blender":
        if not args.blender:
            raise SystemExit("Blender executable required for build: --blender PATH")
        worker = Path(__file__).with_name("blender_worker.py").resolve()
        cmd = [args.blender, "--background", "--factory-startup",
               "--python", str(worker), "--", str(output / "spec.json"), str(output)]
        subprocess.run(cmd, check=True, timeout=1800)
        manifest.update(status="blender_candidate_generated",
                        qc_file=str(output / "qc.json"))
    else:
        raise SystemExit(f"Unsupported backend: {selected.backend}")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
