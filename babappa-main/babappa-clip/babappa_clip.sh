#!/bin/bash
# -----------------------------------------------------------------------------
# Master pipeline for babappa_clip
# Usage: ./babappa_clip.sh <clipkit_model>
# Example: ./babappa_clip.sh kpic
# -----------------------------------------------------------------------------

# Check if model argument is supplied
if [ $# -ne 1 ]; then
    echo "Usage: $0 <clipkit_model> (e.g., kpic, gappy)"
    exit 1
fi

CLIPKIT_MODEL="$1"   # store user-supplied model

# --------------------------------------------------------------------------
# Define log file
# --------------------------------------------------------------------------
log_file="codeml_pipeline_log.txt"
echo "Pipeline started at $(date)" > "$log_file"

# --------------------------------------------------------------------------
# Define ordered scripts
# --------------------------------------------------------------------------
scripts=(script0.sh script1.sh script2.sh script3.sh script4.sh script5.sh script6.sh script7.sh script8.sh)

# --------------------------------------------------------------------------
# Format time function
# --------------------------------------------------------------------------
format_time() {
    local T=$1
    printf "%02d:%02d:%02d" $((T/3600)) $(((T%3600)/60)) $((T%60))
}

# --------------------------------------------------------------------------
# Run each script with logging
# --------------------------------------------------------------------------
run_script() {
    local script=$1
    echo "--------------------------------------------------" | tee -a "$log_file"
    echo "Starting ${script} at $(date)" | tee -a "$log_file"

    tmp_output=$(mktemp)
    start_time=$(date +%s)

    # Pass the model argument to script0.sh only
    if [ "$script" == "script0.sh" ]; then
        CLIPKIT_MODEL="$CLIPKIT_MODEL" ./"${script}" >"$tmp_output" 2>&1 &
    else
        ./"${script}" >"$tmp_output" 2>&1 &
    fi

    pid=$!
    while kill -0 "$pid" 2>/dev/null; do
        elapsed=$(( $(date +%s) - start_time ))
        formatted_elapsed=$(format_time $elapsed)
        echo -ne "Running ${script}... Elapsed time: ${formatted_elapsed}\033[0K\r"
        sleep 1
    done

    wait "$pid"
    exit_code=$?
    finish_time=$(date +%s)
    total_time=$(( finish_time - start_time ))
    formatted_total_time=$(format_time $total_time)
    echo ""

    if [ $exit_code -eq 0 ]; then
        echo "${script} completed successfully at $(date +"%H:%M:%S"). Total time: ${formatted_total_time}" | tee -a "$log_file"
    else
        echo "Error: ${script} failed with exit code ${exit_code} at $(date +"%H:%M:%S"). Total time: ${formatted_total_time}" | tee -a "$log_file"
        echo "----- Output from ${script} -----" >> "$log_file"
        cat "$tmp_output" >> "$log_file"
        echo "---------------------------------" >> "$log_file"
        rm "$tmp_output"
        exit 1
    fi

    echo "----- Output from ${script} -----" >> "$log_file"
    cat "$tmp_output" >> "$log_file"
    echo "---------------------------------" >> "$log_file"
    rm "$tmp_output"
}

# --------------------------------------------------------------------------
# Execute all scripts
# --------------------------------------------------------------------------
for script in "${scripts[@]}"; do
    if [ ! -x "$script" ]; then
        echo "Error: ${script} is missing or not executable. Aborting." | tee -a "$log_file"
        exit 1
    fi
    run_script "$script"
done

echo "--------------------------------------------------" | tee -a "$log_file"
echo "All scripts completed successfully at $(date)." | tee -a "$log_file"
