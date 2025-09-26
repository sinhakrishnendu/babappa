#!/usr/bin/env python3
"""
Faithful Python port of your script2.sh.
- Looks for MSAs under `recombination_blocks/**/*.fas`
- For each MSA (block) creates codemloutput/<block>/
- Copies aligned.fas and codeml.ctl into that folder
- Copies per-gene treefiles from foregroundbranch/<block>/*.treefile into the block folder
- For each treefile runs codeml three times: _B, _BS, _BS_NULL
- Inner/outer parallelism uses available CPU cores automatically
- UTF-8 safe (read/write with encoding='utf-8', errors='replace')
- Crucially: does NOT abort on non-zero codeml return codes (mimics original shell)
"""
import sys
import io
import re
import shutil
import subprocess
import multiprocessing
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# Make stdout/stderr UTF-8 safe
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Config (adjust if needed)
MSA_ROOT = Path("recombination_blocks")   # contains subfolders with .fas files
TREE_ROOT = Path("foregroundbranch")      # per-block tree folders
OUTPUT_ROOT = Path("codemloutput")
BASE_CTL = Path("codeml.ctl")

# sanity checks
if not MSA_ROOT.exists():
    sys.exit(f"Error: MSA root not found: {MSA_ROOT}")
if not TREE_ROOT.exists():
    sys.exit(f"Error: Tree root not found: {TREE_ROOT}")
if not BASE_CTL.exists():
    sys.exit(f"Error: Base control file not found: {BASE_CTL}")

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

def run_cmd(cmd, cwd=None):
    """Run command but don't raise on non-zero return; capture and print stdout/stderr."""
    print("▶", " ".join(cmd), "in", cwd or ".")
    res = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip(), file=sys.stderr)
    if res.returncode != 0:
        print(f"⚠ Command returned code {res.returncode}: {' '.join(cmd)}", file=sys.stderr)
    return res.returncode

def update_ctl(template_path: Path, replacements: dict, out_path: Path):
    """Read template_path (utf-8), replace keys with values using regex, write to out_path."""
    txt = template_path.read_text(encoding="utf-8", errors="replace")
    for key, val in replacements.items():
        # Replace line like: seqfile = something   -> seqfile = VAL
        txt = re.sub(rf"(?m)^\s*{re.escape(key)}\s*=.*", f"{key} = {val}", txt)
    out_path.write_text(txt, encoding="utf-8", errors="replace")

def run_codeml_for_treefile(treefile_path: Path, msa_aligned: Path, species_output: Path):
    """
    For a single treefile (Path), perform:
      - Branch model (_B)
      - Branch-site model (_BS)
      - Branch-site null (_BS_NULL)
    Always attempt all three even if one fails (mimics shell behavior).
    """
    base_name = treefile_path.stem
    tree_name = treefile_path.name
    msa_name = msa_aligned.name

    # Use the codeml.ctl already present in species_output as the base for per-model ctl files
    base_ctl_in_species = species_output / "codeml.ctl"
    if not base_ctl_in_species.exists():
        print(f"Error: ctl not found under {species_output}; skipping {tree_name}")
        return

    # ensure the treefile is present in species_output (some callers may have copied already)
    local_tree = species_output / tree_name
    if not local_tree.exists():
        try:
            shutil.copy(treefile_path, local_tree)
        except Exception as e:
            print(f"Error copying treefile {treefile_path} -> {local_tree}: {e}", file=sys.stderr)
            # still attempt with original path below

    # Helper to write ctl and run codeml (non-fatal)
    def do_model(suffix, ctl_updates):
        folder = species_output / f"{base_name}{suffix}"
        folder.mkdir(parents=True, exist_ok=True)
        # Copy base species ctl into folder and then update it
        target_ctl = folder / f"{base_name}{suffix.lstrip('_')}.ctl"  # e.g. AT5... .B.ctl or .BS.ctl
        shutil.copy(base_ctl_in_species, target_ctl)
        # Make replacements so control file refers to local files (names)
        # If treefile exists in folder, use its name; else use original treefile name
        tree_to_write = (folder / tree_name).name if (species_output / tree_name).exists() else tree_name
        replacements = {"seqfile": msa_name, "treefile": tree_to_write}
        replacements.update(ctl_updates)
        # Update the control file in the folder
        update_ctl(target_ctl, replacements, target_ctl)
        # copy aligned.fas and treefile into the folder (if available)
        try:
            shutil.copy(msa_aligned, folder / msa_name)
        except Exception as e:
            print(f"Warning: failed to copy MSA to {folder}: {e}", file=sys.stderr)
        # copy treefile (use species_output copy if present, else original)
        if (species_output / tree_name).exists():
            try:
                shutil.copy(species_output / tree_name, folder / tree_name)
            except Exception as e:
                print(f"Warning: failed to copy treefile into {folder}: {e}", file=sys.stderr)
        else:
            try:
                shutil.copy(treefile_path, folder / tree_name)
            except Exception as e:
                print(f"Warning: failed to copy original treefile into {folder}: {e}", file=sys.stderr)

        print(f"Running codeml for {folder.name}")
        # Run codeml; do not raise on non-zero exit (shell didn't)
        rc = run_cmd(["codeml", target_ctl.name], cwd=folder)
        return rc

    # Branch model (model=2, NSsites=0)
    do_model(
        suffix=f"_{base_name}_B".replace(f"_{base_name}_","_B_") if False else "_B",  # keep exact folder names like <base>_B
        ctl_updates={"model": "2", "NSsites": "0"}
    )
    # Branch-site model (model=2, NSsites=2)
    do_model("_BS", {"model": "2", "NSsites": "2"})
    # Branch-site NULL (model=2, NSsites=2, fix_omega=1, omega=1)
    do_model("_BS_NULL", {"model": "2", "NSsites": "2", "fix_omega": "1", "omega": "1"})

