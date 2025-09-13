#!/usr/bin/env python3
"""
script4.py - Codeml site model automator
Automatically matches MSA files ending with '_msa.best.fas' to their corresponding treefiles.
"""

import os
import glob
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys, io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ------------------- Config ------------------- #
msa_dir = "msa"
tree_dir = "treefiles"
output_dir = "sitemodel"
base_ctl_file = "codeml.ctl"
max_parallel = 8  # max concurrent codeml runs

# Verify prerequisites
if not os.path.isfile(base_ctl_file):
    raise FileNotFoundError(f"Base control file '{base_ctl_file}' not found.")
os.makedirs(output_dir, exist_ok=True)

# ------------------- Helpers ------------------- #
def run_command(cmd, cwd=None):
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


def prepare_ctl(template_ctl, ctl_path, msa_file_name, tree_file_name):
    shutil.copy(template_ctl, ctl_path)
    with open(ctl_path, "r") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("seqfile"):
            new_lines.append(f"seqfile = {msa_file_name}\n")
        elif line.strip().startswith("treefile"):
            new_lines.append(f"treefile = {tree_file_name}\n")
        elif line.strip().startswith("model"):
            new_lines.append("model = 0\n")
        elif line.strip().startswith("NSsites"):
            new_lines.append("NSsites = 0 1 2 3 7 8\n")
        else:
            new_lines.append(line)
    with open(ctl_path, "w") as f:
        f.writelines(new_lines)


def process_species(msa_file_path):
    species = os.path.basename(msa_file_path).replace(".fas", "")
    # Automatically strip "_msa.best" if present to find the correct tree file
    tree_base_name = species.replace("_msa.best", "")
    tree_file = os.path.join(tree_dir, f"{tree_base_name}.treefile")

    if not os.path.isfile(tree_file):
        print(f"[WARN] Tree file for {species} not found. Skipping.")
        return

    species_output = os.path.join(output_dir, species)
    os.makedirs(species_output, exist_ok=True)

    # Copy files into species folder
    shutil.copy(msa_file_path, species_output)
    shutil.copy(tree_file, species_output)
    shutil.copy(base_ctl_file, species_output)

    ctl_file = os.path.join(species_output, "codeml.ctl")
    prepare_ctl(base_ctl_file, ctl_file, os.path.basename(msa_file_path), os.path.basename(tree_file))

    print(f"[INFO] Running codeml for {species} (Site Models: 0, 1, 2, 3, 7, 8)")
    run_command(f"codeml {os.path.basename(ctl_file)}", cwd=species_output)
    print(f"[INFO] Completed: {species}")


# ------------------- Main ------------------- #
if __name__ == "__main__":
    msa_files = glob.glob(os.path.join(msa_dir, "*.fas"))
    if not msa_files:
        print(f"[WARN] No MSA files found in {msa_dir}")
    else:
        with ThreadPoolExecutor(max_workers=max_parallel) as exe:
            futures = {exe.submit(process_species, msa): msa for msa in msa_files}
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    species_name = os.path.basename(futures[f])
                    print(f"[ERROR] Species {species_name} failed: {e}")

    print("✅ All site model analyses completed successfully!")
