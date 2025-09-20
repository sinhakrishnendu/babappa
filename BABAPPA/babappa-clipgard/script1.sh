#!/bin/bash

###############################################################################
# script1.sh - Run IQ-TREE2 and foreground branch selection on recombination
#              block alignments, using GNU Parallel with automatic CPU detection
###############################################################################

# ------------------ Setup Output Directories ------------------------------
mkdir -p iqtreeoutput treefiles foregroundbranch

# ------------------ Detect Number of CPUs ---------------------------------
if command -v nproc &>/dev/null; then
    TOTAL_CORES=$(nproc)
elif [[ "$(uname)" == "Darwin" ]]; then
    TOTAL_CORES=$(sysctl -n hw.ncpu)
else
    TOTAL_CORES=1
fi

# Use all cores but allow user to override by setting env vars
PARALLEL_IQTREE_JOBS=${PARALLEL_IQTREE_JOBS:-$TOTAL_CORES}
PARALLEL_JOBS=${PARALLEL_JOBS:-$TOTAL_CORES}

echo "Detected $TOTAL_CORES cores → using $PARALLEL_IQTREE_JOBS IQ-TREE jobs and $PARALLEL_JOBS foreground jobs."

# ------------------ IQ-TREE2 Section --------------------------------------
msa_files=($(find recombination_blocks -type f -name "*.fas" 2>/dev/null))
if [ ${#msa_files[@]} -eq 0 ]; then
    echo "No recombination block FASTA files found for IQ-TREE2. Exiting."
    exit 1
fi

run_iqtree() {
    local file="$1"
    local basename=$(basename "$file" .fas)
    local parentdir=$(basename "$(dirname "$file")")
    local output_folder="iqtreeoutput/${parentdir}/${basename}"

    mkdir -p "$output_folder"

    iqtree2 -s "$file" -st CODON -B 1000 -alrt 1000 -bnni -T AUTO \
        -pre "$output_folder/$basename" \
        > "$output_folder/${basename}_iqtree.log" 2>&1
}
export -f run_iqtree

parallel -j "$PARALLEL_IQTREE_JOBS" run_iqtree ::: "${msa_files[@]}"
echo "IQ-TREE2 Step Completed."

# ------------------ Tree File Collection Section --------------------------
find iqtreeoutput/ -name "*.treefile" -exec cp {} treefiles/ \;
echo "All tree files copied to treefiles/."

# ------------------ Foreground Branch Selection ---------------------------
run_foreground_branch() {
    local treefile="$1"
    local gene_name=$(basename "$treefile" .treefile)
    local output_folder="foregroundbranch/${gene_name}"

    mkdir -p "$output_folder"
    python3 4GroundBranchGenerator.py "$treefile" "$output_folder"
}
export -f run_foreground_branch

tree_files=($(ls treefiles/*.treefile 2>/dev/null))
parallel -j "$PARALLEL_JOBS" run_foreground_branch ::: "${tree_files[@]}"

echo "Foreground Branch Selection Completed."
