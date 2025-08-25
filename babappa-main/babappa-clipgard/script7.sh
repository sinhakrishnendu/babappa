#!/bin/bash
# ------------------------------------------------------------------------------
# This script applies Benjamini-Hochberg (BH) correction for branch and branch
# site models by processing species directories in a given base directory.
#
# The script performs the following operations:
# 1. Defines base and output directories.
# 2. Ensures the output directory exists.
# 3. Locates the Python script responsible for applying the BH correction.
# 4. Loops through each species subdirectory within the base directory.
#    a. Extracts the species name based on the folder name.
#    b. Searches for a CSV file in the species directory to ensure valid data exists.
#    c. Changes into the species directory and runs the Python script.
#    d. Searches for the generated Excel file containing the LRT results.
#    e. Creates a dedicated folder in the output directory for each species and
#       moves the Excel file there.
# 5. Provides feedback on the processing status of each species.
# ------------------------------------------------------------------------------

# Define the base directory (containing species subdirectories with CSV files)
base_dir="codemlanalysis"

# Define the output directory where processed results will be stored
output_dir="BHanalysis"

# Create the output directory if it does not already exist (mkdir -p handles this)
mkdir -p "$output_dir"

# Get the absolute path of the Python script that performs the BH correction.
# The variable $PWD represents the current directory.
python_script="$PWD/lrt_bh_correction.py"

# Loop through each subdirectory (representing a species) within the base directory.
# The trailing slash in "$base_dir"/*/ ensures that only directories are considered.
for species_dir in "$base_dir"/*/ ; do

    # Extract the species name by retrieving the basename of the directory path.
    species_name=$(basename "$species_dir")

    # Search for the first CSV file in the species directory at maximum depth 1.
    # This CSV file should contain the necessary data for processing.
    csv_file=$(find "$species_dir" -maxdepth 1 -name "*.csv")
    
    # If no CSV file is found, output a message and skip processing for this species.
    if [[ -z "$csv_file" ]]; then
        echo "No CSV file found in $species_name. Skipping..."
        continue
    fi

    # Inform the user that processing has started for the current species.
    echo "Processing $species_name..."

    # Change into the species directory and run the Python script for BH correction.
    # This inline subshell (cd ... && python3 ...) ensures that the working directory is 
    # switched to the species directory only for the duration of the command.
    (cd "$species_dir" && python3 "$python_script")

    # After running the Python script, search for the generated Excel file that matches
    # the naming pattern "LRT_results_*.xlsx" in the species directory.
    excel_file=$(find "$species_dir" -maxdepth 1 -name "LRT_results_*.xlsx")
    
    # If an Excel file is found, then:
    if [[ -n "$excel_file" ]]; then
        # Create a subdirectory inside the output directory specifically for this species.
        mkdir -p "$output_dir/$species_name"
        
        # Move the generated Excel file to the species-specific subdirectory.
        mv "$excel_file" "$output_dir/$species_name/"
        
        # Provide feedback to the user that the results have been successfully moved.
        echo "Results moved to $output_dir/$species_name/"
    else
        # If no Excel file is found, notify the user that the processing did not generate one.
        echo "No Excel file generated for $species_name."
    fi
done

# Inform the user that the batch processing of all species is completed.
echo "Batch processing completed."
