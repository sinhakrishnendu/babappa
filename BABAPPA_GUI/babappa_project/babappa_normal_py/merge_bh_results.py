#!/usr/bin/env python3
import sys
import os
import pandas as pd
from glob import glob

if len(sys.argv) < 5:
    print("Usage: python merge_bh_results.py <sitemodel_dir> <BS_dir> <block_dir> <output_file>")
    sys.exit(1)

sitemodel_dir, BS_dir, block_dir, output_file = sys.argv[1:5]

def collect_results(directory, label):
    results = []
    if os.path.exists(directory):
        for csv_file in glob(os.path.join(directory, "*", "lrt_results.csv")):
            df = pd.read_csv(csv_file)
            df['Analysis_Type'] = label
            df['Source_File'] = os.path.basename(csv_file)
            results.append(df)
    return results

all_results = []
all_results.extend(collect_results(sitemodel_dir, "SiteModel"))
all_results.extend(collect_results(BS_dir, "BranchSite"))
all_results.extend(collect_results(block_dir, "Block"))

if all_results:
    final_df = pd.concat(all_results, ignore_index=True)
    final_df.to_csv(output_file, index=False)
    print(f"Consolidated results written to {output_file}")
else:
    print("No BH-corrected results found to merge.")