def process_species(msa_file: Path):
    """
    Given an MSA file path (block .fas), create codemloutput/<block>/ and run per-gene tree jobs.
    """
    try:
        species = msa_file.stem
        print(f"\n--- Processing block: {species}")

        # Prepare species output dir
        species_output = OUTPUT_ROOT / species
        species_output.mkdir(parents=True, exist_ok=True)

        # Copy aligned MSA (as aligned.fas) and base ctl into species dir
        aligned_target = species_output / "aligned.fas"
        shutil.copy(msa_file, aligned_target)
        shutil.copy(BASE_CTL, species_output / "codeml.ctl")

        # Patch seqfile in species/codeml.ctl to aligned.fas (so per-model copies inherit it)
        update_ctl(species_output / "codeml.ctl", {"seqfile": "aligned.fas"}, species_output / "codeml.ctl")

        # Find treefiles under foregroundbranch/<species>/
        species_tree_dir = TREE_ROOT / species
        if not species_tree_dir.exists():
            print(f"⚠ Warning: tree directory not found for {species} -> {species_tree_dir}. Skipping.")
            return

        treefiles = sorted(list(species_tree_dir.glob("*.treefile")))
        if not treefiles:
            print(f"⚠ Warning: no .treefile found in {species_tree_dir}. Skipping.")
            return

        # copy all treefiles into species_output (mirrors cp "$species_tree_dir"/*.treefile "$species_output")
        for tf in treefiles:
            try:
                shutil.copy(tf, species_output / tf.name)
            except Exception as e:
                print(f"Warning: failed to copy {tf} into {species_output}: {e}", file=sys.stderr)

        # Inner parallelism: use available cores
        inner_workers = max(1, multiprocessing.cpu_count())
        print(f"Launching up to {inner_workers} parallel tree jobs for {species} (found {len(treefiles)} treefiles).")

        # Submit treefile jobs (we pass the original tf path to ensure copy works if needed)
        with ThreadPoolExecutor(max_workers=inner_workers) as ex:
            futures = [ex.submit(run_codeml_for_treefile, tf, aligned_target, species_output) for tf in treefiles]
            for fut in as_completed(futures):
                try:
                    _ = fut.result()
                except Exception as e:
                    # ensure we do not abort the whole species if one tree thread throws
                    print(f"Error in codeml run (thread): {e}", file=sys.stderr)

        print(f"Completed block: {species}")
    except Exception as e:
        print(f"Fatal error processing {msa_file}: {e}", file=sys.stderr)

def main():
    # find all .fas files under recombination_blocks (non-recursive or recursive depending on structure)
    msa_files = list(MSA_ROOT.rglob("*.fas"))
    if not msa_files:
        sys.exit(f"No .fas files found under {MSA_ROOT}")

    # create list of unique blocks (use file stem)
    msa_files = sorted(msa_files)
    print(f"Detected {len(msa_files)} block MSAs. Using up to {multiprocessing.cpu_count()} parallel outer workers.")

    outer_workers = min(len(msa_files), multiprocessing.cpu_count())
    with ProcessPoolExecutor(max_workers=outer_workers) as ex:
        futures = [ex.submit(process_species, mf) for mf in msa_files]
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as e:
                # don't let one bad block stop others
                print("Error in species-level processing:", e, file=sys.stderr)

    print("All blocks processed.")

if __name__ == "__main__":
    main()
