"""Infinigen individual asset wrapper. Requires an installed, compatible Infinigen checkout."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from .spec import AssetSpec

FACTORY_DEFAULTS = {"rock": "ChunkyRock", "foliage": "BushFactory"}


def run_individual_asset(spec: AssetSpec, output: Path) -> dict:
    factory = spec.extra.get("infinigen_factory", FACTORY_DEFAULTS.get(spec.category))
    if not factory or not factory.replace("_", "").isalnum():
        raise ValueError("Provide an installed Infinigen factory name in extra.infinigen_factory")
    python = os.environ.get("INFINIGEN_PYTHON", "python")
    cmd = [python, "-m", "infinigen_examples.generate_individual_assets",
           "--output_folder", str(output / "infinigen"), "-f", factory,
           "-n", "1", "--save_blend", "--render", "none", "--export", "obj"]
    subprocess.run(cmd, check=True, timeout=3600)
    return {"factory": factory, "command": cmd, "status": "generated_unvalidated"}
