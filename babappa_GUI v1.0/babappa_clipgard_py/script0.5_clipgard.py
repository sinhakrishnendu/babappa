#!/usr/bin/env python3
"""
script0.5.py
Run HyPhy GARD (codon-aware) on all *.msa.best.fas files in msa/ folder.
Store results in gard_output/ as JSON.
Then run split_recombination_blocks.py and filter_blocks.py.
"""

import os
import glob
import subprocess
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import sys, io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ------------------ Helpers ------------------ #
def run_command(cmd):
    """Run a shell command safely."""
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {cmd}\n{e}")
        return False
    return True


# ------------------ Step 1: HyPhy GARD ------------------ #
def run_gard(input_file, out_dir):
    base_name = os.path.basename(input_file).replace(".fas", "")
    output_file = os.path.join(out_dir, f"{base_name}.gard.json")

    if os.path.exists(output_file):
        print(f"⏩ Skipping {input_file} (JSON already exists)")
        return output_file

    print(f"▶ Running GARD on {input_file} ...")
    ok = run_command(f"hyphy gard --alignment {input_file} --type codon --output {output_file}")
    if ok:
        print(f"✔ Finished {input_file} → {output_file}")
    return output_file if ok else None


# ------------------ Step 2: Split recombination blocks ------------------ #
def run_splitter(fas_file, json_file, py_script="split_recombination_blocks.py"):
    if not os.path.exists(json_file):
        print(f"⚠ No JSON found for {fas_file}")
        return
    print(f"▶ Processing {fas_file} with {json_file}")
    run_command(f"python3 {py_script} {fas_file} {json_file}")


# ------------------ Step 3: Filter blocks ------------------ #
def run_filter(py_script="filter_blocks.py"):
    print("▶ Filtering recombination blocks (codon checks)...")
    run_command(f"python3 {py_script}")
    print("✅ Filtering done. Valid blocks in recombination_blocks/, discarded ones in discarded_blocks/")


# ------------------ Main ------------------ #
def main():
    msa_dir = "msa"
    out_dir = "gard_output"
    os.makedirs(out_dir, exist_ok=True)

    total_cores = multiprocessing.cpu_count()
    cores = 1 if total_cores <= 2 else total_cores - 2
    print(f"Detected {total_cores} CPU cores. Using {cores} for GARD.")

    files = glob.glob(os.path.join(msa_dir, "*msa.best.fas"))
    if not files:
        print(f"❌ No msa.best.fas files found in {msa_dir}/")
        return

    # Run GARD in parallel
    with ThreadPoolExecutor(max_workers=cores) as exe:
        gard_results = list(exe.map(lambda f: run_gard(f, out_dir), files))

    print("✅ All GARD analyses completed. JSONs in gard_output/")

    # Step 2: Split recombination blocks
    print("▶ Running Python script to split recombination blocks...")
    for fas in glob.glob(os.path.join(msa_dir, "*.fas")):
        json_file = os.path.join(out_dir, os.path.basename(fas).replace(".fas", ".gard.json"))
        run_splitter(fas, json_file)

    # Step 3: Filter blocks
    run_filter()


if __name__ == "__main__":
    main()
