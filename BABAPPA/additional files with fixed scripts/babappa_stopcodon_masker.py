#!/usr/bin/env python3
"""
babappa_stopcodon_masker.py (GARD-ready)

- Mask internal stop codons and ambiguous codons (NNN) in codon MSA.
- Retain the terminal stop codon if present.
- Ensure all sequences are divisible by 3 (trim trailing incomplete codons).
- Guarantee no unmasked in-frame stop codons remain.
"""

from Bio import SeqIO
from Bio.Seq import Seq
import sys

input_fasta = sys.argv[1]
output_fasta = sys.argv[2]
tolerance = 0.05  # maximum fraction of internal stops/ambiguous codons

STOP_CODONS = {"TAA", "TAG", "TGA"}

def mask_internal_codons(codon_seq):
    codons = [codon_seq[i:i+3] for i in range(0, len(codon_seq), 3)]
    masked_codons = []
    mask_count = 0

    for i, codon in enumerate(codons):
        if len(codon) < 3:
            # skip incomplete codon (will trim later)
            continue
        # last codon: allow natural stop codon
        if i == len(codons) - 1 and codon.upper() in STOP_CODONS:
            masked_codons.append(codon)
        elif codon.upper() in STOP_CODONS or "N" in codon.upper():
            masked_codons.append("---")
            mask_count += 1
        else:
            masked_codons.append(codon)

    return "".join(masked_codons), mask_count / max(len(codons), 1)

def clean_and_validate(seq_str):
    """Ensure sequence length is divisible by 3 and no leftover stop codons remain."""
    # trim trailing incomplete codon
    trim_len = len(seq_str) % 3
    if trim_len != 0:
        seq_str = seq_str[:-trim_len]

    # final pass: mask any leftover in-frame stops
    codons = [seq_str[i:i+3] for i in range(0, len(seq_str), 3)]
    for i, codon in enumerate(codons[:-1]):  # exclude last codon
        if codon.upper() in STOP_CODONS:
            codons[i] = "---"
    return "".join(codons)

def process_msa(input_fasta, output_fasta, tolerance):
    kept_records = []
    discarded_records = []

    for record in SeqIO.parse(input_fasta, "fasta"):
        masked_seq, mask_fraction = mask_internal_codons(str(record.seq))
        cleaned_seq = clean_and_validate(masked_seq)

        if mask_fraction > tolerance:
            discarded_records.append(record.id)
        else:
            record.seq = Seq(cleaned_seq)
            kept_records.append(record)

    SeqIO.write(kept_records, output_fasta, "fasta")
    print(f"Total sequences kept: {len(kept_records)}")
    print(f"Total sequences discarded due to >{tolerance*100:.1f}% masked codons: {len(discarded_records)}")
    if discarded_records:
        print("Discarded sequences:", ", ".join(discarded_records))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python babappa_stopcodon_masker.py <input_fasta> <output_fasta>")
        sys.exit(1)
    process_msa(input_fasta, output_fasta, tolerance)
