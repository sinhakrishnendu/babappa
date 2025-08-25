#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: codeml_pipeline.sh
# Description: Master script to sequentially run codeml shell scripts (Script0.sh to Script8.sh),
#              tracking time, logging output, and stopping on error.
# -----------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Define log file
# --------------------------------------------------------------------------
log_file="codeml_pipeline_log.txt"
echo "Pipeline started at $(date)" > "$log_file"

# --------------------------------------------------------------------------
# Define an ordered array of all script names to execute
# --------------------------------------------------------------------------
scripts=(script0.sh script1.sh script2.sh script3.sh script4.sh script5.sh script6.sh script7.sh script8.sh)

# --------------------------------------------------------------------------
# Format time in hh:mm:ss
# --------------------------------------------------------------------------
format_time() {
    local T=$1
    printf "%02d:%02d:%02d" $((T/3600)) $(((T%3600)/60)) $((T%60))
}

# --------------------------------------------------------------------------
# Run each script with logging and error tracking
# --------------------------------------------------------------------------
run_script() {
    local script=$1
    echo "--------------------------------------------------" | tee -a "$log_file"
    echo "Starting ${script} at $(date)" | tee -a "$log_file"

    local tmp_output
    tmp_output=$(mktemp)

    start_time=$(date +%s)

    ./"${script}" >"$tmp_output" 2>&1 &
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
    echo ""  # clear timer line

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
# Execute all scripts in order
# --------------------------------------------------------------------------
for script in "${scripts[@]}"; do
    if [ ! -x "$script" ]; then
        echo "Error: ${script} is missing or not executable. Aborting." | tee -a "$log_file"
        exit 1
    fi
    run_script "$script"
done

# --------------------------------------------------------------------------
# Final completion message
# --------------------------------------------------------------------------
echo "--------------------------------------------------" | tee -a "$log_file"
echo "All scripts completed successfully at $(date)." | tee -a "$log_file"
