#!/bin/bash
# ------------------------------------------------------------------------------
# This script processes species data for codeml analysis using M0 model.
# It automatically detects the number of blocks (FASTA files in msa/)
# and runs all blocks in parallel.
# ------------------------------------------------------------------------------

set -e  # Exit immediately on error

# ---------------------------------------------------------------------------
# Define directories
msa_dir="msa"
tree_dir="treefiles"
output_dir="codemloutput"
base_ctl_file="codeml.ctl"

# ---------------------------------------------------------------------------
# Check for required directories and files
if [ ! -d "$msa_dir" ] || [ ! -d "$tree_dir" ] || [ ! -f "$base_ctl_file" ]; then
    echo "Error: Required directories or files are missing."
    exit 1
fi

# ---------------------------------------------------------------------------
# Function: process_species
process_species() {
    species="$1"
    species_output="$output_dir/$species"

    msa_file="$msa_dir/${species}.fas"
    tree_file=$(find "$tree_dir" -name "${species}.treefile" -print -quit)

    if [ ! -f "$msa_file" ]; then
        echo "Warning: MSA file for $species not found. Skipping..."
        return
    fi
    if [ ! -f "$tree_file" ]; then
        echo "Warning: Tree file for $species not found. Skipping..."
        return
    fi

    mkdir -p "$species_output"
    cp "$msa_file" "$species_output/aligned.fas"
    cp "$tree_file" "$species_output/treefile.treefile"
    cp "$base_ctl_file" "$species_output/"

    (
        cd "$species_output"
        echo "Processing M0 model for $species"

        sed -i "s|^ *seqfile *=.*|seqfile = aligned.fas|" codeml.ctl
        sed -i "s|^ *treefile *=.*|treefile = treefile.treefile|" codeml.ctl
        sed -i "s|^ *model *=.*|model = 0|" codeml.ctl
        sed -i "s|^ *NSsites *=.*|NSsites = 0|" codeml.ctl

        m0_folder="M0"
        mkdir -p "$m0_folder"
        cp codeml.ctl "$m0_folder/M0.ctl"
        cp aligned.fas treefile.treefile "$m0_folder/"

        (cd "$m0_folder" && codeml "M0.ctl")
        echo "Completed M0 model for $species"
    )
}

export -f process_species
export msa_dir tree_dir output_dir base_ctl_file  

# ---------------------------------------------------------------------------
# Detect number of blocks and run in parallel
species_files=$(find "$msa_dir" -maxdepth 1 -name "*.fas" -printf "%f\n" | sed 's/\.fas$//')
num_parallel=$(echo "$species_files" | wc -l)
echo "Detected $num_parallel blocks. Running all in parallel."

echo "$species_files" | xargs -n 1 -P "$num_parallel" bash -c 'process_species "$@"' _

# ---------------------------------------------------------------------------
echo "All M0 model processing completed."
