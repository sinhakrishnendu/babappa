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
    ensure_dir('QCseq')
    ensure_dir('msa')

    # gather input fasta files
    exts = ('*.fasta','*.fas','*.fa')
    input_files = []
    for e in exts:
        input_files.extend(sorted(Path('.').glob(e)))
    if not input_files:
        print('No input files found in the directory!')
        sys.exit(1)

    PARALLEL_JOBS = int(os.environ.get('PARALLEL_JOBS','1'))

    # QC step
    from concurrent.futures import ThreadPoolExecutor, as_completed
    def run_qc(file):
        out = Path('QCseq') / (file.stem + '_QC.fasta')
        print('Running QC on', file)
        try:
            run(['python3','seqQC.py', str(file), str(out)])
            print('QC Passed:', file, '->', out)
        except subprocess.CalledProcessError:
            print('QC Failed:', file)

    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as ex:
        futures = [ex.submit(run_qc, f) for f in input_files]
        for fut in as_completed(futures):
            fut.result()

    print('QC Step Completed.')

    # PRANK MSA
    qc_files = sorted(Path('QCseq').glob('*.fasta'))
    def run_prank(file):
        output_prefix = Path('msa') / (file.stem + '_msa')
        print('Running PRANK on', file)
        run(['prank', f'-d={str(file)}', f'-o={str(output_prefix)}', '-codon'])

    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as ex:
        futures = [ex.submit(run_prank, f) for f in qc_files]
        for fut in as_completed(futures):
            try: fut.result()
            except Exception as e: print('PRANK error:', e)

    print('MSA Step Completed.')

    # ClipKit trimming
    prank_files = sorted(Path('msa').glob('*.best.fas'))
    def run_clipkit(file):
        tmp_output = file.with_name(file.name.replace('.best.fas','_clipkit_temp.fas'))
        logfile = file.with_name(file.name.replace('.best.fas','_clipkit.log'))
        print('Trimming MSA with ClipKit for', file)
        run(['clipkit', str(file), '-m', 'smart-gap', '--codon', '-o', str(tmp_output)])
        # overwrite original
        tmp_output.replace(file)
        print('ClipKit log saved to:', logfile)

    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as ex:
        futures = [ex.submit(run_clipkit,f) for f in prank_files]
        for fut in as_completed(futures):
            try: fut.result()
            except Exception as e: print('ClipKit error:', e)

    print('ClipKit trimming completed. Trimmed MSAs and logs are ready in msa/')

    # Mask internal stops
    def mask_internal_stops(file):
        print('Masking internal stop/ambiguous codons for', file)
        run(['python3','babappa_stopcodon_masker.py', str(file), str(file)])

    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as ex:
        futures = [ex.submit(mask_internal_stops,f) for f in prank_files]
        for fut in as_completed(futures):
            fut.result()

    print('Internal stop/ambiguous codon masking completed. Corrected MSAs are ready in msa/')
    print('Script0 completed. Proceed with Script1 onwards for phylogenetic and selection analysis.')

if __name__ == '__main__':
    main()
