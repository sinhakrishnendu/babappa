#!/bin/bash
#================================================================================
# codeml site model automator
#
# This script automates the process of running codeml analyses with various
# site models on multiple MSA (multiple sequence alignment) files. For each MSA,
# it locates the corresponding phylogenetic tree, customizes a control file, and
# executes codeml in parallel (up to 8 jobs at a time).
#
# Pre-requisites:
# - A directory "MSAStopCodonChecked" that contains MSA files in FASTA format.
# - A directory "treefiles" that contains tree files named as "<species>.treefile".
# - A base control file named "codeml.ctl" configured for codeml.
#
# The script creates a separate output folder for each species under the "sitemodel"
# directory, and it copies the MSA, tree file, and a modified control file into that
# folder before running codeml.
#================================================================================

# Exit the script immediately if any command fails to avoid unexpected errors.
set -e

#================================================================================
# Define Directories and Base File
#================================================================================

# Directory containing the MSA files with stop codon checked (for script1_optional.sh).
# msa_dir="MSAStopCodonChecked"
msa_dir="msa"

# Directory that contains corresponding tree files.
tree_dir="treefiles"

# Directory where the output for each species will be stored.
output_dir="sitemodel"

# The base control file for codeml, which will be customized per species.
base_ctl_file="codeml.ctl"

#================================================================================
# Ensure Prerequisites are in Place
#================================================================================

# Check if the base control file exists. Exit with an error if it's missing.
if [ ! -f "$base_ctl_file" ]; then
    echo "Error: Base control file '$base_ctl_file' not found."
    exit 1
fi

# Create the output directory if it does not already exist.
mkdir -p "$output_dir"

#================================================================================
# Main Loop: Process Each MSA File
#================================================================================

# Loop through each MSA file (with extension .fas) in the msa_dir directory.
# Avoid using pipelines to preserve the shell environment for the for-loop.
for msa_file in "$msa_dir"/*.fas; do
    # Extract the species name from the MSA file name.
    # This removes any trailing text that matches "_msa.best" and anything following it.
    species=$(basename "$msa_file" | sed 's/_msa\.best.*//')

    # Define the expected tree file for this species based on the species name.
    tree_file="$tree_dir/${species}.treefile"

    # Debug output to show the processing details for the current species.
    echo "Processing species: $species"
    echo "MSA file: $msa_file"
    echo "Expected tree file: $tree_file"

    # If the corresponding tree file does not exist, print a warning and skip this species.
    if [ ! -f "$tree_file" ]; then
        echo "Warning: Tree file for $species not found. Skipping."
        continue
    fi

    #================================================================================
    # Set Up Species-Specific Output Folder and Files
    #================================================================================

    # Create a dedicated output folder for the current species inside the output_dir.
    species_output="$output_dir/$species"
    mkdir -p "$species_output"

    # Copy the MSA file, tree file, and the base control file into this species-specific folder.
    cp "$msa_file" "$tree_file" "$base_ctl_file" "$species_output/"

    # Create a control file inside the species output folder by copying the base control file.
    ctl_file="$species_output/codeml.ctl"
    cp "$base_ctl_file" "$ctl_file"

    #================================================================================
    # Modify the Control File for the Current Analysis
    #================================================================================
    # Update key parameters in the control file using sed:
    # - Change the 'seqfile' entry to point to the name of the MSA file.
    # - Change the 'treefile' entry to point to the name of the tree file.
    # - Set the 'model' parameter to 0 (the specific configuration for codeml).
    # - Set the 'NSsites' parameter to include multiple site models (0, 1, 2, 3, 7, 8).
    sed -i "s|^ *seqfile *=.*|seqfile = $(basename "$msa_file")|" "$ctl_file"
    sed -i "s|^ *treefile *=.*|treefile = $(basename "$tree_file")|" "$ctl_file"
    sed -i "s|^ *model *=.*|model = 0|" "$ctl_file"
    sed -i "s|^ *NSsites *=.*|NSsites = 0 1 2 3 7 8|" "$ctl_file"

    #================================================================================
    # Run codeml Analysis in Parallel
    #================================================================================
    # Change directory to the species output folder and run codeml with the 
    # modified control file. Run the codeml job in the background to allow parallelism.
    (
        cd "$species_output"
        echo "Running codeml for $species (Site Models: 0, 1, 2, 3, 7, 8)"
        codeml "$(basename "$ctl_file")"
        echo "Completed: $species"
    ) &

    # Limit the number of parallel jobs to 8. This loop checks the number of running
    # background jobs; if there are 8 or more, the script will wait until one finishes.
    while [ "$(jobs -r | wc -l)" -ge 8 ]; do
        sleep 1
    done
done

# Wait for all background codeml jobs to finish before moving on.
wait

# Final message indicating that all analyses have completed successfully.
echo "✅ All site model analyses completed successfully!"
