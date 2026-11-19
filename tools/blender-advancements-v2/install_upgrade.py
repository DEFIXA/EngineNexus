"""Safely merge V2 overlay into the original ZIP, preserving original files.

Run from the directory containing this script. Does not overwrite the source ZIP.
"""
from __future__ import annotations
import argparse
import stat
import zipfile
from pathlib import Path, PurePosixPath

def safe_name(name):
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe ZIP entry: {name}")
    return name

def merge(original, output):
    original, output = Path(original).resolve(), Path(output).resolve()
    if original == output:
        raise ValueError("Output must differ from original archive")
    overlay = Path(__file__).resolve().parent
    additions = [p for p in overlay.rglob("*") if p.is_file()
                 and "__pycache__" not in p.parts and ".git" not in p.parts]
    with zipfile.ZipFile(original) as src:
        entries = src.infolist()
        names = set()
        for info in entries:
            name = safe_name(info.filename)
            if (info.external_attr >> 16) & 0o170000 == stat.S_IFLNK:
                raise ValueError("Symlink in original ZIP")
            if name in names:
                raise ValueError(f"Duplicate ZIP entry: {name}")
            names.add(name)
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as dst:
            for info in entries:
                dst.writestr(info, src.read(info))
            for path in additions:
                rel = path.relative_to(overlay).as_posix()
                # Keep the upgrade in its own namespace, never clobber original files.
                dest = "blender_advancements_v2/" + rel
                if dest in names:
                    raise ValueError(f"Upgrade already present: {dest}")
                dst.write(path, dest)
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("original_zip")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(merge(args.original_zip, args.output))

if __name__ == "__main__":
    main()
