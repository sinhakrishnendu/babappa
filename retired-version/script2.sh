#!/bin/bash

###############################################################################
# SCRIPT OVERVIEW:
# This script is designed to run the program "codeml" (from the PAML package)
# in parallel over multiple species and for each species, over multiple treefiles.
# It uses GNU Parallel constructs (via xargs with the -P flag) to achieve both:
#   - Outer parallelization: processing different species simultaneously.
#   - Inner parallelization: within each species, processing multiple treefiles concurrently.
#
# The script assumes that the necessary files and directories are already set up:
#   - A directory containing Multiple Sequence Alignments (MSAs) checked for stop codons.
#   - A directory containing treefiles for each species.
#   - A base control file "codeml.ctl" as a template.
#
# Also note that essential software such as codeml and GNU Parallel must be installed 
# and available in the system's PATH.
###############################################################################

# Exit immediately if any command exits with a non-zero status.
set -e

###############################################################################
# VARIABLE DEFINITIONS:
###############################################################################

# Outer level: Number of species processed in parallel.
num_parallel=1

# Inner level: Number of treefiles processed in parallel per species.
inner_parallel=1

# Define directory names for input and output:
# msa_dir="MSAStopCodonChecked"       # Directory where MSAs (with stop codon checks) are stored for script1_optional.sh
msa_dir="msa"                         # Directory where MSA sare stored for script1
tree_dir="foregroundbranch"           # Directory containing treefiles organized by species.
output_dir="codemloutput"             # Directory where codeml output will be saved.
base_ctl_file="codeml.ctl"            # Template control file for codeml run.

# Verify that critical directories and the control file exist.
if [ ! -d "$msa_dir" ] || [ ! -d "$tree_dir" ] || [ ! -f "$base_ctl_file" ]; then
    echo "Error: Required directories or files are missing."
    exit 1
fi

# Create the output directory if it doesn't already exist.
mkdir -p "$output_dir"

###############################################################################
# FUNCTION: run_codeml_for_treefile
# Purpose:
#   This function runs codeml for a single treefile using three different models:
#     1. Branch Model.
#     2. Branch-Site Model.
#     3. Null Model (a variation of branch-site model with fixed omega).
#
# Parameters:
#   $1 -> treefile: The current treefile to be processed.
#   $2 -> species: The species name (used mainly for logging).
#   $3 -> species_output: The directory where output files for this species are stored.
#
# Details:
#   - Changes directory to the species output folder.
#   - Derives a base name from the treefile name (by removing the ".treefile" extension).
#   - For each model, a specific folder is created and the base control file is copied.
#   - The control file is updated using sed to reflect the parameters required for the specific model.
#   - The MSA and treefile are copied into the model-specific folder.
#   - codeml is executed within that folder.
###############################################################################
run_codeml_for_treefile() {
    local treefile="$1"      # The treefile to process.
    local species="$2"       # The species being processed.
    local species_output="$3"  # The output directory for this species.

    # Change directory into the species-specific output folder.
    cd "$species_output"
    
    # Define the MSA file name used within the species directory.
    local msa_file="aligned.fas"
    # Remove the '.treefile' suffix to create a base name for file/folder naming.
    local base_name="${treefile%.treefile}"
    
    echo "Processing $treefile in $species"
    
    # ---------------------- Branch Model ----------------------------
    # Prepare a folder for the branch model run.
    local branch_folder="${base_name}_B"
    mkdir -p "$branch_folder"
    
    # Copy the base control file into the model-specific folder and rename it.
    cp codeml.ctl "$branch_folder/$base_name.B.ctl"
    # Update the control file: set the treefile path.
    sed -i "s|^ *treefile *=.*|treefile = $treefile|" "$branch_folder/$base_name.B.ctl"
    # Set model parameter to 2 for branch model.
    sed -i "s|^ *model *=.*|model = 2|" "$branch_folder/$base_name.B.ctl"
    # Set NSsites parameter to 0 (indicating branch model).
    sed -i "s|^ *NSsites *=.*|NSsites = 0|" "$branch_folder/$base_name.B.ctl"
    # Copy the MSA file and the treefile into the branch folder.
    cp "$msa_file" "$treefile" "$branch_folder/"
    # Run codeml on the branch model control file in its own subdirectory.
    (cd "$branch_folder" && codeml "$base_name.B.ctl")
    
    # ------------------- Branch-Site Model --------------------------
    # Prepare a folder for the branch-site model.
    local bs_folder="${base_name}_BS"
    mkdir -p "$bs_folder"
    
    cp codeml.ctl "$bs_folder/$base_name.BS.ctl"
    sed -i "s|^ *treefile *=.*|treefile = $treefile|" "$bs_folder/$base_name.BS.ctl"
    sed -i "s|^ *model *=.*|model = 2|" "$bs_folder/$base_name.BS.ctl"
    # Set NSsites parameter to 2 indicating branch-site model.
    sed -i "s|^ *NSsites *=.*|NSsites = 2|" "$bs_folder/$base_name.BS.ctl"
    cp "$msa_file" "$treefile" "$bs_folder/"
    (cd "$bs_folder" && codeml "$base_name.BS.ctl")
    
    # --------------------- Null Model -------------------------------
    # Prepare a folder for the null model (branch-site null) run.
    local null_folder="${base_name}_BS_NULL"
    mkdir -p "$null_folder"
    
    cp codeml.ctl "$null_folder/$base_name.BS_NULL.ctl"
    sed -i "s|^ *treefile *=.*|treefile = $treefile|" "$null_folder/$base_name.BS_NULL.ctl"
    sed -i "s|^ *model *=.*|model = 2|" "$null_folder/$base_name.BS_NULL.ctl"
    sed -i "s|^ *NSsites *=.*|NSsites = 2|" "$null_folder/$base_name.BS_NULL.ctl"
    # Set fix_omega to 1 to fix the omega parameter in this null model.
    sed -i "s|^ *fix_omega *=.*|fix_omega = 1|" "$null_folder/$base_name.BS_NULL.ctl"
    # Set omega to 1 to indicate that no selection is assumed (null hypothesis).
    sed -i "s|^ *omega *=.*|omega = 1|" "$null_folder/$base_name.BS_NULL.ctl"
    cp "$msa_file" "$treefile" "$null_folder/"
    (cd "$null_folder" && codeml "$base_name.BS_NULL.ctl")
    
    echo "Finished $treefile in $species"
}
# Export the function so that it is available to subshells spawned by xargs.
export -f run_codeml_for_treefile

