#!/usr/bin/env python3
import os
import sys
import io
import shutil
import subprocess
import multiprocessing
from pathlib import Path

# ---------------------------------------------------------------------------
# Force stdout/stderr to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Define directories
msa_parent_dir = Path("recombination_blocks")   # new parent folder
tree_dir = Path("treefiles")
output_dir = Path("codemloutput")
base_ctl_file = Path("codeml.ctl")

# ---------------------------------------------------------------------------
# Check for required directories and files
if not msa_parent_dir.is_dir() or not tree_dir.is_dir() or not base_ctl_file.is_file():
    raise SystemExit("Error: Required directories or files are missing.")

# ---------------------------------------------------------------------------
# Function: process_species
def process_species(msa_path: Path):
    species = msa_path.stem  # full block name (e.g. ATCOL_QC_msa.best.fas.gard_block1_1-305)
    species_output = output_dir / species

    tree_file_candidates = list(tree_dir.glob(f"{species}.treefile"))
    if not msa_path.is_file():
        print(f"Warning: MSA file for {species} not found. Skipping...")
        return
    if not tree_file_candidates:
        print(f"Warning: Tree file for {species} not found. Skipping...")
        return

    tree_file = tree_file_candidates[0]

    # Prepare output directory
    species_output.mkdir(parents=True, exist_ok=True)

    # Copy required input files
    shutil.copy(msa_path, species_output / "aligned.fas")
    shutil.copy(tree_file, species_output / "treefile.treefile")
    shutil.copy(base_ctl_file, species_output / "codeml.ctl")

    # Modify codeml.ctl in place
    ctl_path = species_output / "codeml.ctl"
    with open(ctl_path, "r") as f:
        lines = f.readlines()

    with open(ctl_path, "w") as f:
        for line in lines:
            if line.strip().startswith("seqfile"):
                f.write("seqfile = aligned.fas\n")
            elif line.strip().startswith("treefile"):
                f.write("treefile = treefile.treefile\n")
            elif line.strip().startswith("model"):
                f.write("model = 0\n")
            elif line.strip().startswith("NSsites"):
                f.write("NSsites = 0\n")
            else:
                f.write(line)

    # Run codeml inside M0 folder
    m0_folder = species_output / "M0"
    m0_folder.mkdir(exist_ok=True)

    shutil.copy(ctl_path, m0_folder / "M0.ctl")
    shutil.copy(species_output / "aligned.fas", m0_folder / "aligned.fas")
    shutil.copy(species_output / "treefile.treefile", m0_folder / "treefile.treefile")

    print(f"Processing M0 model for {species}")
    subprocess.run(["codeml", "M0.ctl"], cwd=m0_folder, check=True)
    print(f"Completed M0 model for {species}")

# ---------------------------------------------------------------------------
# Detect blocks
species_files = list(msa_parent_dir.glob("*/*.fas"))  # look inside subfolders
num_parallel = len(species_files)
print(f"Detected {num_parallel} blocks. Running all in parallel.")

# ---------------------------------------------------------------------------
# Run in parallel
with multiprocessing.Pool(processes=num_parallel) as pool:
    pool.map(process_species, species_files)

print("All M0 model processing completed.")
