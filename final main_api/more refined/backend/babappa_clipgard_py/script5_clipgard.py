#!/usr/bin/env python3
"""
script5.py - Extract lnL and np values from PAML codeml outputs
             for branch and branch-site models and save as CSV.
"""

import os
import csv
import re
from pathlib import Path

# ----------------------------
# Set up input and output directories
# ----------------------------
input_dir = Path("codemloutput")
output_dir = Path("codemlanalysis")
output_dir.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Iterate through all species directories
# ----------------------------
for species_path in input_dir.iterdir():
    if not species_path.is_dir():
        continue
    species_name = species_path.name

    for analysis_path in species_path.iterdir():
        if not analysis_path.is_dir():
            continue
        analysis_name = analysis_path.name
        output_file_path = analysis_path / "output.txt"

        # ----------------------------
        # Check if output.txt exists
        # ----------------------------
        if output_file_path.is_file():
            # Read the file and look for lnL(ntime ...) line
            with open(output_file_path) as f:
                lines = f.readlines()

            lnL_np_line = None
            for line in lines:
                if "lnL(ntime" in line:
                    lnL_np_line = line.strip()
                    break

            if lnL_np_line:
                # ----------------------------
                # Extract lnL and np values
                # ----------------------------
                # lnL is typically the 5th column (0-indexed 4)
                parts = lnL_np_line.split()
                lnL = parts[4] if len(parts) >= 5 else ""

                # np is after 'np:' and before ')'
                np_match = re.search(r"np:\s*(\d+)", lnL_np_line)
                np_value = np_match.group(1) if np_match else ""

                # ----------------------------
                # Organize CSV output
                # ----------------------------
                species_output_dir = output_dir / species_name
                species_output_dir.mkdir(parents=True, exist_ok=True)
                csv_file = species_output_dir / "lnL_np_values.csv"

                # Initialize CSV with headers if not exists
                if not csv_file.exists():
                    with open(csv_file, "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Analysis", "lnL", "np"])

                # Append values
                with open(csv_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([analysis_name, lnL, np_value])

print(f"Extraction complete. Results saved in {output_dir}.")