###############################################################################
# FUNCTION: process_species
# Purpose:
#   This function processes one species at a time by:
#     - Locating the corresponding MSA file.
#     - Locating the species-specific tree directory.
#     - Preparing an output directory and copying necessary input files.
#     - Updating the codeml control file so that it points to the species' MSA file.
#     - Running the codeml processes in parallel for each treefile associated with this species.
#
# Parameters:
#   $1 -> species: The species name to process.
###############################################################################
process_species() {
    local species="$1"  # Species name being processed.
    
    # Define paths for output and tree files for this species.
    local species_output="$output_dir/$species"
    local species_tree_dir="$tree_dir/$species"
    
    # Find the species-specific MSA file. The file must have the pattern "${species}_msa.best.fas".
    local msa_file
    msa_file=$(find "$msa_dir" -name "${species}_msa.best.fas" -print -quit)
    
    # Warn and skip if the MSA file is not found.
    if [ ! -f "$msa_file" ]; then
        echo "Warning: MSA file for $species not found. Skipping..."
        return
    fi
    # Warn and skip if the species-specific tree directory is missing.
    if [ ! -d "$species_tree_dir" ]; then
        echo "Warning: Tree directory for $species not found. Skipping..."
        return
    fi
    
    # Create an output directory for this species and copy the required files.
    mkdir -p "$species_output"
    cp "$msa_file" "$species_output/aligned.fas"
    cp "$base_ctl_file" "$species_output/"
    
    # Update the codeml control file (within the species output directory)
    # so that the seqfile is set to "aligned.fas" (the copied MSA).
    sed -i -E 's|^[[:space:]]*seqfile[[:space:]]*=.*|seqfile = aligned.fas|' "$species_output/codeml.ctl"
    
    # Copy all treefiles for this species into the species output directory.
    cp "$species_tree_dir"/*.treefile "$species_output/"
    
    # Change to the species output directory.
    cd "$species_output"
    # Gather the list of all treefiles now present in this directory.
    treefiles=($(ls *.treefile))
    
    # Use xargs to run the codeml function in parallel for each treefile.
    # The flag -n 1 passes one treefile at a time, and -P "$inner_parallel" sets the maximum parallel jobs.
    printf "%s\n" "${treefiles[@]}" | xargs -n 1 -P "$inner_parallel" -I{} bash -c "run_codeml_for_treefile \"{}\" \"$species\" \"$species_output\""
    
    echo "Completed processing for $species"
}
# Export the function and required environment variables so they are available to xargs subshells.
export -f process_species
export msa_dir tree_dir output_dir base_ctl_file inner_parallel

###############################################################################
# MAIN SCRIPT EXECUTION:
###############################################################################

# Get the list of species from the filenames present in the MSA directory.
# It lists all files matching *_msa.best.fas and strips the directory and suffix to leave the species name.
species_list=$(ls "$msa_dir"/*_msa.best.fas | sed 's|.*/||' | sed 's/_msa\.best\.fas//')

# Use xargs to process each species in parallel based on the number specified in num_parallel.
echo "$species_list" | xargs -n 1 -P "$num_parallel" -I{} bash -c "process_species \"{}\""

# Notify once all species processing is completed.
echo "All species processing completed."
