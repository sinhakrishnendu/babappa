import re
import os
import sys

def generate_all_foreground_newicks(newick_tree, output_dir):
    # Capture any label (no parentheses/commas/colons) before a branch length
    label_pattern = r"([^():,]+)(?=:[0-9])"
    all_labels = set(re.findall(label_pattern, newick_tree))

    # Keep only labels that are not numeric-only and do not contain '/'
    labels = {
        lbl for lbl in all_labels
        if not re.fullmatch(r"[0-9.]+", lbl) and "/" not in lbl
    }

    print("Detected leaf labels:")
    for lbl in sorted(labels):
        print("  ", lbl)

    for label in labels:
        # Add #1 only to this leaf
        modified_tree = re.sub(
            rf"(?<![A-Za-z0-9_.]){re.escape(label)}(?![A-Za-z0-9_.])",
            f"{label}#1",
            newick_tree
        )

        # Safe filename
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", label)
        file_name = os.path.join(output_dir, f"{safe_name}.treefile")

        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w") as file:
            file.write(modified_tree)

        print(f"Foreground tree written: {file_name}")

    print("Foreground Branch Selection Completed.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 4GroundBranchGenerator.py <input_treefile> <output_directory>")
        sys.exit(1)

    input_treefile = sys.argv[1]
    output_dir = sys.argv[2]

    with open(input_treefile, "r") as file:
        newick_tree = file.read().strip()

    generate_all_foreground_newicks(newick_tree, output_dir)
