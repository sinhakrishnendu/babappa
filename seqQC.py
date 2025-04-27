import argparse
import numpy as np
from Bio import SeqIO
import os

# Constants for biological QC
START_CODON = "ATG"
STOP_CODONS = {"TAA", "TAG", "TGA"}
VALID_NUCLEOTIDES = {"A", "T", "G", "C"}

def is_valid_sequence(seq: str) -> tuple[bool, str | None]:
    """
    Returns (True, None) if the sequence is valid, else (False, reason).
    Quality criteria:
      - Starts with ATG
      - Ends with a valid stop codon (TAA, TAG, or TGA)
      - Length > 300 and divisible by 3
      - Contains only A, T, G, C
      - No internal in-frame stop codons
    """
    seq = seq.upper()
    if not seq.startswith(START_CODON):
        return False, "Does not start with ATG"
    if seq[-3:] not in STOP_CODONS:
        return False, "Does not end with a valid stop codon"
    if len(seq) <= 300:
        return False, "Length less than 300 bp"
    if len(seq) % 3 != 0:
        return False, "Length not divisible by 3"
    if not set(seq).issubset(VALID_NUCLEOTIDES):
        return False, "Contains non-ATGC characters"
    for i in range(3, len(seq) - 3, 3):
        if seq[i:i+3] in STOP_CODONS:
            return False, f"Internal stop codon at position {i+1}"
    return True, None

def filter_sequences_by_quality(sequences, log_file_path):
    """
    Applies biological QC checks and logs failures.
    
    Returns a dictionary of sequences that passed QC.
    """
    passed = {}
    with open(log_file_path, "w") as log_file:
        for id_, seq in sequences.items():
            valid, reason = is_valid_sequence(seq)
            if valid:
                passed[id_] = seq.upper()  # ensure output is uppercase
            else:
                log_file.write(f"{id_}\tFAILED\t{reason}\n")
    return passed

def remove_length_outliers(sequences):
    """Removes length outliers using the IQR method."""
    if not sequences:
        return {}

    lengths = np.array([len(seq) for seq in sequences.values()])
    if len(lengths) < 4:
        return sequences

    q1, q3 = np.percentile(lengths, [25, 75])
    iqr = q3 - q1
    lower_bound, upper_bound = q1 - 3 * iqr, q3 + 3 * iqr

    return {id_: seq for id_, seq in sequences.items() if lower_bound <= len(seq) <= upper_bound}

def process_fasta(input_file, output_passed):
    """
    Processes a FASTA file:
     - Performs biological QC and logs failures.
     - Removes outliers using the Modified Z-score method.
     - Writes the QC-passed sequences in uppercase to the output file.
    """
    # Check if input file exists and is accessible
    if not os.path.isfile(input_file):
        print(f"Error: Input file {input_file} does not exist or is not accessible.")
        return

    sequences = {record.id: str(record.seq) for record in SeqIO.parse(input_file, "fasta")}
    
    # Check if sequences were parsed correctly
    if not sequences:
        print(f"Failed QC: {input_file} (No sequences found or unable to parse)")
        return

    log_file = output_passed + ".log.txt"
    
    # Apply biological QC and log failures
    filtered_sequences = filter_sequences_by_quality(sequences, log_file)
    
    # Remove length outliers using the Modified Z-score method
    filtered_sequences = remove_length_outliers(filtered_sequences)

    # Check if any sequences pass QC
    if filtered_sequences:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_passed)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_passed, "w") as out_f:
            for id_, seq in filtered_sequences.items():
                out_f.write(f">{id_}\n{seq}\n")
        print(f"Passed QC: {input_file} -> {output_passed}")
        print(f"QC log saved to: {log_file}")
    else:
        print(f"Failed QC: {input_file} (All sequences removed during QC)")
        print(f"QC log saved to: {log_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Biological QC filter for FASTA sequences with robust outlier detection.")
    parser.add_argument("input", help="Input FASTA file")
    parser.add_argument("output_passed", help="Output file for QC-passed sequences")
    args = parser.parse_args()
    
    process_fasta(args.input, args.output_passed)
