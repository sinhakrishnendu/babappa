#!/bin/bash
# Launcher for Babappa v2.0

# Activate conda
source /home/krishnendu/miniconda3/etc/profile.d/conda.sh
conda activate babappa

# Move to project folder
cd /mnt/d/babappa_build

# Start backend & GUI
python3 main_api.py & python3 babappa_gui.py
