# LRT analysis with BH correction for site models
import pandas as pd
import scipy.stats as stats
from statsmodels.stats.multitest import multipletests
import os
import sys

# Get CSV file path from arguments
if len(sys.argv) < 2:
    raise FileNotFoundError("No CSV file provided.")

csv_file = sys.argv[1]

# Debugging print
print(f"Checking file: {csv_file}")

# Check if the file exists
if not os.path.exists(csv_file):
    raise FileNotFoundError(f"File not found: {csv_file}")

# Load the CSV
df = pd.read_csv(csv_file)

# Debugging print
print("CSV content preview:")
print(df.head())

# Check expected columns
expected_columns = {"Model", "lnL", "np"}
if not expected_columns.issubset(df.columns):
    raise ValueError("CSV file does not contain the expected columns.")

print("CSV successfully loaded and contains required columns!")

# Define model comparisons
comparisons = [
    ("Model 0:", "Model 1:"),
    ("Model 1:", "Model 2:"),
    ("Model 0:", "Model 3:"),
    ("Model 7:", "Model 8:")
]

lrt_results = []

# Perform LRT for each comparison
for null_model, alt_model in comparisons:
    if null_model in df["Model"].values and alt_model in df["Model"].values:
        lnL0 = df.loc[df["Model"] == null_model, "lnL"].values[0]
        lnL1 = df.loc[df["Model"] == alt_model, "lnL"].values[0]
        np0 = df.loc[df["Model"] == null_model, "np"].values[0]
        np1 = df.loc[df["Model"] == alt_model, "np"].values[0]
        
        # Compute test statistic
        LRT_stat = 2 * (lnL1 - lnL0)
        df_diff = np1 - np0
        
        # Compute p-value
        p_value = stats.chi2.sf(LRT_stat, df_diff)
        lrt_results.append((null_model, alt_model, LRT_stat, df_diff, p_value))

# Convert results to DataFrame
lrt_df = pd.DataFrame(lrt_results, columns=["Null Model", "Alternative Model", "LRT Statistic", "df", "p-value"])

# Apply Benjamini-Hochberg correction
lrt_df["BH-corrected p-value"] = multipletests(lrt_df["p-value"], method="fdr_bh")[1]

# Save results to CSV
output_file = "lrt_results.csv"
lrt_df.to_csv(output_file, index=False)

# Display results
print(f"Analysis complete. Results saved to {output_file}")
print(lrt_df)
