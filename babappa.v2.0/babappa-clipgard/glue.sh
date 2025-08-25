#!/bin/bash

# Define the target directory
TARGET_DIR="analysis"

# Create the main analysis folder
mkdir -p "$TARGET_DIR"

echo "Creating analysis directory structure..."

# 1. Copy the entire foregroundbranch directory
cp -r foregroundbranch "$TARGET_DIR/"

# 2. Copy the entire treefiles directory
cp -r treefiles "$TARGET_DIR/"

# 3. Copy recombination_blocks contents into a new subfolder called msa inside analysis
mkdir -p "$TARGET_DIR/msa"
cp recombination_blocks/Arabidopsis_halleri/*.fas "$TARGET_DIR/msa/"
cp recombination_blocks/Arabidopsis_lyrata/*.fas "$TARGET_DIR/msa/"

# 4. Copy the listed scripts and files into analysis
cp \
  lrt_bh_correction.py\
  lrt_bh_correction.sitemodel.py\
  run_codeml.py\
  codeml.ctl \
  script2.sh \
  script3.sh \
  script4.sh \
  script5.sh \
  script6.sh \
  script7.sh \
  script8.sh \
  "$TARGET_DIR/"

echo "All files and directories copied successfully into $TARGET_DIR/"
