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

print(f"Checking file: {csv_file}")

if not os.path.exists(csv_file):
    raise FileNotFoundError(f"File not found: {csv_file}")

# Load CSV
df = pd.read_csv(csv_file)
print("CSV content preview:")
print(df.head())

# Ensure expected columns
expected_columns = {"Model", "lnL", "np"}
if not expected_columns.issubset(df.columns):
    raise ValueError("CSV file does not contain the expected columns.")
print("CSV successfully loaded and contains required columns!")

# Strip whitespace and trailing colons from model names
df["Model"] = df["Model"].str.strip().str.rstrip(":")

# Define model comparisons
comparisons = [
    ("Model 0", "Model 1"),
    ("Model 1", "Model 2"),
    ("Model 0", "Model 3"),
    ("Model 7", "Model 8")
]

lrt_results = []

# Perform LRT for each comparison
for null_model, alt_model in comparisons:
    if null_model in df["Model"].values and alt_model in df["Model"].values:
        lnL0 = df.loc[df["Model"] == null_model, "lnL"].values[0]
        lnL1 = df.loc[df["Model"] == alt_model, "lnL"].values[0]
        np0 = df.loc[df["Model"] == null_model, "np"].values[0]
        np1 = df.loc[df["Model"] == alt_model, "np"].values[0]

        LRT_stat = 2 * (lnL1 - lnL0)
        df_diff = np1 - np0

        p_value = stats.chi2.sf(LRT_stat, df_diff)
        lrt_results.append((null_model, alt_model, LRT_stat, df_diff, p_value))

if not lrt_results:
    print("❌ No valid LRT comparisons found. BH correction skipped.")
    sys.exit(0)

# Convert to DataFrame
lrt_df = pd.DataFrame(
    lrt_results,
    columns=["Null Model", "Alternative Model", "LRT Statistic", "df", "p-value"]
)

# Apply BH correction safely
lrt_df["BH-corrected p-value"] = multipletests(lrt_df["p-value"], method="fdr_bh")[1]

# Save results
output_file = "lrt_results.csv"
lrt_df.to_csv(output_file, index=False)

print(f"✅ Analysis complete. Results saved to {output_file}")
print(lrt_df)
