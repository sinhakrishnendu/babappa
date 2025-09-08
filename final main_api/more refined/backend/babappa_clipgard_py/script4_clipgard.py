#!/usr/bin/env python3
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# -----------------------------
# CONFIGURATION
# -----------------------------
msa_dir = "msa"
tree_dir = "treefiles"
output_dir = "sitemodel"
base_ctl_file = "codeml.ctl"

# Detect cores and set parallelism
TOTAL_CORES = max(1, multiprocessing.cpu_count() - 1)
print(f"[INFO] Total cores detected: {multiprocessing.cpu_count()}, using {TOTAL_CORES} parallel codeml jobs")

# Limit for background jobs
parallel_jobs = min(TOTAL_CORES, 8)

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def modify_ctl_file(ctl_path, seqfile, treefile, model=0, ns_sites="0 1 2 3 7 8"):
    """Modify the codeml control file for site models"""
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

def process_species(msa_file):
    """Process a single species for site models"""
    species = os.path.splitext(os.path.basename(msa_file))[0]
    tree_file = os.path.join(tree_dir, f"{species}.treefile")
    
    if not os.path.isfile(tree_file):
        print(f"[WARN] Tree file for {species} not found. Skipping.")
        return
    
    species_output = os.path.join(output_dir, species)
    os.makedirs(species_output, exist_ok=True)
    
    shutil.copy(msa_file, species_output)
    shutil.copy(tree_file, species_output)
    shutil.copy(base_ctl_file, species_output)
    
    ctl_file = os.path.join(species_output, "codeml.ctl")
    modify_ctl_file(ctl_file, os.path.basename(msa_file), os.path.basename(tree_file))
    
    # Run codeml
    print(f"[INFO] Running codeml for {species} (Site Models 0,1,2,3,7,8)")
    subprocess.run(["codeml", ctl_file], cwd=species_output, check=True)
    print(f"[DONE] Completed: {species}")

# -----------------------------
# MAIN EXECUTION
# -----------------------------
os.makedirs(output_dir, exist_ok=True)

msa_files = [os.path.join(msa_dir, f) for f in os.listdir(msa_dir) if f.endswith(".fas")]

# Run species in parallel
with ThreadPoolExecutor(max_workers=parallel_jobs) as executor:
    futures = [executor.submit(process_species, msa) for msa in msa_files]
    for f in as_completed(futures):
        try:
            f.result()
        except Exception as e:
            print(f"[ERROR] {e}")

print("[ALL DONE] All site model analyses completed successfully!")
