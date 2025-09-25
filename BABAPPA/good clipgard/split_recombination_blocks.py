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

def adjust_to_codon_boundaries(start_nt, end_nt, aln_len_nt):
    """Ensure block boundaries fall on full codons by trimming.
       Returns adjusted (start_nt, end_nt, trim_start, trim_end)."""
    orig_start, orig_end = start_nt, end_nt

    # Move start up to next codon boundary
    if (start_nt - 1) % 3 != 0:
        start_nt += (3 - ((start_nt - 1) % 3))
    # Move end down to previous codon boundary
    if end_nt % 3 != 0:
        end_nt -= (end_nt % 3)

    # Clamp to alignment length
    start_nt = max(1, min(start_nt, aln_len_nt))
    end_nt   = max(1, min(end_nt, aln_len_nt))

    trim_start = start_nt - orig_start
    trim_end   = orig_end - end_nt
    return start_nt, end_nt, trim_start, trim_end

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

    # Convert codon → nt ranges and adjust to codon boundaries
    nt_blocks = []
    for (cs, ce) in codon_blocks:
        start_nt = (cs - 1) * scale + 1
        end_nt   = ce * scale
        start_nt, end_nt, trim_start, trim_end = adjust_to_codon_boundaries(start_nt, end_nt, aln_len_nt)
        if start_nt <= end_nt:
            nt_blocks.append((cs, ce, start_nt, end_nt, trim_start, trim_end))

    # Get organism name
    fasta_base = os.path.basename(fasta_file)
    organism = fasta_base.split(".")[0]
    org_dir = os.path.join(output_dir, organism)
    os.makedirs(org_dir, exist_ok=True)

    # Open log file
    log_file = os.path.join(org_dir, "split_recombination_blocks.log")
    with open(log_file, "w") as log:
        log.write(f"Input FASTA: {fasta_file}\n")
        log.write(f"GARD JSON: {json_file}\n")
        log.write(f"Alignment length: {aln_len_nt} nt\n")
        log.write(f"Scale factor: {scale}\n\n")

        codon_ranges = [f"{cs}-{ce}" for (cs, ce, _, _, _, _) in nt_blocks]
        nt_ranges = [f"{snt}-{ent}" for (_, _, snt, ent, _, _) in nt_blocks]
        log.write(f"Blocks (codon): {codon_ranges}\n")
        log.write(f"Blocks (nt): {nt_ranges}\n\n")

        print(f"   Blocks (codon): {codon_ranges}")
        print(f"   Blocks (nt, scale={scale}): {nt_ranges}")

        for idx, (cs, ce, snt, ent, trim_start, trim_end) in enumerate(nt_blocks, 1):
            if (ent - snt + 1) < 3:
                msg = f"✘ Skipped block {idx}: too short after trimming (<1 codon)\n"
                print(msg.strip())
                log.write(msg)
                continue

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

            msg = (f"✔ Saved block {idx}: {out_file}\n"
                   f"   Trimmed {trim_start} nt at start, {trim_end} nt at end\n")
            print(msg.strip())
            log.write(msg + "\n")

    print(f"\n📑 Log written to: {log_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python split_recombination_blocks.py <alignment.fas> <results.gard.json>")
        sys.exit(1)
    split_by_gard_json(sys.argv[1], sys.argv[2])
