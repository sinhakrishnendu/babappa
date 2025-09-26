import os
import subprocess
import sys
import io

# Force stdout/stderr to UTF-8 (portable)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

def create_ctl_file(model_type, tree_file, alignment_file, output_file, foreground_branches, fix_omega=None, omega=None):
    ctl_content = f"""
      seqfile = {alignment_file}
      treefile = {tree_file}
      outfile = {output_file}
      noisy = 9
      verbose = 1
      runmode = 0
      seqtype = 1
      CodonFreq = 7
      clock = 0
      aaDist = 0
      model = {model_type}
      NSsites = {2 if model_type == 2 else 0}
      cleandata = 1
      fix_kappa = 0
      kappa = 2
      fix_alpha = 1
      alpha = 0
      Malpha = 0
      ncatG = 8
      getSE = 0
      RateAncestor = 0
      method = 0
    """.strip()
    
    if model_type in [1, 2]:  # Branch or Branch-site model
        ctl_content += f"\n      foreground = {' '.join(map(str, foreground_branches))}"
        if fix_omega is not None and omega is not None:
            ctl_content += f"\n      fix_omega = {fix_omega}\n      omega = {omega}"
    
    return ctl_content

def run_codeml(branch_folder, output_folder):
    tree_file = os.path.join(branch_folder, "foreground.tree")
    alignment_file = os.path.join(branch_folder, "aligned.fasta")
    
    if not os.path.exists(tree_file) or not os.path.exists(alignment_file):
        print(f"Skipping {branch_folder}, missing required files.")
        return
    
    foreground_branches = [1]  # Modify as needed
    models = {"site": 0, "branch": 1, "branch-site": 2}
    
    for model, model_type in models.items():
        model_output_folder = os.path.join(output_folder, model)
        os.makedirs(model_output_folder, exist_ok=True)
        
        output_file = os.path.join(model_output_folder, "results.txt")
        ctl_file = os.path.join(model_output_folder, "codeml.ctl")
        
        if model == "branch-site":
            # Alternative hypothesis (allows positive selection)
            with open(ctl_file, "w") as f:
                f.write(create_ctl_file(model_type, tree_file, alignment_file, output_file, foreground_branches, fix_omega=0, omega=0.5))
            print(f"Running codeml for branch-site model (alternative) in {branch_folder}...")
            subprocess.run(["codeml", ctl_file], cwd=model_output_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Null hypothesis (no positive selection, fix omega = 1)
            null_output_folder = os.path.join(output_folder, "branch-site-null")
            os.makedirs(null_output_folder, exist_ok=True)
            
            null_output_file = os.path.join(null_output_folder, "results.txt")
            null_ctl_file = os.path.join(null_output_folder, "codeml.ctl")
            
            with open(null_ctl_file, "w") as f:
                f.write(create_ctl_file(model_type, tree_file, alignment_file, null_output_file, foreground_branches, fix_omega=1, omega=1))
            print(f"Running codeml for branch-site model (null) in {branch_folder}...")
            subprocess.run(["codeml", null_ctl_file], cwd=null_output_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif model == "branch":
            # Alternative hypothesis (branch model with different ω)
            with open(ctl_file, "w") as f:
                f.write(create_ctl_file(model_type, tree_file, alignment_file, output_file, foreground_branches))
            print(f"Running codeml for branch model in {branch_folder}...")
            subprocess.run(["codeml", ctl_file], cwd=model_output_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Null hypothesis (M0 model with one ω for all branches)
            m0_output_folder = os.path.join(output_folder, "branch-null")
            os.makedirs(m0_output_folder, exist_ok=True)
            
            m0_output_file = os.path.join(m0_output_folder, "results.txt")
            m0_ctl_file = os.path.join(m0_output_folder, "codeml.ctl")
            
            with open(m0_ctl_file, "w") as f:
                f.write(create_ctl_file(0, tree_file, alignment_file, m0_output_file, foreground_branches))
            print(f"Running codeml for M0 model (null) in {branch_folder}...")
            subprocess.run(["codeml", m0_ctl_file], cwd=m0_output_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            with open(ctl_file, "w") as f:
                f.write(create_ctl_file(model_type, tree_file, alignment_file, output_file, foreground_branches))
            print(f"Running codeml for {model} model in {branch_folder}...")
            subprocess.run(["codeml", ctl_file], cwd=model_output_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 run_codeml.py <foreground_branch_folder> <output_folder>")
        sys.exit(1)
    
    branch_folder = sys.argv[1]
    output_folder = sys.argv[2]
    os.makedirs(output_folder, exist_ok=True)
    run_codeml(branch_folder, output_folder)
