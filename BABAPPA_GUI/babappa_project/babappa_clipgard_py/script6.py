#!/usr/bin/env python3
import re
import csv
from pathlib import Path

def parse_output_file(output_file: Path, csv_file: Path):
    models = []
    lnL_values = []
    np_values = []

    with open(output_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    current_model = None
    for line in lines:
        # Detect NSsites Model lines
        match_model = re.match(r"^\s*NSsites Model (\d+):", line)
        if match_model:
            current_model = f"Model {match_model.group(1)}"
            continue

        # Detect lnL line after a model
        if current_model:
            match_lnL = re.search(r"lnL\(.*np:\s*(\d+)\):\s*([-0-9.]+)", line)
            if match_lnL:
                np_val = match_lnL.group(1)
                lnL_val = match_lnL.group(2)

                models.append(current_model)
                np_values.append(np_val)
                lnL_values.append(lnL_val)

                current_model = None  # reset until next Model line

    # Write CSV
    with open(csv_file, "w", newline="", encoding="utf-8") as csv_out:
        writer = csv.writer(csv_out)
        writer.writerow(["Model", "np", "lnL"])
        for m, npv, lnLv in zip(models, np_values, lnL_values):
            writer.writerow([m, npv, lnLv])

    print(f"Extraction complete. Results saved to {csv_file}")

def main():
    # Path setup
    base_dir = Path("sitemodelanalysis")
    base_dir.mkdir(exist_ok=True)

    # Assume each site model run has an output.txt inside sitemodel/*/
    for sm_dir in Path("sitemodel").iterdir():
        if sm_dir.is_dir():
            output_file = sm_dir / "output.txt"
            if not output_file.exists():
                print(f"Warning: {output_file} not found, skipping.")
                continue

            out_csv_dir = base_dir / sm_dir.name
            out_csv_dir.mkdir(parents=True, exist_ok=True)
            csv_file = out_csv_dir / "lnL_np_values.csv"

            parse_output_file(output_file, csv_file)

if __name__ == "__main__":
    main()
