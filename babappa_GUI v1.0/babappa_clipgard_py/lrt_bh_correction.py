import os
import pandas as pd
import numpy as np
from scipy.stats import chi2
from statsmodels.stats.multitest import multipletests  # Benjamini-Hochberg correction
import sys, io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Get the current working directory
directory = os.getcwd()
print(f"Checking directory: {directory}")

# Find all CSV files in the directory
csv_files = [f for f in os.listdir(directory) if f.endswith(".csv")]
print(f"CSV files found: {csv_files}")

if not csv_files:
    print("No CSV files found. Exiting.")
    exit()

for filename in csv_files:
    file_path = os.path.join(directory, filename)
    df = pd.read_csv(file_path)
    print(f"\nProcessing file: {filename} with {len(df)} rows.")

    # Ensure necessary columns exist
    required_cols = {"Analysis", "lnL"}
    if not required_cols.issubset(df.columns):
        print(f"Skipping {filename}: Missing required columns {required_cols}")
        continue

    # Extract gene names by removing suffixes (_B, _BS, _BS_NULL)
    df["Gene"] = df["Analysis"].str.replace(r'(_B|_BS|_BS_NULL)$', '', regex=True)
    unique_genes = df["Gene"].unique()
    print(f"Unique genes found: {len(unique_genes)}")

    ###### 1. Extract M0 lnL (global null model) ######
    m0_row = df[df["Analysis"] == "M0"]  # Find the M0 entry
    if m0_row.empty:
        print("⚠️ No M0 row found! Skipping branch model analysis.")
        continue
    lnL_m0 = m0_row.iloc[0]["lnL"]
    print(f"Global M0 lnL: {lnL_m0}")

    ###### 2. Branch-site Model (Gene_BS vs Gene_BS_NULL) ######
    branchsite_results = []
    for gene in unique_genes:
        bs_data = df[df["Analysis"] == f"{gene}_BS"]
        null_data = df[df["Analysis"] == f"{gene}_BS_NULL"]

        if not bs_data.empty and not null_data.empty:
            lnL_bs = bs_data.iloc[0]['lnL']
            lnL_null = null_data.iloc[0]['lnL']
            lrt_value = 2 * (lnL_bs - lnL_null)
            p_value = 1 - chi2.cdf(lrt_value, df=1)

            branchsite_results.append({
                "Gene": gene,
                "lnL_BS": lnL_bs,
                "lnL_BS_NULL": lnL_null,
                "LRT": lrt_value,
                "p_value": p_value
            })

    branchsite_df = pd.DataFrame(branchsite_results)

    # Apply Benjamini-Hochberg Correction (SciPy's built-in)
    if not branchsite_df.empty:
        branchsite_df['FDR_Corrected_P'] = multipletests(branchsite_df["p_value"], method="fdr_bh")[1]
        branchsite_df['Significant (FDR < 0.05)'] = np.where(branchsite_df['FDR_Corrected_P'] < 0.05, "Yes", "No")

    print(f"Branchsite model results: {len(branchsite_df)} rows")

    ###### 3. Branch Model (Gene_B vs M0) ######
    branch_model_results = []
    for gene in unique_genes:
        branch_data = df[df["Analysis"] == f"{gene}_B"]

        if not branch_data.empty:
            lnL_branch = branch_data.iloc[0]['lnL']
            lrt_value_branch = 2 * (lnL_branch - lnL_m0)
            p_value_branch = 1 - chi2.cdf(lrt_value_branch, df=1)

            branch_model_results.append({
                "Gene": gene,
                "lnL_B": lnL_branch,
                "lnL_M0": lnL_m0,
                "LRT": lrt_value_branch,
                "p_value": p_value_branch
            })

    branch_model_df = pd.DataFrame(branch_model_results)

    # Apply Benjamini-Hochberg Correction
    if not branch_model_df.empty:
        branch_model_df["FDR_Corrected_P"] = multipletests(branch_model_df["p_value"], method="fdr_bh")[1]
        branch_model_df['Significant (FDR < 0.05)'] = np.where(branch_model_df['FDR_Corrected_P'] < 0.05, "Yes", "No")

    print(f"Branch model results: {len(branch_model_df)} rows")

    ######  4. Save Results to Excel ######
    output_file = f"LRT_results_{filename.replace('.csv', '.xlsx')}"
    with pd.ExcelWriter(output_file) as writer:
        if not branchsite_df.empty:
            branchsite_df.to_excel(writer, sheet_name="Branchsite_Model", index=False)
        if not branch_model_df.empty:
            branch_model_df.to_excel(writer, sheet_name="Branch_Model", index=False)

    print(f"Results saved to {output_file}")

print("LRT analysis with Benjamini-Hochberg correction completed.")
