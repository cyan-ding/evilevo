🚀 Hackathon Detection Strategy (6 Hours)

Layer	Primary Heuristic Focus	Key Tool / Library	Difficulty
Layer 1	Direct Threat Similarity (Known Pathogens)	BLAST+ (Command Line) & Custom Python Script	Easy (1-2 hours)
Layer 3	Host Adaptability (Eukaryotic Expression)	Biopython & JASPAR/Promoter 2.0	Easy-Medium (1-2 hours)

1. Layer 1: Direct Threat Similarity (The Baseline)

The fastest and most critical check: Does the sequence look like a known pathogen?

A. Heuristics

    Whole-Genome Homology: High sequence identity (e.g., >85% over >1000 bp) to any virus on the Select Agent List or a current Public Health Emergency of International Concern (PHEIC).

    Oligonucleotide/Fragment Check: High identity to short, highly conserved, pathogenic regions (e.g., a viral packaging signal or a replication initiation site).

B. Tools and Implementation

Tool	Purpose	Implementation Notes
BLAST+ (Command Line)	Highly optimized sequence alignment.	Pre-download a small, targeted "database of concern" (DBC) containing only viral Select Agents (e.g., Ebola, Marburg, Variola, highly pathogenic flu). This avoids slow searching against the entire NCBI database.
Python (subprocess & XML Parser)	Run BLAST command and parse output.	Your Python script will feed the query sequence to blastn, collect the XML output, and search for hits with high %-identity and coverage.
Biopython (SeqUtils.GC / Custom Script)	Basic GC Content Check (Bonus).	Calculate the GC content of the viral genome. A content highly optimized for mammalian cells (~40-50% GC for humans) is a flag, as many native viruses have varying (sometimes very low) GC content.

C. Difficulty: Easy (Focus on the output parser)

The difficulty is not running BLAST, but setting up the targeted database and writing a robust parser to interpret the results and assign a risk score based on the %-identity and the identity of the top hit.

2. Layer 3: Host Adaptability and Assembly

This layer looks for elements that maximize the virus's ability to be expressed and replicated in a target eukaryotic host (like human cells), which is a clear sign of malign intent.

A. Heuristics

    Strong Eukaryotic Promoters: Presence of strong viral or mammalian promoters/enhancers (e.g., CMV, SV40, or Pol II promoters) adjacent to the viral genes.

    Codon Optimization: Use of codons that are preferred by the target host (e.g., Homo sapiens), indicating a design intended for high-efficiency protein production.

B. Tools and Implementation

Tool	Purpose	Implementation Notes
Promoter 2.0 (Local/Web) or JASPAR (API/DB)	Predicts Pol II eukaryotic promoter sites.	Use a local implementation of a simple neural network predictor (if available) or, more reliably, use the JASPAR database (via API or local files) to search for Transcription Factor Binding Sites (TFBS) known to be associated with strong mammalian gene expression (e.g., NF-kB, AP-1 sites).
Custom Python Script (Codon Optimization Index)	Calculate the Codon Adaptation Index (CAI).	Create a small file of the Optimal Codon Usage for Homo sapiens. Your script will calculate the CAI of the viral genes. A high CAI (close to 1.0) is a major flag for intentional optimization for human cells.
Python (re module)	Search for common vector components (Assembly Flag).	Use simple Regular Expressions (re) to search for tell-tale sequences like common restriction sites (used for assembly) or remnants of common cloning vector backbones (e.g., a specific antibiotic resistance gene).

C. Difficulty: Easy-Medium (CAI is easy; TFBS/Promoter search adds complexity)

Calculating the CAI is mathematically simple and very fast. The TFBS/Promoter step adds time, but you can simplify it to a search for a few well-known, high-risk promoter sequences.

💡 Hackathon Execution Strategy

    Preparation (Pre-Hackathon): Download and install all command-line tools (BLAST+). Curate your small, high-priority databases (DBC, Human Codon Usage Table).

    Hour 1: Setup & Layer 1: Write the Python script to take FASTA input and execute BLAST+ against your DBC. Focus on the scoring/reporting logic.

    Hour 2-3: Layer 3: Implement the CAI calculation and the Promoter/TFBS search.

    Hour 4-5: Integration: Integrate all layers into a single function that returns a cumulative risk score.

    Hour 6: Polish & Demo: Debug, create a simple command-line interface, and prepare the final presentation.