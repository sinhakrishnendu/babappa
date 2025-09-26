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
    base_dir = Path('codemlanalysis')
    output_dir = Path('BHanalysis')
    ensure_dir(output_dir)
    python_script = Path.cwd()/'lrt_bh_correction.py'
    for species_dir in sorted(base_dir.glob('*/')):
        species_name = species_dir.name
        csv_file = next(species_dir.glob('*.csv'), None)
        if not csv_file:
            print('No CSV file found in', species_name, 'Skipping...')
            continue
        print('Processing', species_name)
        run(['bash','-lc', f'cd {species_dir} && python3 {python_script}'])
        excel_file = next(species_dir.glob('LRT_results_*.xlsx'), None)
        if excel_file:
            ensure_dir(output_dir/species_name)
            shutil.move(str(excel_file), str(output_dir/species_name/excel_file.name))
            print('Results moved to', output_dir/species_name)
        else:
            print('No Excel file generated for', species_name)
    print('Batch processing completed.')

if __name__ == '__main__':
    main()
