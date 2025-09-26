#!/usr/bin/env python3
"""
script_phylo_auto.py - Run IQ-TREE2 phylogenetic analysis and foreground branch selection
on MSA files in parallel, automatically detecting CPU cores for job assignment.
"""

import os
import glob
import shutil
import subprocess
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import sys, io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ------------------ Setup Output Directories ------------------------------
os.makedirs("iqtreeoutput", exist_ok=True)
os.makedirs("treefiles", exist_ok=True)
os.makedirs("foregroundbranch", exist_ok=True)

# ------------------ Automatic Parallel Job Selection ----------------------
TOTAL_CORES = multiprocessing.cpu_count()
# Leave 2 cores free for system responsiveness
PARALLEL_IQTREE_JOBS = max(1, TOTAL_CORES - 2)
PARALLEL_JOBS = max(1, TOTAL_CORES - 2)

print(f"Detected {TOTAL_CORES} CPU cores → using {PARALLEL_IQTREE_JOBS} IQ-TREE jobs and {PARALLEL_JOBS} foreground jobs.")

# ------------------ IQ-TREE2 Section --------------------------------------
msa_files = glob.glob("msa/*_msa.best.fas")
if not msa_files:
    print("No MSA files found for IQ-TREE2. Skipping phylogenetic analysis.")
    exit(1)

def run_iqtree(file: str):
    gene_name = os.path.basename(file).replace("_msa.best.fas", "")
    output_folder = os.path.join("iqtreeoutput", gene_name)
    os.makedirs(output_folder, exist_ok=True)
    log_file = os.path.join(output_folder, f"{gene_name}_iqtree.log")

    cmd = [
        "iqtree2",
        "-s", file,
        "-st", "CODON",
        "-B", "1000",
        "-alrt", "1000",
        "-bnni",
        "-T", "AUTO",
        "-pre", os.path.join(output_folder, gene_name)
    ]

    try:
        with open(log_file, "w") as log:
            subprocess.run(cmd, stdout=log, stderr=log, check=True)
        print(f"✔ IQ-TREE2 finished: {file}")
    except subprocess.CalledProcessError:
        print(f"❌ IQ-TREE2 failed: {file}")

with ThreadPoolExecutor(max_workers=PARALLEL_IQTREE_JOBS) as exe:
    list(exe.map(run_iqtree, msa_files))

print("✅ IQ-TREE2 Step Completed.")

# ------------------ Tree File Collection Section --------------------------
for treefile in glob.glob("iqtreeoutput/**/*.treefile", recursive=True):
    shutil.copy(treefile, "treefiles")

print("All tree files copied to treefiles/.")

# ------------------ Foreground Branch Selection Section --------------------
tree_files = glob.glob("treefiles/*.treefile")

def run_foreground_branch(treefile: str):
    gene_name = os.path.basename(treefile).replace(".treefile", "")
    output_folder = os.path.join("foregroundbranch", gene_name)
    os.makedirs(output_folder, exist_ok=True)

    cmd = ["python3", "4GroundBranchGenerator.py", treefile, output_folder]
    try:
        subprocess.run(cmd, check=True)
        print(f"✔ Foreground branch selection completed: {treefile}")
    except subprocess.CalledProcessError:
        print(f"❌ Foreground branch selection failed: {treefile}")

with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as exe:
    list(exe.map(run_foreground_branch, tree_files))

print("✅ Foreground Branch Selection Completed.")
