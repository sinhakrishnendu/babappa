#!/usr/bin/env python3
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import sys, io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# -----------------------------
# CONFIGURATION
# -----------------------------
msa_dir = "msa"
tree_dir = "treefiles"
output_dir = "codemloutput"
base_ctl_file = "codeml.ctl"

# Detect number of CPU cores
TOTAL_CORES = max(1, multiprocessing.cpu_count() - 1)
print(f"[INFO] Total cores detected: {multiprocessing.cpu_count()}, using {TOTAL_CORES} for species-level parallelization")

outer_parallel = TOTAL_CORES  # species-level parallelism

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def modify_ctl_file(ctl_path, seqfile, treefile, model=0, ns_sites=0):
    """Modify the codeml control file for M0 model"""
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
    """Process a single species with M0 model"""
    species_output = os.path.join(output_dir, species)
    msa_file = os.path.join(msa_dir, f"{species}.fas")
    tree_file = None
    # Find tree file
    for f in os.listdir(tree_dir):
        if f.startswith(species) and f.endswith(".treefile"):
            tree_file = os.path.join(tree_dir, f)
            break

    if not os.path.isfile(msa_file):
        print(f"[WARN] MSA file for {species} not found. Skipping.")
        return
    if not tree_file or not os.path.isfile(tree_file):
        print(f"[WARN] Tree file for {species} not found. Skipping.")
        return

    os.makedirs(species_output, exist_ok=True)
    shutil.copy(msa_file, os.path.join(species_output, "aligned.fas"))
    shutil.copy(tree_file, os.path.join(species_output, "treefile.treefile"))
    shutil.copy(base_ctl_file, species_output)

    # Modify codeml.ctl
    ctl_path = os.path.join(species_output, "codeml.ctl")
    modify_ctl_file(ctl_path, "aligned.fas", "treefile.treefile", model=0, ns_sites=0)

    # Create M0 subfolder
    m0_folder = os.path.join(species_output, "M0")
    os.makedirs(m0_folder, exist_ok=True)
    shutil.copy(ctl_path, os.path.join(m0_folder, "M0.ctl"))
    shutil.copy(os.path.join(species_output, "aligned.fas"), m0_folder)
    shutil.copy(os.path.join(species_output, "treefile.treefile"), m0_folder)

    # Run codeml
    print(f"[INFO] Processing M0 model for {species}")
    subprocess.run(["codeml", "M0.ctl"], cwd=m0_folder, check=True)
    print(f"[DONE] Completed M0 model for {species}")

# -----------------------------
# MAIN EXECUTION
# -----------------------------
os.makedirs(output_dir, exist_ok=True)

# Get species list from msa_dir
species_list = [os.path.splitext(f)[0] for f in os.listdir(msa_dir) if f.endswith(".fas")]

# Parallel execution
with ThreadPoolExecutor(max_workers=outer_parallel) as executor:
    futures = [executor.submit(process_species, species) for species in species_list]
    for f in as_completed(futures):
        f.result()

print("[ALL DONE] All M0 model processing completed.")
