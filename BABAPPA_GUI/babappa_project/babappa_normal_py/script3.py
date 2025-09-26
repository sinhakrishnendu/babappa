#!/usr/bin/env python3
"""
script1_m0.py
Runs codeml M0 model in parallel for multiple species.
"""

import os
import glob
import shutil
import subprocess
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys, io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ------------------- Config ------------------- #
num_parallel = None  # None = auto-detect cores
msa_dir = "msa"
tree_dir = "treefiles"
output_dir = "codemloutput"
base_ctl_file = "codeml.ctl"

# Verify critical directories/files exist
for path in [msa_dir, tree_dir, base_ctl_file]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file or directory not found: {path}")

os.makedirs(output_dir, exist_ok=True)

# Auto-detect cores
total_cores = multiprocessing.cpu_count()
num_parallel = num_parallel or max(1, total_cores // 2)
print(f"[INFO] Detected {total_cores} CPU cores. Using {num_parallel} species in parallel for M0.")


# ------------------- Helpers ------------------- #
def run_command(cmd, cwd=None):
    """Run a shell command and capture output."""
    print(f"[CMD] {cmd} (cwd={cwd})")
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=cwd,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout.strip():
            print(result.stdout)
        if result.stderr.strip():
            print("[STDERR]", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {cmd}\n{e}")
        print("[STDOUT]", e.stdout)
        print("[STDERR]", e.stderr)
        return False


def prepare_ctl(template_ctl, ctl_path, seqfile, treefile, model=0, ns_sites=0):
    """Prepare a codeml control file for M0 model."""
    shutil.copy(template_ctl, ctl_path)
    with open(ctl_path, "r") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("seqfile"):
            new_lines.append(f"seqfile = {seqfile}\n")
        elif line.strip().startswith("treefile"):
            new_lines.append(f"treefile = {treefile}\n")
        elif line.strip().startswith("model"):
            new_lines.append(f"model = {model}\n")
        elif line.strip().startswith("NSsites"):
            new_lines.append(f"NSsites = {ns_sites}\n")
        else:
            new_lines.append(line)
    with open(ctl_path, "w") as f:
        f.writelines(new_lines)


def process_species(species):
    """Process one species: prepare files and run M0 model."""
    species_output = os.path.join(output_dir, species)
    os.makedirs(species_output, exist_ok=True)

    # Find MSA and tree files
    msa_file_list = glob.glob(os.path.join(msa_dir, f"{species}_msa.best.fas"))
    tree_file_list = glob.glob(os.path.join(tree_dir, f"{species}.treefile"))

    if not msa_file_list:
        print(f"[WARN] MSA file for {species} not found. Skipping...")
        return
    if not tree_file_list:
        print(f"[WARN] Tree file for {species} not found. Skipping...")
        return

    msa_file = msa_file_list[0]
    tree_file = tree_file_list[0]

    # Copy files to species output folder
    shutil.copy(msa_file, os.path.join(species_output, "aligned.fas"))
    shutil.copy(tree_file, os.path.join(species_output, "treefile.treefile"))
    shutil.copy(base_ctl_file, species_output)

    # Prepare control file in M0 folder
    m0_folder = os.path.join(species_output, "M0")
    os.makedirs(m0_folder, exist_ok=True)
    ctl_path = os.path.join(m0_folder, "M0.ctl")
    prepare_ctl(base_ctl_file, ctl_path, "aligned.fas", "treefile.treefile")

    # Copy inputs into M0 folder
    shutil.copy(os.path.join(species_output, "aligned.fas"), m0_folder)
    shutil.copy(os.path.join(species_output, "treefile.treefile"), m0_folder)

    # Run codeml
    print(f"[INFO] Running M0 model for {species}")
    run_command(f"codeml {os.path.basename(ctl_path)}", cwd=m0_folder)
    print(f"[INFO] Completed M0 model for {species}")


# ------------------- Main ------------------- #
if __name__ == "__main__":
    # List species from MSA files
    species_list = [os.path.basename(f).replace("_msa.best.fas", "")
                    for f in glob.glob(os.path.join(msa_dir, "*_msa.best.fas"))]
    print(f"[INFO] Found {len(species_list)} species: {species_list}")

    # Process species in parallel
    with ThreadPoolExecutor(max_workers=num_parallel) as exe:
        futures = {exe.submit(process_species, sp): sp for sp in species_list}
        for f in as_completed(futures):
            sp = futures[f]
            try:
                f.result()
            except Exception as e:
                print(f"[ERROR] Species {sp} failed: {e}")

    print("[INFO] All M0 model processing completed.")
