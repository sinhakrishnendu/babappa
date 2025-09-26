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
    ensure_dir('iqtreeoutput')
    ensure_dir('treefiles')
    ensure_dir('foregroundbranch')

    total = cpu_count()
    PARALLEL_IQTREE_JOBS = int(os.environ.get('PARALLEL_IQTREE_JOBS', str(total)))
    PARALLEL_JOBS = int(os.environ.get('PARALLEL_JOBS', str(total)))
    print(f'Detected {total} cores → using {PARALLEL_IQTREE_JOBS} IQ-TREE jobs and {PARALLEL_JOBS} foreground jobs.')

    msa_files = sorted(Path('recombination_blocks').rglob('*.fas'))
    if not msa_files:
        print('No recombination block FASTA files found for IQ-TREE2. Exiting.')
        sys.exit(1)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    def run_iqtree(file):
        basename = file.stem
        parentdir = file.parent.name
        output_folder = Path('iqtreeoutput')/parentdir/basename
        ensure_dir(output_folder)
        logfile = output_folder / f'{basename}_iqtree.log'
        run(['iqtree2','-s',str(file),'-st','CODON','-B','1000','-alrt','1000','-bnni','-T','AUTO','-pre',str(output_folder/f'{basename}')], check=True)
        print('IQ-TREE2 finished for', file)

    with ThreadPoolExecutor(max_workers=PARALLEL_IQTREE_JOBS) as ex:
        futures = [ex.submit(run_iqtree,f) for f in msa_files]
        for fut in as_completed(futures):
            try: fut.result()
            except Exception as e: print('iqtree error:', e)

    print('IQ-TREE2 Step Completed.')

    # copy treefiles
    for p in Path('iqtreeoutput').rglob('*.treefile'):
        shutil.copy(p, Path('treefiles')/p.name)
    print('All tree files copied to treefiles/.')

    # Foreground branch selection
    def run_foreground_branch(treefile):
        gene_name = Path(treefile).stem
        output_folder = Path('foregroundbranch')/gene_name
        ensure_dir(output_folder)
        run(['python3','4GroundBranchGenerator.py', str(treefile), str(output_folder)])

    tree_files = sorted(Path('treefiles').glob('*.treefile'))
    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as ex:
        futures = [ex.submit(run_foreground_branch, str(tf)) for tf in tree_files]
        for fut in as_completed(futures):
            try: fut.result()
            except Exception as e: print('foreground branch error:', e)

    print('Foreground Branch Selection Completed.')

if __name__ == '__main__':
    main()
