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
    input_dir = Path('codemloutput')
    output_dir = Path('codemlanalysis')
    ensure_dir(output_dir)
    import re
    for species_path in sorted(input_dir.glob('*/')):
        species_name = species_path.name
        for analysis_path in sorted(species_path.glob('*/')):
            analysis_name = analysis_path.name
            if (analysis_path/'output.txt').exists():
                lnL_np_line = ''
                with open(analysis_path/'output.txt') as fh:
                    for line in fh:
                        if 'lnL(ntime' in line:
                            lnL_np_line = line.strip()
                            break
                if lnL_np_line:
                    parts = lnL_np_line.split()
                    lnL = parts[4] if len(parts) >=5 else ''
                    np_v = ''
                    m = re.search(r'np:\s*([0-9]+)', lnL_np_line)
                    if m: np_v = m.group(1)
                    species_output_dir = Path(output_dir)/species_name
                    ensure_dir(species_output_dir)
                    output_file = species_output_dir/'lnL_np_values.csv'
                    if not output_file.exists():
                        output_file.write_text('Analysis,lnL,np\n')
                    with open(output_file,'a') as outfh:
                        outfh.write(f'{analysis_name},{lnL},{np_v}\n')
    print('Extraction complete. Results saved in', output_dir)

if __name__ == '__main__':
    main()
