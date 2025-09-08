#!/usr/bin/env python3
"""
script_BH_correction.py - Apply Benjamini-Hochberg correction on branch and branch-site model CSVs.
Processes species directories in 'codemlanalysis', runs 'lrt_bh_correction.py', and moves Excel results to 'BHanalysis'.
"""

import os
import subprocess
from pathlib import Path
import shutil

# ----------------------------
# Define directories
# ----------------------------
base_dir = Path("codemlanalysis")
output_dir = Path("BHanalysis")
output_dir.mkdir(parents=True, exist_ok=True)

python_script = Path.cwd() / "lrt_bh_correction.py"

# ----------------------------
# Iterate through species directories
# ----------------------------
for species_dir in base_dir.iterdir():
    if not species_dir.is_dir():
        continue
    species_name = species_dir.name

    # Find CSV files in the species directory (depth 1)
    csv_files = list(species_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV file found in {species_name}. Skipping...")
        continue

    print(f"Processing {species_name}...")

    # Run the BH correction Python script in the species directory
    try:
        subprocess.run(
            ["python3", str(python_script)],
            cwd=species_dir,
            check=True
        )
    except subprocess.CalledProcessError:
        print(f"❌ BH correction failed for {species_name}. Skipping to next species.")
        continue

    # Find generated Excel file(s) matching the pattern
    excel_files = list(species_dir.glob("LRT_results_*.xlsx"))
    if excel_files:
        species_output_dir = output_dir / species_name
        species_output_dir.mkdir(parents=True, exist_ok=True)
        for excel_file in excel_files:
            shutil.move(str(excel_file), species_output_dir)
        print(f"Results moved to {species_output_dir}/")
    else:
        print(f"No Excel file generated for {species_name}.")

print("Batch processing completed.")

