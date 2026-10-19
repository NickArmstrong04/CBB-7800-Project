"""Download NHANES 2017-Mar 2020 laboratory (P_BIOPRO) and liver elastography
(P_LUX) files and merge them on SEQN into a single CSV.

Usage:
    python merge_lab_liver.py                   # inner join -> data/processed/lab_liver.csv
    python merge_lab_liver.py --how left        # keep every elastography record
    python merge_lab_liver.py --extra P_CBC P_DEMO   # also merge other files
"""
import argparse
import sys
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/{}.xpt"
RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
CORE_FILES = ["P_LUX", "P_BIOPRO"]   # liver elastography, standard biochemistry


def download(name: str, force: bool = False) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / f"{name}.xpt"
    if dest.exists() and not force:
        print(f"  {name}: already downloaded ({dest.stat().st_size:,} bytes)")
        return dest
    print(f"  {name}: downloading ...", end="", flush=True)
    urlretrieve(BASE_URL.format(name), dest)
    print(f" {dest.stat().st_size:,} bytes")
    return dest


def load(path: Path) -> pd.DataFrame:
    df = pd.read_sas(path, format="xport")
    df["SEQN"] = df["SEQN"].astype(int)
    # Clean SAS XPORT artifacts: byte-string text columns and the ~5e-79
    # "fuzz" value that pandas produces for a true SAS zero.
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda v: v.decode().strip() if isinstance(v, bytes) else v)
            df[col] = df[col].replace("", pd.NA)
        elif pd.api.types.is_float_dtype(df[col]):
            df.loc[df[col].abs() < 1e-70, col] = 0.0
    if df["SEQN"].duplicated().any():
        sys.exit(f"ERROR: duplicate SEQN in {path.name}; cannot merge one-to-one")
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--how", default="inner", choices=["inner", "left", "outer"],
                    help="join type; 'left' keeps all P_LUX rows (default: inner)")
    ap.add_argument("--extra", nargs="*", default=[], metavar="FILE",
                    help="additional NHANES files to merge, e.g. P_CBC P_DEMO")
    ap.add_argument("--out", default=OUT_DIR / "lab_liver.csv", type=Path)
    ap.add_argument("--force", action="store_true", help="re-download even if cached")
    args = ap.parse_args()

    files = CORE_FILES + [f for f in args.extra if f not in CORE_FILES]

    print("Downloading:")
    paths = {f: download(f, args.force) for f in files}

    print("Loading:")
    frames = {}
    for f, p in paths.items():
        frames[f] = load(p)
        print(f"  {f}: {len(frames[f]):,} rows, {frames[f].shape[1]} columns")

    # Start from the elastography file: it defines the population.
    merged = frames["P_LUX"]
    for f in files[1:]:
        before = len(merged)
        merged = merged.merge(frames[f], on="SEQN", how=args.how, validate="one_to_one")
        print(f"Merged {f} ({args.how}): {before:,} -> {len(merged):,} rows")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.out, index=False)

    print(f"\nWrote {args.out}: {len(merged):,} rows x {merged.shape[1]} columns")
    if "LUAXSTAT" in merged:
        print(f"Complete elastography exams (LUAXSTAT=1): {(merged['LUAXSTAT'] == 1).sum():,}")
    for col in ("LBXSASSI", "LBXSATSI"):
        if col in merged:
            print(f"{col} non-missing: {merged[col].notna().sum():,}")


if __name__ == "__main__":
    main()
