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
    MSA_DIR = Path('msa')
    OUT_DIR = Path('gard_output')
    PY_SCRIPT = Path('split_recombination_blocks.py')

    ensure_dir(OUT_DIR)

    total = cpu_count()
    cores = max(1, total - 2) if total > 2 else 1
    print(f'Detected {total} CPU cores. Using {cores} for GARD.')

    files = sorted(MSA_DIR.glob('*msa.best.fas'))
    if not files:
        print(f'❌ No msa.best.fas files found in {MSA_DIR}/')
        sys.exit(1)

    # Run hyphy gard jobs in parallel using multiprocessing
    from concurrent.futures import ThreadPoolExecutor, as_completed
    def run_gard(f):
        base = f.stem
        out = OUT_DIR / f'{base}.gard.json'
        if out.exists():
            print(f'⏩ Skipping {f} (JSON already exists)')
            return
        print(f'▶ Running GARD on {f} ...')
        run(['hyphy', 'gard', '--alignment', str(f), '--type', 'codon', '--output', str(out)])
        print(f'✔ Finished {f} → {out}')

    with ThreadPoolExecutor(max_workers=cores) as ex:
        futures = [ex.submit(run_gard, f) for f in files]
        for fut in as_completed(futures):
            try:
                fut.result()
            except subprocess.CalledProcessError as e:
                print('Error running GARD:', e)

    print('✅ All GARD analyses completed. JSONs in', OUT_DIR)

    # Step 2: run split_recombination_blocks.py for each corresponding .fas/.gard.json pair
    print('▶ Running Python script to split recombination blocks...')
    for fas in sorted(MSA_DIR.glob('*.fas')):
        json_file = OUT_DIR / f'{fas.stem}.gard.json'
        if json_file.exists():
            print(f'▶ Processing {fas} with {json_file}')
            run(['python3', str(PY_SCRIPT), str(fas), str(json_file)])
        else:
            print('⚠ No JSON found for', fas)

    print('▶ Filtering recombination blocks (codon checks)...')
    run(['python3', 'filter_blocks.py'])
    print('✅ Filtering done. Valid blocks in recombination_blocks/, discarded ones in discarded_blocks()')

if __name__ == '__main__':
    main()
