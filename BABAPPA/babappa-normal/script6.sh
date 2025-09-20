#!/bin/bash
# =============================================================================
# lnL and np Value Extractor for sitemodel
#
# This script navigates through species-specific subdirectories within the 
# "sitemodel" folder. For each species, it checks for the existence of an 
# "output.txt" file. If found, it extracts the lnL (log-likelihood) and np 
# (number of parameters) values for each model entry and writes these values 
# into a CSV file placed in a corresponding directory structure under 
# "sitemodelanalysis".
#
# The CSV file is formatted with headers and one row per model entry, 
# containing the model name, lnL value, and np value.
#
# -----------------------------------------------------------------------------
# Step-by-step Overview:
#
# 1. Define input and output directories.
#
# 2. Create the main output directory if it does not exist.
#
# 3. Iterate over each species subdirectory in the input directory.
#
# 4. For each species directory:
#    a. Extract the species name from the folder name.
#    b. Verify that an "output.txt" file exists.
#    c. Create a corresponding species subdirectory in the output folder.
#    d. Initialize a CSV file with headers "Model,lnL,np".
#
# 5. Read the "output.txt" file line-by-line:
#    a. Identify lines that designate a model name (e.g., "Model 1") and store 
#       the model identification.
#    b. When a line contains the text "lnL(ntime", extract:
#       - The lnL value from the 5th field.
#       - The np value using a regular expression to remove any extra characters.
#    c. Append the extracted values to the CSV file.
#
# 6. Once processing is complete for all species, print a completion message.
# =============================================================================

# Define input and output directories
input_dir="sitemodel"                  # Input folder containing species subdirectories
output_dir="sitemodelanalysis"         # Main output folder for storing extracted CSV data

# Create the main output directory if it doesn't exist
mkdir -p "$output_dir"                 # The -p option creates the directory if needed

# Loop through all species subdirectories within the sitemodel folder
for species_path in "$input_dir"/*/ ; do
    # Extract species name from the folder name using basename
    species_name=$(basename "$species_path")

    # Check if output.txt exists inside the species folder
    if [[ -f "$species_path/output.txt" ]]; then
        # Create a subdirectory for this species within the main output directory
        species_output_dir="$output_dir/$species_name"
        mkdir -p "$species_output_dir"

        # Define the path for the output CSV file inside the species subfolder
        output_file="$species_output_dir/lnL_np_values.csv"

        # Initialize the CSV file with headers: Model, lnL, np
        echo "Model,lnL,np" > "$output_file"

        # Initialize an empty variable to store the current model's name
        current_model=""

        # Process each line of the output.txt file
        while IFS= read -r line; do
            # Detect lines that start with "Model" followed by a number to capture the model's identity.
            if [[ "$line" =~ ^Model[[:space:]]+[0-9]+ ]]; then
                # Extract the model name using awk; this assumes the model name is in the first two fields.
                current_model=$(echo "$line" | awk '{print $1, $2}')
            fi

            # Check if the current line contains the specific pattern "lnL(ntime", which indicates
            # that lnL and np values are present in this line.
            if [[ "$line" == *"lnL(ntime"* ]]; then
                # Extract the lnL value:
                # The value is assumed to be in the 5th field of the line.
                lnL=$(echo "$line" | awk '{print $5}')

                # Extract the np value:
                # This uses sed with an extended regex (-E) to find "np:" followed by digits,
                # capturing the digits as the np value. Any extraneous characters are discarded.
                np=$(echo "$line" | sed -E 's/.*np: *([0-9]+).*/\1/')

                # Append the extracted values along with the model name into the CSV file,
                # using comma-separated values.
                echo "$current_model,$lnL,$np" >> "$output_file"
            fi
        done < "$species_path/output.txt"
    fi
done

# Print a completion message to indicate that the extraction process is done.
echo "Extraction complete. Results saved in $output_dir."
