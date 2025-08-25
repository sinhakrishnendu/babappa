#!/bin/bash
# ----------------------------------------------------------------------
# Script Overview:
# Performs QC, PRANK codon MSA, and masks internal stop codons for codeml-ready alignments.
# ----------------------------------------------------------------------

mkdir -p QCseq msa

input_files=($(ls *.fasta *.fas *.fa 2>/dev/null))

if [ ${#input_files[@]} -eq 0 ]; then
    echo "No input files found in the directory!"
    exit 1
fi

PARALLEL_JOBS=1  

# ------------------ QC Step ------------------
run_qc() {
    local file="$1"
    output_file="QCseq/$(basename "$file" .txt)_QC.fasta"
    echo "Running QC on $file..."
    python3 seqQC.py "$file" "$output_file"
    if [ $? -eq 0 ]; then
        echo "QC Passed: $file -> $output_file"
    else
        echo "QC Failed: $file"
    fi
}
export -f run_qc
parallel -j "$PARALLEL_JOBS" run_qc ::: "${input_files[@]}"
echo "QC Step Completed."

# ------------------ PRANK MSA ------------------
qc_files=($(ls QCseq/*.fasta 2>/dev/null))

run_prank() {
    local file="$1"
    output_prefix="msa/$(basename "$file" .fasta)_msa"
    echo "Running PRANK on $file..."
    prank -d="$file" -o="$output_prefix" -codon > "${output_prefix}.log" 2>&1
}
export -f run_prank
parallel -j "$PARALLEL_JOBS" run_prank ::: "${qc_files[@]}"
echo "MSA Step Completed."

# ------------------ Internal Stop Codon Masking ------------------
# Collect all PRANK .best.fas files
msa_files=($(ls msa/*.best.fas 2>/dev/null))

mask_internal_stops() {
    local file="$1"
    echo "Masking internal stop codons for $file..."
    # Overwrite the PRANK output with masked/corrected MSA
    python3 babappa_stopcodon_masker.py "$file" "$file"
}
export -f mask_internal_stops
parallel -j "$PARALLEL_JOBS" mask_internal_stops ::: "${msa_files[@]}"
echo "Internal stop codon masking completed. Corrected MSAs are ready in msa/"

echo "Script0 completed. Proceed with Script1 onwards for phylogenetic and selection analysis."
