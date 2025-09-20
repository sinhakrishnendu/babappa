import re
import os
import sys

def generate_all_foreground_newicks(newick_tree, output_dir):
    # Only capture labels that contain a '|', i.e., gene entries, not bootstrap/support values
    label_pattern = r"([^,:()]*\|[^,:()]*)"
    labels = set(re.findall(label_pattern, newick_tree))

    for label in labels:
        modified_tree = newick_tree

        for target_label in labels:
            if target_label == label:
                modified_tree = modified_tree.replace(target_label, f"{target_label}#1")
            else:
                modified_tree = modified_tree.replace(f"{target_label}#1", target_label)  # reset

        # Make filename safe for filesystem
        safe_name = label.replace("|", "_").replace(":", "_").replace("/", "_")
        file_name = os.path.join(output_dir, f"{safe_name}.treefile")

        # Ensure parent directories exist
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        with open(file_name, "w") as file:
            file.write(modified_tree)

        print(f"Foreground tree written: {file_name}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 4GroundBranchGenerator.py <input_treefile> <output_directory>")
        sys.exit(1)

    input_treefile = sys.argv[1]
    output_dir = sys.argv[2]

    with open(input_treefile, "r") as file:
        newick_tree = file.read().strip()

    generate_all_foreground_newicks(newick_tree, output_dir)
