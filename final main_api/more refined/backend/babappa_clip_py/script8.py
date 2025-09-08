#!/usr/bin/env python3
"""
script_BH_sitemodel.py - Apply Benjamini-Hochberg correction on codeml site-model CSVs.
Processes species directories in 'sitemodelanalysis', runs 'lrt_bh_correction.sitemodel.py',
and moves results to 'BHanalysis4sitemodel/<species>/'.
"""

import subprocess
from pathlib import Path
import shutil

# ----------------------------
# Define directories
# ----------------------------
base_dir = Path.cwd()
site_model_dir = base_dir / "sitemodelanalysis"
bh_analysis_dir = base_dir / "BHanalysis4sitemodel"
bh_analysis_dir.mkdir(parents=True, exist_ok=True)

python_script = base_dir / "lrt_bh_correction.sitemodel.py"

# ----------------------------
# Iterate through species directories
# ----------------------------
for species_dir in site_model_dir.iterdir():
    if not species_dir.is_dir():
        continue

    species = species_dir.name
    output_dir = bh_analysis_dir / species
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find the first CSV file in the species directory
    csv_files = list(species_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV file found in {species_dir}")
        continue

    csv_file = csv_files[0]
    print(f"Processing {csv_file} for species {species}")

    # Run the BH correction Python script
    try:
        subprocess.run(
            ["python3", str(python_script), str(csv_file)],
            check=True
        )
    except subprocess.CalledProcessError:
        print(f"❌ BH correction failed for {species}")
        continue

    # Move the generated output file to the species output directory
    output_file = base_dir / "lrt_results.csv"
    if output_file.is_file():
        shutil.move(str(output_file), output_dir / output_file.name)
    else:
        print(f"Error: No output file generated for {species}")

print("BH correction for site models completed.")
