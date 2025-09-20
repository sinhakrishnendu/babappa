#!/usr/bin/env python3
"""
script1.py - Run IQ-TREE2 and foreground branch selection on recombination
             block alignments, using multiprocessing for parallel jobs.
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
# ------------------ Setup Output Directories ------------------------------
os.makedirs("iqtreeoutput", exist_ok=True)
os.makedirs("treefiles", exist_ok=True)
os.makedirs("foregroundbranch", exist_ok=True)

# ------------------ Detect Number of CPUs ---------------------------------
TOTAL_CORES = multiprocessing.cpu_count()
PARALLEL_IQTREE_JOBS = int(os.environ.get("PARALLEL_IQTREE_JOBS", TOTAL_CORES))
PARALLEL_JOBS = int(os.environ.get("PARALLEL_JOBS", TOTAL_CORES))

print(f"Detected {TOTAL_CORES} cores → using {PARALLEL_IQTREE_JOBS} IQ-TREE jobs and {PARALLEL_JOBS} foreground jobs.")

# ------------------ IQ-TREE2 Section --------------------------------------
msa_files = glob.glob("recombination_blocks/**/*.fas", recursive=True)

if not msa_files:
    print("❌ No recombination block FASTA files found for IQ-TREE2. Exiting.")
    exit(1)


def run_iqtree(file: str):
    basename = os.path.splitext(os.path.basename(file))[0]
    parentdir = os.path.basename(os.path.dirname(file))
    output_folder = os.path.join("iqtreeoutput", parentdir, basename)
    os.makedirs(output_folder, exist_ok=True)

    log_file = os.path.join(output_folder, f"{basename}_iqtree.log")

    cmd = [
        "iqtree2",
        "-s", file,
        "-st", "CODON",
        "-B", "1000",
        "-alrt", "1000",
        "-bnni",
        "-T", "AUTO",
        "-pre", os.path.join(output_folder, basename),
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

print("📂 All tree files copied to treefiles/.")

# ------------------ Foreground Branch Selection ---------------------------
tree_files = glob.glob("treefiles/*.treefile")

if not tree_files:
    print("⚠ No .treefile files found in treefiles/. Exiting foreground branch step.")
    exit(0)


def run_foreground_branch(treefile: str):
    gene_name = os.path.splitext(os.path.basename(treefile))[0]
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
