#!/bin/bash
# =============================================================================
# Universal lnL and np Value Extractor for sitemodel (PAML output)
#
# Handles both styles of output:
#   1. "NSsites Model 0: one-ratio"
#   2. "Model: One dN/dS ratio,"
#
# Extracts Model (number if present), lnL, and np into CSV files.
# =============================================================================

input_dir="sitemodel"
output_dir="sitemodelanalysis"

mkdir -p "$output_dir"

for species_path in "$input_dir"/*/ ; do
    species_name=$(basename "$species_path")

    if [[ -f "$species_path/output.txt" ]]; then
        species_output_dir="$output_dir/$species_name"
        mkdir -p "$species_output_dir"

        output_file="$species_output_dir/lnL_np_values.csv"
        echo "Model,lnL,np" > "$output_file"

        current_model=""

        while IFS= read -r line; do
            # Case 1: NSsites Model lines
            if [[ "$line" =~ ^NSsites[[:space:]]+Model[[:space:]]+([0-9]+) ]]; then
                model_num="${BASH_REMATCH[1]}"
                current_model="Model $model_num"
            fi

            # Case 2: Simple "Model:" line (no number given)
            if [[ "$line" =~ ^Model: ]]; then
                # Use just "Model" if no number is provided
                current_model="Model"
            fi

            # Extract lnL and np
            if [[ "$line" == *"lnL(ntime"* ]]; then
                lnL=$(echo "$line" | awk '{print $5}')
                np=$(echo "$line" | sed -E 's/.*np: *([0-9]+).*/\1/')
                echo "$current_model,$lnL,$np" >> "$output_file"
            fi
        done < "$species_path/output.txt"
    fi
done

echo "Extraction complete. Results saved in $output_dir."
