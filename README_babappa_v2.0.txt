# BABAPPA v2.0  
**BAsh-Based Automated Parallel Positive selection Analysis**  

BABAPPA is a fully automated, modular, and highly efficient pipeline for detecting episodic positive selection across gene families.  
Version **2.0** introduces **three flavours** of BABAPPA to support advanced sequence quality control and recombination detection strategies:  

- **babappa-normal** → classic BABAPPA pipeline (QC, codon-aware MSA, phylogeny, codeml models, LRT + BH correction).  
- **babappa-clip** → integrates [ClipKit](https://github.com/JLSteenwyk/ClipKIT) to filter MSA and improve alignment quality before codeml runs.  
- **babappa-clipgard** → combines ClipKit with [GARD](http://www.datamonkey.org/gard) recombination breakpoint detection to identify and correct for recombination blocks.  

📖 Citation:  
Krishnendu Sinha et al. (2025). **BABAPPA: BAsh-Based Automated Parallel Positive selection Analysis.** *bioRxiv*. https://doi.org/10.1101/2025.04.27.650835  

---

## ✨ Features  

- **End-to-end automation**: from raw FASTA → codeml-ready MSA → phylogeny → positive selection reports.  
- **Codon-aware alignment** using PRANK.  
- **ClipKit MSA rectification** (*clip, clipgard flavours*).  
- **GARD-based recombination block partitioning** (*clipgard flavour*).  
- **Phylogenetic inference** with IQ-TREE2.  
- **Foreground branch marking** for branch-site tests.  
- **Parallel codeml execution** with GNU Parallel.  
- **Likelihood Ratio Tests (LRTs)** and **Benjamini–Hochberg FDR corrections**.  
- **Excel reports** summarizing genes/sites under selection.  
- **Built-in stop-codon masker** (`babappa_stopcodon_masker.py`) for codeml compatibility.  

---

## 📂 Repository Structure  

```
babappa.v2.0/
│
├── babappa-normal/        # Classic BABAPPA pipeline
│   ├── babappa.sh         # Master script
│   ├── seqQC.py           # Sequence QC
│   ├── run_codeml.py      # Codeml automation
│   ├── 4GroundBranchGenerator.py
│   ├── babappa_stopcodon_masker.py
│   ├── lrt_bh_correction*.py
│   ├── merge_bh_results.py
│   └── script0.sh ... script8.sh
│
├── babappa-clip/          # BABAPPA + ClipKit
│   ├── babappa_clip.sh
│   ├── seqQC.py, run_codeml.py, ...
│   ├── babappa_stopcodon_masker.py
│   └── script0.sh ... script8.sh
│
├── babappa-clipgard/      # BABAPPA + ClipKit + GARD
│   ├── babappa_clipgard.sh
│   ├── filter_blocks.py, split_recombination_blocks.py
│   ├── glue.sh            # Recombine split block results
│   ├── seqQC.py, run_codeml.py, ...
│   └── script0.sh ... script8.sh
│
└── Example FASTAs
    ├── Arabidopsis_halleri.fasta
    └── Arabidopsis_lyrata.fasta
```

---

## ⚙️ Installation  

> **Linux / WSL (Windows users must install Ubuntu under WSL)**  

1. Install dependencies:  
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install prank iqtree paml parallel python3 python3-pip -y
   pip3 install biopython scipy statsmodels pandas openpyxl
   ```

2. Clone repository:  
   ```bash
   git clone https://github.com/sinhakrishnendu/babappa.git
   cd babappa/babappa.v2.0
   ```

3. Make scripts executable:  
   ```bash
   chmod +x babappa-normal/babappa.sh
   chmod +x babappa-clip/babappa_clip.sh
   chmod +x babappa-clipgard/babappa_clipgard.sh
   ```

---

## 🚀 Usage  

### 1. Prepare input  
Place your coding sequence (CDS) FASTA files into an `input/` folder.  

### 2. Run pipeline  
- **Classic run**:  
  ```bash
  ./babappa-normal/babappa.sh
  ```

- **With ClipKit rectification**:  
  ```bash
  ./babappa-clip/babappa_clip.sh
  ```

- **With ClipKit + GARD recombination detection**:  
  ```bash
  ./babappa-clipgard/babappa_clipgard.sh
  ```

### 3. Outputs  
Pipeline creates structured folders automatically:  
```
QCseq/  
msa/  
treefiles/  
codemloutput/  
codemlanalysis/  
BHanalysis/  
BHanalysis4sitemodel/  
sitemodel/  
sitemodelanalysis/  
SiteModelBH/  
```

---

## 📥 Input Requirements  

Input FASTA must:  
- Contain **coding sequences (CDS)** only.  
- Start with `ATG` and end with valid stop codon (`TAA`, `TAG`, `TGA`).  
- Length must be **multiple of 3** and **> 300 bp**.  
- No internal in-frame stop codons.  
- Sequences with errors or length outliers are logged and excluded.  

---

## 📊 Output Files  

- Codon-aware MSA (PRANK, optionally ClipKit-filtered).  
- Maximum likelihood trees (IQ-TREE2).  
- codeml outputs for **site, branch, branch-site** models.  
- Likelihood ratio test (LRT) results.  
- Benjamini–Hochberg corrected p-values.  
- Final Excel report (`.xlsx`) with positively selected genes/sites.  

---

## ❤️ Acknowledgment  

The name **BABAPPA** was lovingly inspired by the author’s son, whose word for “butterfly” was “babappa.”  

---

## 📜 License  

This project is licensed under the **MIT License**.  

---

**Happy Positive Selection Hunting with BABAPPA v2.0!** 🦋  
