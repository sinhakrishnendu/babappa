#!/usr/bin/env bash
# script0.5.sh
# Run HyPhy GARD (codon-aware) on all *.msa.best.fas files in msa/ folder
# Store results in gard_output/ as JSON
# Then run split_recombination_blocks.py to split MSAs into recombination blocks

set -euo pipefail

# Directories
MSA_DIR="msa"
OUT_DIR="gard_output"
PY_SCRIPT="split_recombination_blocks.py"

# Create output directory if it doesn't exist
mkdir -p "$OUT_DIR"

# Detect available cores, keeping 2 free
TOTAL_CORES=$(nproc)
if [ "$TOTAL_CORES" -le 2 ]; then
    CORES=1
else
    CORES=$((TOTAL_CORES - 2))
fi

echo "Detected $TOTAL_CORES CPU cores. Using $CORES for GARD."

# Find all msa.best.fas files
FILES=("$MSA_DIR"/*msa.best.fas)

if [ ${#FILES[@]} -eq 0 ]; then
    echo "❌ No msa.best.fas files found in $MSA_DIR/"
    exit 1
fi

# Export variables for GNU parallel
export OUT_DIR

# Function to run HyPhy GARD on one file
run_gard() {
    input_file="$1"
    base_name=$(basename "$input_file" .fas)
    output_file="$OUT_DIR/${base_name}.gard.json"

    if [ -f "$output_file" ]; then
        echo "⏩ Skipping $input_file (JSON already exists)"
    else
        echo "▶ Running GARD on $input_file ..."
        hyphy gard --alignment "$input_file" --type codon --output "$output_file"
        echo "✔ Finished $input_file → $output_file"
    fi
}
export -f run_gard

# Run all jobs in parallel
printf "%s\n" "${FILES[@]}" | parallel -j "$CORES" run_gard {}

echo "✅ All GARD analyses completed. JSONs in $OUT_DIR/"

# -------------------------------
# Step 2: Run Python recombination block splitter
# -------------------------------
echo "▶ Running Python script to split recombination blocks..."
for fas in msa/*.fas; do
    json_file="gard_output/$(basename "$fas" .fas).gard.json"
    if [[ -f "$json_file" ]]; then
        echo "▶ Processing $fas with $json_file"
        python3 split_recombination_blocks.py "$fas" "$json_file"
    else
        echo "⚠ No JSON found for $fas"
    fi
done

echo "▶ Filtering recombination blocks (codon checks)..."
python3 filter_blocks.py
echo "✅ Filtering done. Valid blocks in recombination_blocks/, discarded ones in discarded_blocks/"

