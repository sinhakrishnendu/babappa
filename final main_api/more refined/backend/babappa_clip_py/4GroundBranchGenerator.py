import re
import os
import sys

def generate_all_foreground_newicks(newick_tree, output_dir):
    # Find all gene names using regex
    gene_pattern = r"([A-Za-z][A-Za-z0-9_.-]*)"
    genes = set(re.findall(gene_pattern, newick_tree))  # Use set to avoid duplicates
    
    for gene in genes:
        modified_tree = newick_tree
        
        for target_gene in genes:
            if target_gene == gene:
                modified_tree = modified_tree.replace(target_gene, f"{target_gene}#1")
            else:
                modified_tree = modified_tree.replace(f"{target_gene}#1", target_gene)  # Remove any previous #1 markings

        # Save the modified tree in the foreground branch subfolder
        os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
        file_name = os.path.join(output_dir, f"{gene}.treefile")
        with open(file_name, "w") as file:
            file.write(modified_tree)
        print(f"File {file_name} created successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 4GroundBranchGenerator.py <input_treefile> <output_directory>")
        sys.exit(1)

    input_treefile = sys.argv[1]
    output_dir = sys.argv[2]

    with open(input_treefile, "r") as file:
        newick_tree = file.read().strip()

    generate_all_foreground_newicks(newick_tree, output_dir)
