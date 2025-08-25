#!/bin/bash
#================================================================================
# Master runner script
#
# This script runs all other scripts sequentially in the correct order:
# 1. script0.sh -> script0.5.sh
# 2. script1.sh -> glue.sh (creates 'analysis' folder)
# 3. cd into analysis folder -> script2.sh -> script8.sh sequentially
#
# It shows running status and timestamps, and logs all output into master_log.txt
#================================================================================

set -e  # Exit on any error

# Define master log
MASTER_LOG="master_log.txt"
echo "=================== Master run started: $(date) ===================" > "$MASTER_LOG"

# Function to run a script and log its output
run_script() {
    local script_name="$1"
    echo "--------------------------------------------------" | tee -a "$MASTER_LOG"
    echo "Running $script_name at $(date)" | tee -a "$MASTER_LOG"
    START_TIME=$(date +%s)

    if [ ! -x "$script_name" ]; then
        echo "Error: $script_name not found or not executable!" | tee -a "$MASTER_LOG"
        exit 1
    fi

    # Run the script and append both stdout and stderr to master log
    ./"$script_name" 2>&1 | tee -a "$MASTER_LOG"

    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    echo "Completed $script_name at $(date) (Elapsed time: ${ELAPSED}s)" | tee -a "$MASTER_LOG"
    echo "" | tee -a "$MASTER_LOG"
}

#================================================================================
# Step 1: Run script0.sh and script0.5.sh
#================================================================================
run_script "script0.sh"
run_script "script0.5.sh"

#================================================================================
# Step 2: Run script1.sh and glue.sh
#================================================================================
run_script "script1.sh"
run_script "glue.sh"

# Ensure analysis folder exists and move into it
ANALYSIS_DIR="analysis"
if [ ! -d "$ANALYSIS_DIR" ]; then
    echo "Error: Glue script did not create '$ANALYSIS_DIR' folder!" | tee -a "$MASTER_LOG"
    exit 1
fi

cd "$ANALYSIS_DIR"

#================================================================================
# Step 3: Run script2.sh to script8.sh sequentially inside analysis folder
#================================================================================
for i in {2..8}; do
    run_script "script${i}.sh"
done

#================================================================================
# All scripts completed
#================================================================================
echo "=================== Master run completed: $(date) ===================" | tee -a "../$MASTER_LOG"
