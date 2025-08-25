#!/bin/bash
# ----------------------------------------------------------------------
# Script Overview:
# This script performs quality control (QC) on sequence files and then
# runs multiple sequence alignment (MSA) using PRANK on the QC-processed
# sequences. It processes input files in parallel to optimize performance.
#
# The workflow consists of two main steps:
# 1. QC Step: Run a Python script (seqQC.py) on each input file to perform quality control.
# 2. MSA Step: Run the PRANK program for multiple sequence alignment on QC passed files.
#
# The script uses GNU Parallel to run jobs concurrently, with a job limit defined
# by the user. It also provides a message upon completion for the next analysis step.
# ----------------------------------------------------------------------

# Create required output directories if they do not exist.
# "QCseq" will contain the QC processed sequence files.
# "msa" will hold the output results from PRANK MSA.
mkdir -p QCseq msa

# Find all files in the current directory with .txt and .fasta extensions.
# The command 'ls *.txt *.fasta 2>/dev/null' lists these files.
# 2>/dev/null suppresses error messages if no files match.
input_files=($(ls *.txt *.fasta 2>/dev/null))

# Check if the input_files array is empty.
# If no files have been found, print a message and exit the script with status 1.
if [ ${#input_files[@]} -eq 0 ]; then
    echo "No input files found in the directory!"
    exit 1
fi

# Define the maximum number of parallel jobs for GNU Parallel.
# Adjust PARALLEL_JOBS if your system can handle more or fewer simultaneous processes.
PARALLEL_JOBS=1  

# ------------------ QC Step ------------------
# Define a function to run quality control (QC) on an individual file.
# This function uses a Python QC script to assess and process the sequence file.
run_qc() {
    # Accept the input file as the first argument.
    local file="$1"

    # Define the output file name:
    # The basename extracts the filename without the directory, and the extension
    # is removed (.txt) then '_QC.fasta' is appended to indicate QC processed output.
    output_file="QCseq/$(basename "$file" .txt)_QC.fasta"

    # Announce that the QC is starting for this file.
    echo "Running QC on $file..."

    # Execute the Python script 'seqQC.py' with two arguments:
    # 1. The input file (raw sequence data)
    # 2. The output file (destination for the QC passed sequences)
    python3 seqQC.py "$file" "$output_file"

    # Check if the Python command executed successfully.
    # If the exit code ($?) is 0, the QC step passed.
    if [ $? -eq 0 ]; then
        echo "QC Passed: $file -> $output_file"
    else
        echo "QC Failed: $file"
    fi
}

# Export the run_qc function to make it available to GNU Parallel.
export -f run_qc

# Use GNU Parallel to process each input file concurrently.
# The '-j' option specifies the maximum parallel jobs.
# '::: "${input_files[@]}"' supplies the list of input files to the run_qc function.
parallel -j "$PARALLEL_JOBS" run_qc ::: "${input_files[@]}"

# Indicate that the QC Step is completed.
echo "QC Step Completed."

# ------------------ PRANK MSA ------------------
# Collect all QC passed files located in the QCseq directory.
# We assume that only QC passed files from the previous step are available as .fasta files.
qc_files=($(ls QCseq/*.fasta 2>/dev/null))

# Define a function to run PRANK for multiple sequence alignment.
# This function processes each QC passed file using PRANK.
run_prank() {
    # Get the file name from the first argument passed to this function.
    local file="$1"

    # Generate the output file prefix for PRANK.
    # This creates a file prefix in the 'msa' directory, removing the .fasta extension and adding "_msa".
    output_prefix="msa/$(basename "$file" .fasta)_msa"

    # Announce that PRANK is starting for the specified file.
    echo "Running PRANK on $file..."

    # Run PRANK with the following parameters:
    # - '-d' specifies the input file (the QC passed file).
    # - '-o' sets the output file prefix.
    # - '-codon' tells PRANK to use codon-based alignment.
    # The STDOUT and STDERR are redirected to a log file with the .log extension.
    prank -d="$file" -o="$output_prefix" -codon > "${output_prefix}.log" 2>&1
}

# Export the run_prank function for use with GNU Parallel.
export -f run_prank

# Use GNU Parallel to run PRANK in parallel for each QC passed file.
parallel -j "$PARALLEL_JOBS" run_prank ::: "${qc_files[@]}"

# Indicate that the MSA step is completed.
echo "MSA Step Completed."

# Final message to inform the user that the script has completed and to run the next script.
echo "Script1 completed. Run Script2 onwards to proceed with phylogenetic analysis and selection analysis."
