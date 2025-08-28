#!/bin/bash
# -------------------------------------------------------------------
# Script: babappa.sh
# Purpose: 
#   1. Collect .fasta/.fas files from the current directory
#      (where this script resides) and copy them into all 4 subfolders.
#   2. If no fasta files are found, abort the run.
#   3. Run the 4 known babappa scripts in parallel, leaving 2 cores free.
#   4. Pass MODELNAME to babappa_clip.sh.
#   5. Verbose logging.
# Usage: ./babappa.sh MODELNAME
# -------------------------------------------------------------------

# Ensure argument is supplied
if [ $# -lt 1 ]; then
    echo "Usage: $0 MODELNAME"
    exit 1
fi

MODELNAME="$1"

# Detect number of CPU cores, leaving 2 free (minimum 1 core)
TOTAL_CORES=$(nproc)
USE_CORES=$((TOTAL_CORES - 2))
if [ "$USE_CORES" -lt 1 ]; then
    USE_CORES=1
fi

echo "=================== Master run started: $(date) ==================="
echo "Total CPU cores detected: $TOTAL_CORES"
echo "Cores reserved for system: 2"
echo "Cores allocated for jobs: $USE_CORES"
echo "Model argument to pass: $MODELNAME"
echo "-------------------------------------------------------------------"

# Hardcoded scripts + folders
TARGETS=(
    "babappa-normal/babappa_normal.sh"
    "babappa-clip/babappa_clip.sh"
    "babappa-gard/babappa_gard.sh"
    "babappa-clipgard/babappa_clipgard.sh"
)
FOLDERS=(babappa-normal babappa-clip babappa-gard babappa-clipgard)

# Step 1: Collect fasta/fas files from *current* directory
echo "[INFO] Checking current directory ($(pwd)) for .fasta/.fas files..."
FASTA_FILES=( *.fasta *.fas )

# Handle case where no match is found
if [ "${FASTA_FILES[0]}" = "*.fasta" ] && [ "${FASTA_FILES[1]}" = "*.fas" ]; then
    echo "[ERROR] No .fasta or .fas files found in current directory. Aborting run."
    echo "=================== Master run aborted: $(date) ==================="
    exit 1
fi

echo "[INFO] Found ${#FASTA_FILES[@]} fasta/fas files. Copying into all target folders..."
for f in "${FASTA_FILES[@]}"; do
    if [ -f "$f" ]; then
        for d in "${FOLDERS[@]}"; do
            if [ -d "$d" ]; then
                cp -u "$f" "$d/"
                echo "[INFO] Copied $f -> $d/"
            fi
        done
    fi
done
echo "-------------------------------------------------------------------"

# Step 2: Function to run script inside its directory
run_script() {
    script="$1"
    dir=$(dirname "$script")
    base=$(basename "$script")

    if [ ! -f "$script" ]; then
        echo "[WARN] $(date): Skipping missing script: $script"
        return
    fi

    echo "-------------------------------------------------------------------"
    echo "[INFO] $(date): Preparing to run $script"
    echo "[INFO] Changing directory to: $dir"

    (
        cd "$dir" || { echo "[ERROR] Could not enter $dir"; exit 1; }

        echo "[START] $(date): Executing $base"

        if [[ "$base" == "babappa_clip.sh" ]]; then
            echo "[INFO] Passing argument: $MODELNAME"
            bash "./$base" "$MODELNAME"
        else
            bash "./$base"
        fi

        status=$?
        if [ $status -eq 0 ]; then
            echo "[DONE] $(date): $base completed successfully"
        else
            echo "[FAIL] $(date): $base exited with status $status"
        fi
    )

    echo "[INFO] Returned to parent directory: $(pwd)"
    echo "-------------------------------------------------------------------"
}
export -f run_script
export MODELNAME

# Step 3: Run scripts in parallel
printf "%s\n" "${TARGETS[@]}" | parallel -j "$USE_CORES" run_script {}

echo "=================== Master run finished: $(date) ==================="
