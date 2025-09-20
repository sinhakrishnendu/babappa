#!/usr/bin/env python3
import os
import shutil
from Bio import SeqIO
import sys, io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

RECOMB_DIR = "recombination_blocks"
DISCARD_DIR = "discarded_blocks"

def has_stop_codon(seq):
    stop_codons = {"TAA", "TAG", "TGA"}
    for i in range(0, len(seq) - 2, 3):
        codon = str(seq[i:i+3]).upper()
        if codon in stop_codons:
            return True
    return False

def check_block(filepath):
    records = list(SeqIO.parse(filepath, "fasta"))
    if not records:
        return False, "empty alignment"

    length = len(records[0].seq)
    if length % 3 != 0:
        return False, f"length {length} not divisible by 3"

    for rec in records:
        if has_stop_codon(rec.seq):
            return False, f"stop codon found in {rec.id}"

    return True, "valid"

def main():
    for root, _, files in os.walk(RECOMB_DIR):
        for file in files:
            if not file.endswith(".fas"):
                continue
            fpath = os.path.join(root, file)
            ok, reason = check_block(fpath)

            if ok:
                print(f"✔ Keeping {fpath} ({reason})")
            else:
                # infer organism from parent folder
                organism = os.path.basename(os.path.dirname(fpath))
                dest_dir = os.path.join(DISCARD_DIR, organism)
                os.makedirs(dest_dir, exist_ok=True)

                dest = os.path.join(dest_dir, file)
                shutil.move(fpath, dest)
                print(f"❌ Discarded {fpath} → {dest} ({reason})")

if __name__ == "__main__":
    main()
