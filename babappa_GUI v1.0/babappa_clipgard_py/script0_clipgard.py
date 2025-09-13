#!/usr/bin/env python3
"""
Pipeline: QC → PRANK MSA → ClipKit trimming → Stop/N masking
Replaces the original .sh script with a Python version.
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
def run_command(cmd, logfile=None):
    """Run a shell command, optionally saving stdout/stderr to a log file."""
    try:
        if logfile:
            with open(logfile, "w") as log:
                subprocess.run(cmd, shell=True, check=True, stdout=log, stderr=subprocess.STDOUT)
        else:
            subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {cmd}\n{e}")
        return False
    return True


# ------------------ QC Step ------------------ #
def run_qc(file):
    output_file = os.path.join("QCseq", os.path.splitext(os.path.basename(file))[0] + "_QC.fasta")
    print(f"Running QC on {file}...")
    ok = run_command(f"python3 seqQC.py {file} {output_file}")
    if ok:
        print(f"QC Passed: {file} -> {output_file}")
    else:
        print(f"QC Failed: {file}")
    return output_file if ok else None


# ------------------ PRANK Step ------------------ #
def run_prank(file):
    prefix = os.path.join("msa", os.path.splitext(os.path.basename(file))[0] + "_msa")
    log_file = prefix + ".log"
    print(f"Running PRANK on {file}...")
    run_command(f"prank -d={file} -o={prefix} -codon", logfile=log_file)
    return prefix + ".best.fas"


# ------------------ ClipKit Step ------------------ #
def run_clipkit(file):
    tmp_output = file.replace(".best.fas", "_clipkit_temp.fas")
    log_file = file.replace(".best.fas", "_clipkit.log")

    print(f"Trimming MSA with ClipKit smart-gap codon model: {file}")
    run_command(f"clipkit {file} -m smart-gap --codon -o {tmp_output}", logfile=log_file)

    # overwrite input with trimmed version
    os.replace(tmp_output, file)
    print(f"ClipKit log saved to: {log_file}")
    return file


# ------------------ Stop/N Masking ------------------ #
def run_mask(file):
    print(f"Masking internal stop/ambiguous codons: {file}")
    run_command(f"python3 babappa_stopcodon_masker.py {file} {file}")
    return file


# ------------------ Main ------------------ #
def main():
    os.makedirs("QCseq", exist_ok=True)
    os.makedirs("msa", exist_ok=True)

    # find input fasta files
    input_files = glob.glob("*.fasta") + glob.glob("*.fas") + glob.glob("*.fa")
    if not input_files:
        print("No input files found in the directory!")
        return

    # detect available cores
    parallel_jobs = multiprocessing.cpu_count()
    print(f"Detected {parallel_jobs} CPU cores → running jobs in parallel.")

    # ---------- Step 1: QC ----------
    with ThreadPoolExecutor(max_workers=parallel_jobs) as exe:
        qc_results = list(exe.map(run_qc, input_files))
    qc_files = [f for f in qc_results if f]
    print("QC Step Completed.")

    # ---------- Step 2: PRANK ----------
    with ThreadPoolExecutor(max_workers=parallel_jobs) as exe:
        prank_results = list(exe.map(run_prank, qc_files))
    prank_files = [f for f in prank_results if os.path.exists(f)]
    print("MSA Step Completed.")

    # ---------- Step 3: ClipKit ----------
    with ThreadPoolExecutor(max_workers=parallel_jobs) as exe:
        list(exe.map(run_clipkit, prank_files))
    print("ClipKit trimming completed. Trimmed MSAs and logs are ready in msa/")

    # ---------- Step 4: Stop/N Masking ----------
    with ThreadPoolExecutor(max_workers=parallel_jobs) as exe:
        list(exe.map(run_mask, prank_files))
    print("Internal stop/ambiguous codon masking completed. Corrected MSAs are ready in msa/")

    print("Script0 completed. Proceed with Script0.5 onwards for phylogenetic and selection analysis.")


if __name__ == "__main__":
    main()
