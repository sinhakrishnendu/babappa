#!/bin/bash
# ------------------------------------------------------------------------------
# This script processes species data for codeml analysis using M0 model.
# It checks for necessary input files/directories, then performs parallel
# processing for each species by preparing control files and running codeml.
# ------------------------------------------------------------------------------

# Exit the script immediately if any command exits with a non-zero status.
set -e

# ------------------------------------------------------------------------------
# Define Number of parallel jobs.
# This value controls how many species will be processed concurrently.
num_parallel=1

# ------------------------------------------------------------------------------
# Define directory and file paths.
# msa_dir: Contains multiple sequence alignments that have been checked for stop codons.
# tree_dir: Contains tree files corresponding to each species.
# output_dir: Where the results (codeml outputs) will be saved.
# base_ctl_file: The base configuration file used by codeml.
# For script1_optional.sh
# msa_dir="MSAStopCodonChecked"
msa_dir="msa"
tree_dir="treefiles"
output_dir="codemloutput"
base_ctl_file="codeml.ctl"

# ------------------------------------------------------------------------------
# Check for the existence of required directories and control file.
# If any required directory or file is missing, display an error and exit.
if [ ! -d "$msa_dir" ] || [ ! -d "$tree_dir" ] || [ ! -f "$base_ctl_file" ]; then
    echo "Error: Required directories or files are missing."
    exit 1
fi

# ------------------------------------------------------------------------------
# Function: process_species
# This function handles processing for an individual species.
# It takes one argument: the species name (identifier).
process_species() {
    # Capture the species identifier passed to the function.
    species="$1"

    # Define the output path for the species results.
    species_output="$output_dir/$species"
    
    # Find the multiple sequence alignment file corresponding to the species.
    # The expected filename pattern is: [species]_msa.best.fas.
    msa_file=$(find "$msa_dir" -name "${species}_msa.best.fas" -print -quit)
    
    # Find the tree file corresponding to the species.
    # The expected filename pattern is: [species].treefile.
    tree_file=$(find "$tree_dir" -name "${species}.treefile" -print -quit)

    # ------------------------------------------------------------------------------
    # Ensure both the alignment file and tree file exist.
    # If either is missing, display a warning message and skip processing this species.
    if [ ! -f "$msa_file" ]; then
        echo "Warning: MSA file for $species not found. Skipping..."
        return
    fi
    if [ ! -f "$tree_file" ]; then
        echo "Warning: Tree file for $species not found. Skipping..."
        return
    fi

    # ------------------------------------------------------------------------------
    # Prepare the output directory for the species.
    # mkdir -p ensures the directory is created; it does nothing if it already exists.
    mkdir -p "$species_output"

    # Copy the required input files to the species-specific output directory:
    # 1. The multiple sequence alignment file is renamed to aligned.fas.
    # 2. The tree file is renamed to treefile.treefile.
    # 3. The base configuration file (codeml.ctl) is copied as-is.
    cp "$msa_file" "$species_output/aligned.fas"
    cp "$tree_file" "$species_output/treefile.treefile"
    cp "$base_ctl_file" "$species_output/"

    # ------------------------------------------------------------------------------
    # Change directory into the species-specific output directory to execute codeml.
    # The block is enclosed in parentheses to run in a subshell, so the current working
    # directory outside this block remains unchanged.
    (
        cd "$species_output"
        echo "Processing M0 model for $species"

        # ------------------------------------------------------------------------------
        # Modify the codeml control file (codeml.ctl) to set the correct paths and parameters.
        # 'sed' is used to replace lines matching the configuration entries:
        # - Update 'seqfile' with the path to the aligned.fas file.
        # - Update 'treefile' with the path to the treefile.treefile file.
        # - Set the 'model' parameter to 0, designating the M0 model.
        # - Set the 'NSsites' parameter to 0.
        sed -i "s|^ *seqfile *=.*|seqfile = aligned.fas|" codeml.ctl
        sed -i "s|^ *treefile *=.*|treefile = treefile.treefile|" codeml.ctl
        sed -i "s|^ *model *=.*|model = 0|" codeml.ctl
        sed -i "s|^ *NSsites *=.*|NSsites = 0|" codeml.ctl

        # ------------------------------------------------------------------------------
        # Create a subfolder specifically for the M0 model analysis.
        m0_folder="M0"
        mkdir -p "$m0_folder"
        
        # Copy the modified codeml control file into the M0 folder as "M0.ctl".
        cp codeml.ctl "$m0_folder/M0.ctl"
        # Also copy the input files needed to run codeml into the M0 folder.
        cp aligned.fas treefile.treefile "$m0_folder/"

        # ------------------------------------------------------------------------------
        # Run codeml on the M0 model.
        # This is done by changing into the M0 folder and running codeml with the given control file.
        (cd "$m0_folder" && codeml "M0.ctl")

        # Indicate successful completion for this species' M0 model analysis.
        echo "Completed M0 model for $species"
    )
}

# ------------------------------------------------------------------------------
# Export the process_species function and global variables so that they are available
# to the parallel jobs spawned by xargs.
export -f process_species
export msa_dir tree_dir output_dir base_ctl_file  

# ------------------------------------------------------------------------------
# Generate a unique list of species names based on the filenames in the MSA directory.
# The command does the following:
# 1. Lists all files matching *_msa.best.fas in the msa_dir.
# 2. Uses sed to remove the directory path, keeping only the filename.
# 3. Uses a second sed command to remove the suffix (_msa.best.fas) to extract the species identifier.
species_list=$(ls "$msa_dir"/*_msa.best.fas | sed 's|.*/||' | sed 's/_msa\.best\.fas//')

# ------------------------------------------------------------------------------
# Run processing in parallel for each species in the species_list.
# xargs is used to run up to 'num_parallel' jobs concurrently.
# The '-n 1' option ensures that each process_species call gets one species name.
# The '-P' option specifies the number of parallel processes.
echo "$species_list" | xargs -n 1 -P $num_parallel bash -c 'process_species "$@"' _

# ------------------------------------------------------------------------------
# Indicate that all species have been processed.
echo "All M0 model processing completed."
