#!/usr/bin/env python3
"""Auto-converted from the user's shell script; aim to keep logic unchanged."""
import os
import sys
import io
import shutil
import subprocess
import multiprocessing
from pathlib import Path

# Force stdout/stderr to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

def run(cmd, check=True, capture_output=False, **kwargs):
    print('▶', ' '.join(cmd) if isinstance(cmd, (list,tuple)) else cmd)
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=True, **kwargs)

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def cpu_count():
    try:
        return multiprocessing.cpu_count()
    except Exception:
        return 1

def main():
    BASE_DIR = Path.cwd()
    SITE_MODEL_DIR = BASE_DIR/'sitemodelanalysis'
    BH_ANALYSIS_DIR = BASE_DIR/'BHanalysis4sitemodel'
    ensure_dir(BH_ANALYSIS_DIR)
    for species_dir in sorted(SITE_MODEL_DIR.glob('*/')):
        species = species_dir.name
        output_dir = BH_ANALYSIS_DIR/species
        ensure_dir(output_dir)
        csv_file = next(species_dir.glob('*.csv'), None)
        if csv_file:
            print('Processing', csv_file, 'for species', species)
            run(['python3', str(BASE_DIR/'lrt_bh_correction.sitemodel.py'), str(csv_file)])
            if (BASE_DIR/'lrt_results.csv').exists():
                shutil.move(str(BASE_DIR/'lrt_results.csv'), str(output_dir/'lrt_results.csv'))
            else:
                print('Error: No output file generated for', species)
        else:
            print('No CSV file found in', species_dir)

if __name__ == '__main__':
    main()
