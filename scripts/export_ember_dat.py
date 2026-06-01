#!/usr/bin/env python3
import argparse
import csv
import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]

EMBER_MODULE_PATH = REPO_ROOT / "malware_rl" / "envs" / "utils" / "ember.py"
ember_spec = importlib.util.spec_from_file_location("meme_modify_ember", EMBER_MODULE_PATH)
ember_module = importlib.util.module_from_spec(ember_spec)
sys.modules[ember_spec.name] = ember_module
ember_spec.loader.exec_module(ember_module)
PEFeatureExtractor = ember_module.PEFeatureExtractor


FEATURE_DIM = 2381


def iter_files(paths):
    for root in paths:
        root = Path(root)
        if not root.exists():
            raise FileNotFoundError(f"Input path does not exist: {root}")
        if root.is_file():
            yield root, root.parent.name
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                try:
                    relative = path.relative_to(root)
                    family = relative.parts[0] if len(relative.parts) > 1 else path.parent.name
                except ValueError:
                    family = path.parent.name
                yield path, family


def collect_labeled_files(benign_roots, malware_roots):
    files = []
    files.extend((path, 0.0, family) for path, family in iter_files(benign_roots))
    files.extend((path, 1.0, family) for path, family in iter_files(malware_roots))
    if not files:
        raise ValueError("No files found for this split")
    return files


def write_split(files, output_dir, split_name, skip_errors):
    extractor = PEFeatureExtractor(feature_version=2)
    if extractor.dim != FEATURE_DIM:
        raise RuntimeError(f"Unexpected feature dimension: {extractor.dim}")

    output_dir.mkdir(parents=True, exist_ok=True)
    x_path = output_dir / f"X_{split_name}.dat"
    y_path = output_dir / f"y_{split_name}.dat"

    x_mem = np.memmap(x_path, dtype=np.float32, mode="w+", shape=(len(files), FEATURE_DIM))
    y_mem = np.memmap(y_path, dtype=np.float32, mode="w+", shape=(len(files),))

    written = 0
    failed = []
    manifest_rows = []
    for path, label, family in files:
        try:
            bytez = path.read_bytes()
            features = extractor.feature_vector(bytez)
            if features.shape != (FEATURE_DIM,):
                raise ValueError(f"expected shape {(FEATURE_DIM,)}, got {features.shape}")
        except Exception as exc:
            if not skip_errors:
                raise RuntimeError(f"Failed to extract features from {path}: {exc}") from exc
            failed.append((str(path), str(exc)))
            continue

        x_mem[written, :] = features
        y_mem[written] = label
        manifest_rows.append(
            {
                "index": written,
                "label": int(label),
                "family": family,
                "path": str(path),
            }
        )
        written += 1

        if written % 100 == 0:
            print(f"{split_name}: wrote {written}/{len(files)}")

    x_mem.flush()
    y_mem.flush()

    if written != len(files):
        compact_x = np.array(
            np.memmap(x_path, dtype=np.float32, mode="r", shape=(len(files), FEATURE_DIM))[:written],
            copy=True,
        )
        compact_y = np.array(
            np.memmap(y_path, dtype=np.float32, mode="r", shape=(len(files),))[:written],
            copy=True,
        )
        del x_mem
        del y_mem
        x_mem = np.memmap(x_path, dtype=np.float32, mode="w+", shape=(written, FEATURE_DIM))
        y_mem = np.memmap(y_path, dtype=np.float32, mode="w+", shape=(written,))
        x_mem[:] = compact_x
        y_mem[:] = compact_y
        x_mem.flush()
        y_mem.flush()

    if failed:
        failed_path = output_dir / f"{split_name}_failed.txt"
        failed_path.write_text(
            "\n".join(f"{path}\t{error}" for path, error in failed) + "\n",
            encoding="utf-8",
        )

    manifest_path = output_dir / f"{split_name}_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "label", "family", "path"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"{split_name}: wrote {written} samples to {x_path} and {y_path}")
    print(f"{split_name}: wrote manifest to {manifest_path}")
    if failed:
        print(f"{split_name}: skipped {len(failed)} failed files; see {failed_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Export PE folders to EMBER/SOREL 2381-dim memmap .dat files for surrogate.py."
    )
    parser.add_argument("--out", required=True, help="Output directory for X_val/y_val/X_test/y_test .dat files")
    parser.add_argument("--val-benign", nargs="+", required=True, help="Benign folder(s) or file(s) for X_val/y_val")
    parser.add_argument("--val-malware", nargs="+", required=True, help="Malware folder(s) or file(s) for X_val/y_val")
    parser.add_argument("--test-benign", nargs="+", required=True, help="Benign folder(s) or file(s) for X_test/y_test")
    parser.add_argument("--test-malware", nargs="+", required=True, help="Malware folder(s) or file(s) for X_test/y_test")
    parser.add_argument("--skip-errors", action="store_true", help="Skip files that LIEF cannot parse")
    args = parser.parse_args()

    output_dir = Path(args.out)
    val_files = collect_labeled_files(args.val_benign, args.val_malware)
    test_files = collect_labeled_files(args.test_benign, args.test_malware)

    write_split(val_files, output_dir, "val", args.skip_errors)
    write_split(test_files, output_dir, "test", args.skip_errors)


if __name__ == "__main__":
    main()
