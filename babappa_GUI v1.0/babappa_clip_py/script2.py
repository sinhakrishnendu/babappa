#!/usr/bin/env python3
"""
script2_verbose.py
Runs codeml (PAML) in parallel across multiple species and multiple treefiles per species.
This version provides real-time logging and shows stdout/stderr for each codeml run.
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
inner_parallel = None  # None = auto-detect cores

msa_dir = "msa"
tree_dir = "foregroundbranch"
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
inner_parallel = inner_parallel or max(1, total_cores // 2)
print(f"[INFO] Detected {total_cores} CPU cores. Using {num_parallel} species in parallel, "
      f"{inner_parallel} treefiles per species.")


# ------------------- Helpers ------------------- #
def run_command(cmd, cwd=None):
    """Run a shell command safely and print stdout/stderr."""
    print(f"[CMD] {cmd} (cwd={cwd})")
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=cwd,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        print(result.stdout)
        if result.stderr.strip():
            print("[STDERR]", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {cmd}\n{e}")
        print("[STDOUT]", e.stdout)
        print("[STDERR]", e.stderr)
        return False


def prepare_ctl(template_ctl, ctl_path, treefile, model, ns_sites, fix_omega=None, omega=None):
    """Prepare a codeml control file."""
    shutil.copy(template_ctl, ctl_path)
    with open(ctl_path, "r") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("seqfile"):
            new_lines.append("seqfile = aligned.fas\n")
        elif line.strip().startswith("treefile"):
            new_lines.append(f"treefile = {treefile}\n")
        elif line.strip().startswith("model"):
            new_lines.append(f"model = {model}\n")
        elif line.strip().startswith("NSsites"):
            new_lines.append(f"NSsites = {ns_sites}\n")
        elif fix_omega is not None and line.strip().startswith("fix_omega"):
            new_lines.append(f"fix_omega = {fix_omega}\n")
        elif omega is not None and line.strip().startswith("omega"):
            new_lines.append(f"omega = {omega}\n")
        else:
            new_lines.append(line)
    with open(ctl_path, "w") as f:
        f.writelines(new_lines)


def run_codeml_for_treefile(treefile, species_output, base_name):
    """Run codeml for a single treefile with branch, branch-site, and null models."""
    msa_file = "aligned.fas"
    print(f"[INFO] Starting treefile {treefile} in {species_output}")

    models = [
        ("B", 2, 0, None, None),
        ("BS", 2, 2, None, None),
        ("BS_NULL", 2, 2, 1, 1)
    ]

    for suffix, model, ns_sites, fix_omega, omega in models:
        folder = os.path.join(species_output, f"{base_name}_{suffix}")
        os.makedirs(folder, exist_ok=True)
        ctl_path = os.path.join(folder, f"{base_name}.{suffix}.ctl")
        prepare_ctl(base_ctl_file, ctl_path, treefile, model, ns_sites, fix_omega, omega)
        shutil.copy(os.path.join(species_output, msa_file), folder)
        shutil.copy(os.path.join(species_output, treefile), folder)
        print(f"[INFO] Running codeml for {treefile} model {suffix}")
        run_command(f"codeml {os.path.basename(ctl_path)}", cwd=folder)

    print(f"[INFO] Finished treefile {treefile} in {species_output}")


def process_species(species):
    """Process all treefiles for one species."""
    species_output = os.path.join(output_dir, species)
    species_tree_dir = os.path.join(tree_dir, species)
    os.makedirs(species_output, exist_ok=True)

    msa_file_list = glob.glob(os.path.join(msa_dir, f"{species}_msa.best.fas"))
    if not msa_file_list:
        print(f"[WARN] MSA file for {species} not found. Skipping...")
        return
    msa_file = msa_file_list[0]
    shutil.copy(msa_file, os.path.join(species_output, "aligned.fas"))
    shutil.copy(base_ctl_file, species_output)

    if not os.path.isdir(species_tree_dir):
        print(f"[WARN] Tree directory for {species} not found. Skipping...")
        return

    # Copy all treefiles into species output folder
    treefiles = glob.glob(os.path.join(species_tree_dir, "*.treefile"))
    for treefile in treefiles:
        shutil.copy(treefile, species_output)

    # Now run codeml for each treefile in parallel (inner)
    treefiles_local = [os.path.basename(t) for t in treefiles]
    futures = []
    with ThreadPoolExecutor(max_workers=inner_parallel) as exe:
        for tf in treefiles_local:
            base_name = tf.replace(".treefile", "")
            futures.append(exe.submit(run_codeml_for_treefile, tf, species_output, base_name))
        for _ in as_completed(futures):
            pass

    print(f"[INFO] Completed processing for {species}")


# ------------------- Main ------------------- #
if __name__ == "__main__":
    species_list = [os.path.basename(f).replace("_msa.best.fas", "")
                    for f in glob.glob(os.path.join(msa_dir, "*_msa.best.fas"))]
    print(f"[INFO] Found {len(species_list)} species: {species_list}")

    with ThreadPoolExecutor(max_workers=num_parallel) as exe:
        futures = {exe.submit(process_species, sp): sp for sp in species_list}
        for f in as_completed(futures):
            sp = futures[f]
            try:
                f.result()
            except Exception as e:
                print(f"[ERROR] Species {sp} failed: {e}")

    print("[INFO] All species processing completed.")
