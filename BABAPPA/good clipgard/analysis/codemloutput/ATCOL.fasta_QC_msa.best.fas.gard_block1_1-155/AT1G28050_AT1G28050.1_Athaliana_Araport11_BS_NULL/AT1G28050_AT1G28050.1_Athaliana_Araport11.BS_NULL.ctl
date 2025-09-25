seqfile = aligned.fas
treefile = AT1G28050_AT1G28050.1_Athaliana_Araport11.treefile
      outfile = output.txt            * Path to the output file
   
        noisy = 0              * How much rubbish on the screen
      verbose = 1              * More or less detailed report

      seqtype = 1              * Data type
        ndata = 1           * Number of data sets or loci
        icode = 0              * Genetic code 
    cleandata = 0              * Remove sites with ambiguity data?
		
model = 2
NSsites = 2
    CodonFreq = 7        * Codon frequencies
      estFreq = 0        * Use observed freqs or estimate freqs by ML
        clock = 0          * Clock model
fix_omega = 1
omega = 1
 RateAncestor = 0   * (0,1,2): rates (alpha>0) or ancestral states
