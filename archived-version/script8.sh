#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: BH_correction_for_site_models.sh
# Description: This script automates Benjamini-Hochberg (BH) correction for 
#              LRT (Likelihood Ratio Test) results generated from codeml site
#              model analyses across multiple species directories. It locates
#              CSV files containing raw LRT p-values, runs a Python script to 
#              apply BH correction, and saves the results in organized output
#              directories per species.
#
# -----------------------------------------------------------------------------

# Define the base working directory (i.e., where the script is being run from)
BASE_DIR=$(pwd)

# Define the input directory where site model CSV files are located
SITE_MODEL_DIR="$BASE_DIR/sitemodelanalysis"

# Define the output directory where BH-corrected results will be saved
BH_ANALYSIS_DIR="$BASE_DIR/BHanalysis4sitemodel"

# Create the output directory if it does not already exist
mkdir -p "$BH_ANALYSIS_DIR"

# Loop through each subdirectory under SITE_MODEL_DIR
# Each subdirectory is assumed to correspond to a different species
for species_dir in "$SITE_MODEL_DIR"/*/; do
    # Extract just the species name (directory name) from the path
    species=$(basename "$species_dir")
    
    # Create a corresponding output subdirectory for the species under BH_ANALYSIS_DIR
    output_dir="$BH_ANALYSIS_DIR/$species"
    mkdir -p "$output_dir"
    
    # Find the first CSV file in the species directory (assumes one CSV per directory)
    csv_file=$(find "$species_dir" -maxdepth 1 -type f -name "*.csv" | head -n 1)
    
    # Check if a CSV file was found
    if [[ -n "$csv_file" ]]; then
        echo "Processing $csv_file for species $species"
        
        # Run the Python script that performs BH correction on the CSV file
        # This script is assumed to:
        # 1. Read the input CSV file (containing LRT p-values).
        # 2. Apply BH correction.
        # 3. Save the results as 'lrt_results.csv' in the BASE_DIR.
        python3 "$BASE_DIR/lrt_bh_correction.sitemodel.py" "$csv_file"
        
        # After the Python script runs, check whether the output file was generated
        if [[ -f "$BASE_DIR/lrt_results.csv" ]]; then
            # Move the corrected result to the corresponding species output directory
            mv "$BASE_DIR/lrt_results.csv" "$output_dir/"
        else
            # Display an error message if the expected output file wasn't found
            echo "Error: No output file generated for $species."
        fi
    else
        # Inform the user if no CSV file was found in the species directory
        echo "No CSV file found in $species_dir"
    fi
done
