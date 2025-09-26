#!/usr/bin/env python3
import sys
import io
import shutil
import subprocess
import multiprocessing
import re, threading, time
from pathlib import Path

# Force stdout/stderr to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

def run(cmd, check=True, capture_output=False, **kwargs):
    print('▶', ' '.join(cmd) if isinstance(cmd, (list,tuple)) else cmd)
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=True, **kwargs)

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def main():
    msa_parent_dir = Path("recombination_blocks")
    tree_dir = Path("treefiles")
    output_dir = Path("sitemodel")
    base_ctl_file = Path("codeml.ctl")

    if not base_ctl_file.exists():
        print(f'Error: Base control file {base_ctl_file} not found.')
        sys.exit(1)
    ensure_dir(output_dir)

    threads = []
    # Look inside recombination_blocks/*/*.fas
    for msa_file in sorted(msa_parent_dir.glob("*/*.fas")):
        species = msa_file.stem  # keep full block name
        tree_file = tree_dir / f"{species}.treefile"

        print('Processing block:', species)
        if not tree_file.exists():
            print('Warning: Tree file for', species, 'not found. Skipping.')
            continue

        species_output = output_dir / species
        ensure_dir(species_output)

        # Copy required files
        shutil.copy(msa_file, species_output / msa_file.name)
        shutil.copy(tree_file, species_output / tree_file.name)
        shutil.copy(base_ctl_file, species_output / "codeml.ctl")

        ctl_file = species_output / "codeml.ctl"
        txt = ctl_file.read_text()
        txt = re.sub(r'^\s*seqfile\s*=.*', f'seqfile = {msa_file.name}', txt, flags=re.M)
        txt = re.sub(r'^\s*treefile\s*=.*', f'treefile = {tree_file.name}', txt, flags=re.M)
        txt = re.sub(r'^\s*model\s*=.*', 'model = 0', txt, flags=re.M)
        txt = re.sub(r'^\s*NSsites\s*=.*', 'NSsites = 0 1 2 3 7 8', txt, flags=re.M)
        ctl_file.write_text(txt)

        def run_job(sp_out, ctl_name):
            run(['bash','-c', f'cd {sp_out} && codeml {ctl_name}'])
            print('Completed:', sp_out.name)

        # Run in parallel with thread limit (8 concurrent jobs max)
        t = threading.Thread(target=run_job, args=(species_output, ctl_file.name))
        t.start()
        threads.append(t)
        while sum(1 for th in threads if th.is_alive()) >= 8:
            time.sleep(1)

    for t in threads:
        t.join()

    print('✅ All site model analyses completed successfully!')

if __name__ == '__main__':
    main()
