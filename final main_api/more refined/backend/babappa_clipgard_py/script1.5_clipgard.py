#!/usr/bin/env python3
"""
glue.py

Python equivalent of glue.sh

Creates an "analysis" folder (or a custom target) and:
  1. copies the entire 'foregroundbranch' directory
  2. copies the entire 'treefiles' directory
  3. copies all *.fas files from 'recombination_blocks' into analysis/msa/
  4. copies a list of scripts/files into the analysis folder

Usage:
    python3 glue.py
    python3 glue.py --target my_analysis_dir
"""

from pathlib import Path
import shutil
import argparse
import sys

def copy_tree(src: Path, dst: Path):
    if not src.exists():
        print(f"[WARN] Source directory not found: {src}")
        return False
    try:
        # copytree with dirs_exist_ok available in Python 3.8+
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"[OK] Copied directory: {src} -> {dst}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to copy directory {src} -> {dst}: {e}")
        return False

def copy_file(src: Path, dst_dir: Path):
    if not src.exists():
        print(f"[WARN] File not found, skipping: {src}")
        return False
    try:
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_dir)
        print(f"[OK] Copied file: {src} -> {dst_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to copy file {src} -> {dst_dir}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Glue script (Python) to prepare analysis folder.")
    parser.add_argument("--target", "-t", default="analysis", help="Target analysis directory (default: analysis)")
    args = parser.parse_args()

    cwd = Path.cwd()
    target_dir = (cwd / args.target).resolve()

    print(f"Creating analysis directory structure at: {target_dir}")
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[FATAL] Could not create target directory {target_dir}: {e}")
        sys.exit(1)

    # 1. Copy the entire foregroundbranch directory
    copy_tree(cwd / "foregroundbranch", target_dir / "foregroundbranch")

    # 2. Copy the entire treefiles directory
    copy_tree(cwd / "treefiles", target_dir / "treefiles")

    # 3. Copy recombination_blocks *.fas files into a new subfolder called msa inside analysis
    msa_out = target_dir / "msa"
    msa_out.mkdir(parents=True, exist_ok=True)
    recomb_dir = cwd / "recombination_blocks"
    if not recomb_dir.exists():
        print(f"[WARN] recombination_blocks directory not found: {recomb_dir} (no .fas files copied)")
    else:
        count = 0
        for path in recomb_dir.rglob("*.fas"):
            try:
                shutil.copy2(path, msa_out)
                count += 1
            except Exception as e:
                print(f"[ERROR] Could not copy {path} -> {msa_out}: {e}")
        print(f"[OK] Copied {count} .fas file(s) from {recomb_dir} to {msa_out}")

    # 4. Copy listed scripts and files into analysis
    files_to_copy = [
        "lrt_bh_correction.py",
        "lrt_bh_correction.sitemodel.py",
        "run_codeml.py",
        "codeml.ctl",
        "script2.sh",
        "script3.sh",
        "script4.sh",
        "script5.sh",
        "script6.sh",
        "script7.sh",
        "script8.sh",
    ]

    copied = []
    skipped = []
    for fname in files_to_copy:
        src = cwd / fname
        if src.exists():
            ok = copy_file(src, target_dir)
            if ok:
                copied.append(fname)
            else:
                skipped.append(fname)
        else:
            print(f"[WARN] File not found, skipping: {fname}")
            skipped.append(fname)

    print()
    print("Summary:")
    print(f"  Target directory: {target_dir}")
    print(f"  Directories copied: {'foregroundbranch, treefiles' if (target_dir/'foregroundbranch').exists() or (target_dir/'treefiles').exists() else 'none'}")
    print(f"  .fas files copied to {msa_out}: {len(list(msa_out.glob('*.fas')))}")
    print(f"  Files copied: {copied}")
    if skipped:
        print(f"  Files skipped/missing: {skipped}")

    print(f"\nAll files and directories copied (where present) into {target_dir}/")

if __name__ == "__main__":
    main()
