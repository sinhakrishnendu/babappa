#!/bin/bash
# =======================================================================
# Script Name: lnLp and np value extractor for branch and branch-site model
# Description: This script navigates through a given directory structure,
#              extracts lnL (log-likelihood) and np (number of parameters)
#              values from "output.txt" files produced by codeml (from PAML),
#              and saves the extracted data in CSV format organized by species.
#
#              It is specifically designed for analyzing outputs from branch
#              and branch-site models.
#
# Author: [Your Name]
# Date: [Date]
# =======================================================================

# ----------------------------
# Set up input and output directories
# ----------------------------
# 'input_dir' is set to the directory where codeml output is stored.
input_dir="codemloutput"
# 'output_dir' is where the analysis results will be saved in CSV format.
output_dir="codemlanalysis"

# Create the main output directory if it doesn't exist. The -p flag makes sure that the 
# directory is created along with parent directories if they don't exist.
mkdir -p "$output_dir"

# ----------------------------
# Iterate through all species directories in the input folder
# ----------------------------
# The loop goes through each subdirectory inside 'codemloutput'. Each subdirectory
# represents a different species.
for species_path in "$input_dir"/*/ ; do
    # Extract the species name from the folder's basename.
    species_name=$(basename "$species_path")

    # ----------------------------
    # Iterate through all analysis type directories for the current species
    # ----------------------------
    # Inside each species folder, there are further subdirectories for different analysis types.
    for analysis_path in "$species_path"/*/ ; do
        # Extract the analysis type folder name (e.g., branch-site or branch model).
        analysis_name=$(basename "$analysis_path")

        # ----------------------------
        # Check for the existence of the output file and process if available
        # ----------------------------
        # Verify that the expected "output.txt" exists in the current analysis subfolder.
        if [[ -f "$analysis_path/output.txt" ]]; then
            # Search within the output.txt file for the line containing the lnL and np info.
            # The grep command looks for a specific pattern "lnL(ntime", which is expected
            # to be present in the line that also contains the parameter count.
            lnL_np_line=$(grep "lnL(ntime" "$analysis_path/output.txt")

            # Ensure that the grep command found a valid line before processing.
            if [[ ! -z "$lnL_np_line" ]]; then
                # ----------------------------
                # Extract lnL and np values
                # ----------------------------
                # Use awk to extract the lnL value, assuming it is the 5th column
                # in the space-separated output.
                lnL=$(echo "$lnL_np_line" | awk '{print $5}')

                # For extracting 'np' (number of parameters) value, the field is isolated by
                # splitting the line using custom delimiters: "np:" and then ")". It takes the first
                # word after "np:" as the value.
                np=$(echo "$lnL_np_line" | awk -F "np:|\\)" '{print $2}' | awk '{print $1}')

                # ----------------------------
                # Organize the output data by species
                # ----------------------------
                # Define the output subdirectory for the current species inside the main 
                # output directory and create it if it doesn't exist.
                species_output_dir="$output_dir/$species_name"
                mkdir -p "$species_output_dir"

                # Define the full path of the output CSV file where data will be appended.
                output_file="$species_output_dir/lnL_np_values.csv"

                # ----------------------------
                # Initialize CSV file with headers if it doesn't exist
                # ----------------------------
                if [[ ! -f "$output_file" ]]; then
                    # Write header row to the CSV file.
                    echo "Analysis,lnL,np" > "$output_file"
                fi

                # ----------------------------
                # Append extracted lnL and np values to the CSV file
                # ----------------------------
                # Each row in the CSV represents one analysis with its name and the two extracted values.
                echo "$analysis_name,$lnL,$np" >> "$output_file"
            fi
        fi
    done
done

# ----------------------------
# Final message to indicate completion
# ----------------------------
echo "Extraction complete. Results saved in $output_dir."
