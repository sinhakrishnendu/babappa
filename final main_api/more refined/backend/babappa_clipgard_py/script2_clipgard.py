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
tree_dir = "foregroundbranch"
output_dir = "codemloutput"
base_ctl_file = "codeml.ctl"

# Detect number of CPU cores
TOTAL_CORES = max(1, multiprocessing.cpu_count() - 1)
print(f"[INFO] Total cores detected: {multiprocessing.cpu_count()}, using {TOTAL_CORES}")

# You can adjust outer vs inner parallelism here
outer_parallel = TOTAL_CORES  # species-level
inner_parallel = TOTAL_CORES  # treefile-level per species

# -----------------------------
# UTILITIES
# -----------------------------
def modify_ctl_file(ctl_path, treefile, model, ns_sites=None, fix_omega=None, omega=None):
    """Modify control file in-place"""
    with open(ctl_path, "r") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("treefile"):
            new_lines.append(f"treefile = {treefile}\n")
        elif line.strip().startswith("model"):
            new_lines.append(f"model = {model}\n")
        elif ns_sites is not None and line.strip().startswith("NSsites"):
            new_lines.append(f"NSsites = {ns_sites}\n")
        elif fix_omega is not None and line.strip().startswith("fix_omega"):
            new_lines.append(f"fix_omega = {fix_omega}\n")
        elif omega is not None and line.strip().startswith("omega"):
            new_lines.append(f"omega = {omega}\n")
        else:
            new_lines.append(line)
    with open(ctl_path, "w") as f:
        f.writelines(new_lines)

def run_codeml_for_treefile(treefile, species, species_output):
    """Run Branch, Branch-Site, and Null models for a single treefile"""
    os.chdir(species_output)
    msa_file = "aligned.fas"
    base_name = os.path.splitext(treefile)[0]
    models = [
        ("Branch", f"{base_name}_B", 2, 0, None, None),
        ("Branch-Site", f"{base_name}_BS", 2, 2, None, None),
        ("Null", f"{base_name}_BS_NULL", 2, 2, 1, 1),
    ]
    for model_name, folder, model, ns_sites, fix_omega, omega in models:
        os.makedirs(folder, exist_ok=True)
        ctl_dest = os.path.join(folder, f"{base_name}.{model_name}.ctl")
        shutil.copy("codeml.ctl", ctl_dest)
        modify_ctl_file(ctl_dest, treefile, model, ns_sites, fix_omega, omega)
        shutil.copy(msa_file, folder)
        shutil.copy(treefile, folder)
        print(f"[INFO] Running codeml: {species} - {treefile} - {model_name}")
        subprocess.run(["codeml", ctl_dest], check=True)
    print(f"[DONE] Finished {treefile} in {species}")

def process_species(species):
    """Prepare species folder and run codeml for all treefiles"""
    species_output = os.path.join(output_dir, species)
    species_tree_dir = os.path.join(tree_dir, species)
    
    msa_file = None
    for f in os.listdir(msa_dir):
        if f.startswith(species) and f.endswith(".fas"):
            msa_file = os.path.join(msa_dir, f)
            break
    if not msa_file or not os.path.exists(msa_file):
        print(f"[WARN] MSA file for {species} not found. Skipping.")
        return
    if not os.path.isdir(species_tree_dir):
        print(f"[WARN] Tree directory for {species} not found. Skipping.")
        return

    os.makedirs(species_output, exist_ok=True)
    shutil.copy(msa_file, os.path.join(species_output, "aligned.fas"))
    shutil.copy(base_ctl_file, species_output)
    
    treefiles = [f for f in os.listdir(species_tree_dir) if f.endswith(".treefile")]
    for tf in treefiles:
        shutil.copy(os.path.join(species_tree_dir, tf), species_output)

    # Inner parallelization for treefiles
    futures = []
    with ThreadPoolExecutor(max_workers=inner_parallel) as executor:
        for tf in treefiles:
            futures.append(executor.submit(run_codeml_for_treefile, tf, species, species_output))
        for f in as_completed(futures):
            f.result()
    print(f"[DONE] Completed all treefiles for {species}")

# -----------------------------
# MAIN EXECUTION
# -----------------------------
os.makedirs(output_dir, exist_ok=True)
species_list = [os.path.splitext(f)[0] for f in os.listdir(msa_dir) if f.endswith(".fas")]

# Outer parallelization for species
futures = []
with ThreadPoolExecutor(max_workers=outer_parallel) as executor:
    for species in species_list:
        futures.append(executor.submit(process_species, species))
    for f in as_completed(futures):
        f.result()

print("[ALL DONE] All species processing completed.")
