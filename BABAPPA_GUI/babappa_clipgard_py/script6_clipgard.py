#!/usr/bin/env python3
"""
script_sitemodel.py - Extract lnL and np values from sitemodel PAML outputs
                      and save as CSV files organized by species.
"""

import os
import csv
import re
from pathlib import Path
import sys, io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ----------------------------
# Set up input and output directories
# ----------------------------
input_dir = Path("sitemodel")
output_dir = Path("sitemodelanalysis")
output_dir.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Iterate over species subdirectories
# ----------------------------
for species_path in input_dir.iterdir():
    if not species_path.is_dir():
        continue

    species_name = species_path.name
    output_txt = species_path / "output.txt"

    if output_txt.is_file():
        species_output_dir = output_dir / species_name
        species_output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = species_output_dir / "lnL_np_values.csv"

        # Initialize CSV with header
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Model", "lnL", "np"])

            current_model = ""
            with open(output_txt) as infile:
                for line in infile:
                    line = line.strip()

                    # Detect model line (e.g., "Model 1")
                    model_match = re.match(r"^Model\s+\d+", line)
                    if model_match:
                        current_model = model_match.group(0)

                    # Detect lnL line
                    if "lnL(ntime" in line:
                        parts = line.split()
                        lnL = parts[4] if len(parts) >= 5 else ""

                        # Extract np using regex
                        np_match = re.search(r"np:\s*(\d+)", line)
                        np_value = np_match.group(1) if np_match else ""

                        writer.writerow([current_model, lnL, np_value])

print(f"Extraction complete. Results saved in {output_dir}.")
