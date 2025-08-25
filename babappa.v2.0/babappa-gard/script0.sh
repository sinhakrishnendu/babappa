#!/bin/bash
# ----------------------------------------------------------------------
# Script Overview:
# Performs QC, PRANK codon MSA, trims the MSA with ClipKit (codon-aware),
# and masks internal stop/ambiguous codons for codeml-ready alignments.
# ----------------------------------------------------------------------

mkdir -p QCseq msa

# ------------------ Collect Inputs ------------------
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
echo "✅ QC Step Completed."

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
echo "✅ MSA Step Completed."

# ------------------ Internal Stop/NNN Masking ------------------
# Collect actual PRANK outputs (.best.fas)
prank_files=($(ls msa/*_msa.best.fas 2>/dev/null))

if [ ${#prank_files[@]} -eq 0 ]; then
    echo "⚠️ No PRANK output files found for masking!"
else
    mask_internal_stops() {
        local file="$1"
        echo "Masking internal stop/ambiguous codons for $file..."
        python3 babappa_stopcodon_masker.py "$file" "$file"
    }
    export -f mask_internal_stops
    parallel -j "$PARALLEL_JOBS" mask_internal_stops ::: "${prank_files[@]}"
    echo "✅ Internal stop/ambiguous codon masking completed. Corrected MSAs are ready in msa/"
fi

echo "🎯 Script0 completed. Proceed with Script1 onwards for phylogenetic and selection analysis."
