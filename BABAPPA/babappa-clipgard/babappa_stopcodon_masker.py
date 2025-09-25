#!/usr/bin/env python3
"""
force_stop_masker.py
Mask ALL stop codons and ambiguous codons for IQ-TREE compatibility
- Masks all stop codons (TAA, TAG, TGA) regardless of position
- Masks ambiguous codons (containing N)
- Ensures sequences are divisible by 3
- Provides detailed logging
"""

from Bio import SeqIO
from Bio.Seq import Seq
import sys
import os

def mask_all_stop_codons(seq_str):
    """
    Mask ALL stop codons and ambiguous codons regardless of position
    Returns: (masked_sequence, mask_fraction)
    """
    # First trim to make length divisible by 3
    trim_len = len(seq_str) % 3
    if trim_len != 0:
        seq_str = seq_str[:-trim_len]
    
    if not seq_str or len(seq_str) < 3:
        return "", 0.0
    
    masked_seq = []
    mask_count = 0
    total_codons = 0
    
    for i in range(0, len(seq_str), 3):
        codon = seq_str[i:i+3]
        if len(codon) < 3:
            continue
            
        total_codons += 1
        codon_upper = codon.upper()
        
        # Mask ALL stop codons and ambiguous codons
        if codon_upper in {"TAA", "TAG", "TGA"} or "N" in codon_upper:
            masked_seq.append("---")
            mask_count += 1
        else:
            masked_seq.append(codon)
    
    masked_sequence = "".join(masked_seq)
    mask_fraction = mask_count / max(total_codons, 1)
    
    return masked_sequence, mask_fraction

def validate_masking(seq_str):
    """
    Validate that no stop codons remain in the masked sequence
    """
    if not seq_str or len(seq_str) < 3:
        return True
    
    for i in range(0, len(seq_str), 3):
        if i + 3 > len(seq_str):
            continue
            
        codon = seq_str[i:i+3].upper()
        if codon in {"TAA", "TAG", "TGA"}:
            return False
    
    return True

def process_msa(input_fasta, output_fasta, tolerance=0.20):
    """
    Process the MSA: mask stop codons and filter sequences
    """
    kept_records = []
    discarded_records = []
    validation_errors = []
    
    print(f"Processing sequences from: {input_fasta}")
    print("-" * 60)
    
    for record in SeqIO.parse(input_fasta, "fasta"):
        seq_str = str(record.seq)
        
        # Mask all stop codons and ambiguous codons
        masked_seq, mask_fraction = mask_all_stop_codons(seq_str)
        
        # Validate that no stop codons remain
        is_valid = validate_masking(masked_seq)
        
        if not is_valid:
            validation_errors.append(record.id)
            print(f"  ERROR: {record.id} - Stop codons remain after masking!")
        
        if mask_fraction > tolerance:
            discarded_records.append((record.id, mask_fraction))
            print(f"  Discarded: {record.id} (mask fraction: {mask_fraction:.3f})")
        else:
            record.seq = Seq(masked_seq)
            kept_records.append(record)
            status = "VALID" if is_valid else "INVALID"
            print(f"  Kept: {record.id} ({len(masked_seq)} bp, {mask_fraction:.3f} masked, {status})")
    
    # Write output if we have valid sequences
    if kept_records:
        SeqIO.write(kept_records, output_fasta, "fasta")
        print(f"\n✓ Successfully wrote {len(kept_records)} sequences to: {output_fasta}")
    else:
        print(f"\n✗ No sequences passed filtering!")
        return False
    
    # Summary report
    print(f"\n{'='*60}")
    print("PROCESSING SUMMARY:")
    print(f"{'='*60}")
    print(f"Total sequences processed: {len(kept_records) + len(discarded_records)}")
    print(f"Sequences kept: {len(kept_records)}")
    print(f"Sequences discarded (mask fraction > {tolerance}): {len(discarded_records)}")
    print(f"Validation errors: {len(validation_errors)}")
    
    if discarded_records:
        print(f"\nDiscarded sequences (tolerance = {tolerance}):")
        for seq_id, mask_frac in discarded_records:
            print(f"  {seq_id}: {mask_frac:.3f}")
    
    if validation_errors:
        print(f"\n❌ VALIDATION ERRORS (stop codons remain):")
        for seq_id in validation_errors:
            print(f"  {seq_id}")
        return False
    
    # Final validation check
    print(f"\n✅ Final validation:")
    final_kept_records = list(SeqIO.parse(output_fasta, "fasta"))
    all_valid = True
    
    for record in final_kept_records:
        if not validate_masking(str(record.seq)):
            print(f"  ❌ {record.id} still contains stop codons!")
            all_valid = False
        else:
            print(f"  ✅ {record.id} is clean")
    
    if all_valid:
        print(f"\n🎉 SUCCESS: All output sequences are free of stop codons!")
        print(f"   You can now run IQ-TREE with: iqtree2 -s {output_fasta} -st CODON ...")
    else:
        print(f"\n❌ WARNING: Some sequences still contain stop codons!")
    
    return all_valid

def debug_sequence(input_fasta, position=5653):
    """
    Debug function to check what's at a specific position
    """
    print(f"\n{'='*60}")
    print(f"DEBUG: Checking position {position} in sequences")
    print(f"{'='*60}")
    
    for record in SeqIO.parse(input_fasta, "fasta"):
        seq = str(record.seq)
        seq_len = len(seq)
        
        print(f"\n{record.id}:")
        print(f"  Length: {seq_len}")
        
        if position > seq_len:
            print(f"  Position {position} is beyond sequence length")
            continue
        
        # Show context around the position
        start_pos = max(0, position - 6)
        end_pos = min(seq_len, position + 6)
        context = seq[start_pos:end_pos]
        
        print(f"  Context around position {position}: {context}")
        
        # Check if this is part of a stop codon
        codon_start = (position - 1) // 3 * 3  # Convert to 0-based, find codon start
        if codon_start + 3 <= seq_len:
            codon = seq[codon_start:codon_start+3].upper()
            print(f"  Codon containing position {position}: {codon}")
            
            if codon in {"TAA", "TAG", "TGA"}:
                print(f"  ⚠️  STOP CODON DETECTED: {codon}")
            else:
                print(f"  Not a stop codon: {codon}")

if __name__ == "__main__":
    if len(sys.argv) not in [3, 4]:
        print("Usage: python force_stop_masker.py <input_fasta> <output_fasta> [tolerance]")
        print("  tolerance: maximum fraction of masked codons (default: 0.20)")
        print("\nExample: python force_stop_masker.py input.fasta masked.fasta 0.15")
        sys.exit(1)
    
    input_fasta = sys.argv[1]
    output_fasta = sys.argv[2]
    tolerance = float(sys.argv[3]) if len(sys.argv) == 4 else 0.20
    
    # Check if input file exists
    if not os.path.exists(input_fasta):
        print(f"Error: Input file '{input_fasta}' not found!")
        sys.exit(1)
    
    # First, debug the problematic position
    debug_sequence(input_fasta, position=5653)
    
    # Then process the sequences
    print(f"\n{'='*60}")
    print("STARTING STOP CODON MASKING")
    print(f"{'='*60}")
    
    success = process_msa(input_fasta, output_fasta, tolerance)
    
    if success:
        print(f"\n✅ Ready for IQ-TREE analysis!")
        print(f"   Command: iqtree2 -s {output_fasta} -st CODON -B 1000 -alrt 1000 -bnni -T AUTO -pre your_output_prefix")
    else:
        print(f"\n❌ Processing failed - check the errors above")
        sys.exit(1)