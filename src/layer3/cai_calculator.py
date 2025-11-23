"""
Codon Adaptation Index (CAI) Calculator

Implements the CAI algorithm from Sharp & Li (1987):
"The Codon Adaptation Index - a measure of directional synonymous codon usage bias, 
and its potential applications." Nucleic Acids Research, 15(3), 1281-1295.

CAI is calculated as the geometric mean of relative adaptiveness (w) values:
- w = frequency(codon) / max_frequency(synonymous_codons)
- CAI = (w1 × w2 × ... × wn)^(1/n)

High CAI (close to 1.0) indicates optimization for the target organism.
"""

from typing import Dict
from Bio.Seq import Seq
import os

# Human optimal codon usage table (from highly expressed genes)
# Format: {amino_acid: {codon: relative_usage_frequency}}
HUMAN_OPTIMAL_CODONS = {
    'A': {'GCC': 0.40, 'GCT': 0.28, 'GCA': 0.23, 'GCG': 0.09},
    'C': {'TGC': 0.46, 'TGT': 0.54},
    'D': {'GAC': 0.46, 'GAT': 0.54},
    'E': {'GAA': 0.42, 'GAG': 0.58},
    'F': {'TTC': 0.46, 'TTT': 0.54},
    'G': {'GGC': 0.34, 'GGT': 0.32, 'GGA': 0.25, 'GGG': 0.09},
    'H': {'CAC': 0.42, 'CAT': 0.58},
    'I': {'ATC': 0.36, 'ATT': 0.36, 'ATA': 0.28},
    'K': {'AAG': 0.58, 'AAA': 0.42},
    'L': {'CTG': 0.40, 'CTC': 0.20, 'TTA': 0.07, 'TTG': 0.13, 'CTT': 0.13, 'CTA': 0.07},
    'M': {'ATG': 1.0},
    'N': {'AAC': 0.54, 'AAT': 0.46},
    'P': {'CCC': 0.28, 'CCT': 0.28, 'CCA': 0.28, 'CCG': 0.16},
    'Q': {'CAG': 0.75, 'CAA': 0.25},
    'R': {'CGG': 0.11, 'CGA': 0.07, 'CGC': 0.19, 'CGT': 0.08, 'AGA': 0.20, 'AGG': 0.35},
    'S': {'AGC': 0.25, 'AGT': 0.15, 'TCC': 0.22, 'TCT': 0.15, 'TCA': 0.12, 'TCG': 0.11},
    'T': {'ACC': 0.36, 'ACT': 0.24, 'ACA': 0.28, 'ACG': 0.12},
    'V': {'GTG': 0.47, 'GTC': 0.20, 'GTT': 0.18, 'GTA': 0.15},
    'W': {'TGG': 1.0},
    'Y': {'TAC': 0.44, 'TAT': 0.56},
    '*': {'TAA': 0.61, 'TAG': 0.09, 'TGA': 0.30},  # Stop codons
}


def get_optimal_codon_usage() -> Dict[str, Dict[str, float]]:
    """
    Returns the optimal codon usage table for Homo sapiens.
    You can modify this or load from a file for other organisms.
    """
    return HUMAN_OPTIMAL_CODONS


def calculate_cai(sequence: str, codon_table: Dict[str, Dict[str, float]] = None) -> float:
    """
    Calculate Codon Adaptation Index (CAI) for a DNA sequence.
    
    Implements the algorithm from Sharp & Li (1987). The codon usage table
    should contain frequencies from highly expressed genes of the target organism.
    
    CAI is calculated as the geometric mean of the relative adaptiveness
    values (w) of the codons in the sequence, where:
    - w = frequency(codon) / max_frequency(synonymous_codons_for_amino_acid)
    - CAI = (w1 × w2 × ... × wn)^(1/n)
    
    Codons not present in the reference set are excluded from the calculation.
    Stop codons are excluded.
    
    Args:
        sequence: DNA sequence string (must be length multiple of 3)
        codon_table: Codon usage table with format {amino_acid: {codon: frequency}}.
                     Frequencies should be from highly expressed genes.
                     If None, uses human optimal codons.
    
    Returns:
        CAI value between 0 and 1.0 (higher = more optimized)
        
    References:
        Sharp, P. M., & Li, W. H. (1987). The Codon Adaptation Index - a measure 
        of directional synonymous codon usage bias, and its potential applications. 
        Nucleic Acids Research, 15(3), 1281-1295.
    """
    if codon_table is None:
        codon_table = get_optimal_codon_usage()
    
    # Normalize codon table to get relative adaptiveness (w values)
    # w = frequency of codon / frequency of most common codon for that amino acid
    w_values = {}
    for aa, codons in codon_table.items():
        if aa == '*':  # Skip stop codons for CAI calculation
            continue
        max_freq = max(codons.values())
        for codon, freq in codons.items():
            w_values[codon] = freq / max_freq if max_freq > 0 else 0.0
    
    # Translate sequence to get codons
    seq = Seq(sequence.upper())
    
    # Check if sequence length is multiple of 3
    if len(seq) % 3 != 0:
        raise ValueError(f"Sequence length ({len(seq)}) must be a multiple of 3")
    
    # Extract codons
    codons = [str(seq[i:i+3]) for i in range(0, len(seq), 3)]
    
    # Filter out stop codons and codons not in reference set
    # According to Sharp & Li (1987), codons not in reference set are excluded
    valid_codons = []
    for codon in codons:
        if codon in ['TAA', 'TAG', 'TGA']:
            break  # Stop at first stop codon
        if codon in w_values and w_values[codon] > 0:
            valid_codons.append(codon)
    
    if not valid_codons:
        return 0.0
    
    # Calculate geometric mean of w values
    # CAI = (w1 × w2 × ... × wn)^(1/n) per Sharp & Li (1987)
    import math
    product = 1.0
    for codon in valid_codons:
        w = w_values[codon]
        product *= w
    
    # Geometric mean: nth root of product
    cai = math.pow(product, 1.0 / len(valid_codons))
    
    return cai


