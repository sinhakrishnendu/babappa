#!/usr/bin/env python3
import sys, os, json
from Bio import SeqIO

def read_blocks_from_breakpointData(gard_json):
    """Return list of (start_codon, end_codon) from breakpointData, sorted."""
    bpdata = gard_json.get("breakpointData", {})
    blocks = []
    for k in sorted(bpdata.keys(), key=lambda x: int(x)):
        bps_list = bpdata[k].get("bps", [])
        for rng in bps_list:
            if len(rng) == 2:
                start, end = int(rng[0]), int(rng[1])
                if start <= end:
                    blocks.append((start, end))
    blocks = sorted(set(blocks), key=lambda x: (x[0], x[1]))
    return blocks

def infer_scale_factor(seq_len_nt, gard_json):
    """Infer nt-per-site factor (1 for aa/nt; 3 for codon)."""
    n_sites = gard_json.get("input", {}).get("number of sites")
    if isinstance(n_sites, int) and n_sites > 0:
        if seq_len_nt % n_sites == 0:
            return seq_len_nt // n_sites
    return 1

def split_by_gard_json(fasta_file, json_file, output_dir="recombination_blocks"):
    # Load alignment
    records = list(SeqIO.parse(fasta_file, "fasta"))
    if not records:
        raise ValueError(f"No sequences found in {fasta_file}")
    aln_len_nt = len(records[0].seq)

    for r in records:
        if len(r.seq) != aln_len_nt:
            raise ValueError(f"Inconsistent sequence lengths in {fasta_file}")

    # Load JSON
    with open(json_file, "r") as f:
        gard = json.load(f)

    codon_blocks = read_blocks_from_breakpointData(gard)
    if not codon_blocks:
        raise ValueError(f"No blocks found in breakpointData of {json_file}")

    scale = infer_scale_factor(aln_len_nt, gard)

    # Convert codon → nt ranges
    nt_blocks = []
    for (cs, ce) in codon_blocks:
        start_nt = (cs - 1) * scale + 1
        end_nt = ce * scale
        start_nt = max(1, min(start_nt, aln_len_nt))
        end_nt   = max(1, min(end_nt,   aln_len_nt))
        if start_nt <= end_nt:
            nt_blocks.append((cs, ce, start_nt, end_nt))

    # Get organism name (remove QC, msa, etc.)
    fasta_base = os.path.basename(fasta_file)
    organism = fasta_base.split(".")[0]  # e.g. Arabidopsis_halleri
    org_dir = os.path.join(output_dir, organism)
    os.makedirs(org_dir, exist_ok=True)

    # Summary
    codon_ranges = [f"{cs}-{ce}" for (cs, ce, _, _) in nt_blocks]
    nt_ranges = [f"{snt}-{ent}" for (_, _, snt, ent) in nt_blocks]
    print(f"   Blocks (codon): {codon_ranges}")
    print(f"   Blocks (nt, scale={scale}): {nt_ranges}")

    for idx, (cs, ce, snt, ent) in enumerate(nt_blocks, 1):
        out_file = os.path.join(
            org_dir,
            f"{fasta_base}.gard_block{idx}_{cs}-{ce}.fas"
        )
        block_records = []
        for rec in records:
            rec_copy = rec[:]
            rec_copy.seq = rec.seq[snt-1:ent]
            block_records.append(rec_copy)
        SeqIO.write(block_records, out_file, "fasta")
        print(f"✔ Saved block {idx}: {out_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python split_recombination_blocks.py <alignment.fas> <results.gard.json>")
        sys.exit(1)
    split_by_gard_json(sys.argv[1], sys.argv[2])