def calculate_cai_for_orf(sequence: str, frame: int = 0) -> float:
    """
    Calculate CAI for a specific reading frame.
    
    Args:
        sequence: DNA sequence string
        frame: Reading frame (0, 1, or 2 for forward frames)
    
    Returns:
        CAI value
    """
    if frame < 0 or frame > 2:
        raise ValueError("Frame must be 0, 1, or 2")
    
    # Extract sequence for this frame
    orf_seq = sequence[frame:]
    
    # Find the longest ORF (until first stop codon)
    seq_obj = Seq(orf_seq)
    codons = [str(seq_obj[i:i+3]) for i in range(0, len(seq_obj) - len(seq_obj) % 3, 3)]
    
    # Find first stop codon
    stop_pos = len(codons)
    for i, codon in enumerate(codons):
        if codon in ['TAA', 'TAG', 'TGA']:
            stop_pos = i
            break
    
    # Calculate CAI for the ORF
    orf_sequence = ''.join(codons[:stop_pos])
    if len(orf_sequence) < 3:
        return 0.0
    
    return calculate_cai(orf_sequence)


def validate_codon_table(codon_table: Dict[str, Dict[str, float]]) -> bool:
    """
    Validate that codon table has reasonable structure.
    
    Args:
        codon_table: Codon usage table to validate
        
    Returns:
        True if table appears valid
    """
    standard_aas = set('ACDEFGHIKLMNPQRSTVWY')
    for aa, codons in codon_table.items():
        if aa != '*' and aa not in standard_aas:
            return False
        if not codons or len(codons) == 0:
            return False
        # Check that frequencies are non-negative
        if any(freq < 0 for freq in codons.values()):
            return False
    return True


if __name__ == "__main__":
    # Example usage and validation
    print("Validating codon table...")
    if validate_codon_table(HUMAN_OPTIMAL_CODONS):
        print("✓ Codon table is valid")
    else:
        print("✗ Codon table validation failed")
    
    # Test with a highly optimized sequence (all optimal codons)
    # Using human optimal codons: GCC (Ala), GAG (Glu), ATC (Ile), GAC (Asp)
    test_sequence_path = os.path.join(os.path.dirname(__file__), "..",  "test_sequence.txt")
    test_sequence_path = os.path.abspath(test_sequence_path)

    with open(test_sequence_path, "r") as f:
        # Join all non-empty lines, remove whitespace/newlines
        test_seq = "".join([line.strip() for line in f if line.strip()])
    
    # Trim sequence to multiple of 3 (required for codon-based calculations)
    remainder = len(test_seq) % 3
    if remainder != 0:
        test_seq = test_seq[:-remainder]
        print(f"Note: Trimmed sequence from {len(test_seq) + remainder} to {len(test_seq)} bases (removed {remainder} trailing base(s))")
    
    cai = calculate_cai(test_seq)
    print(f"\nCAI for optimized test sequence: {cai:.4f}")
    print("Expected: close to 1.0 (all optimal codons)")
    
    # # Test with a less optimized sequence
    # test_seq2 = "GCGGAAGATGGT"  # Using less optimal codons (12 bases = 4 codons)
    # cai2 = calculate_cai(test_seq2)
    # print(f"CAI for less optimized sequence: {cai2:.4f}")
    # print("Expected: lower than optimized sequence")

