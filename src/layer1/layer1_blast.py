"""
Layer 1: Direct Threat Similarity Detection using BLAST

This module implements the first layer of the malicious genome detection system.
It uses BLAST+ to search query sequences against a "Database of Concern" (DBC)
containing known viral Select Agents and PHEIC pathogens.

Heuristics:
- Whole-Genome Homology: High sequence identity (>85% over >1000 bp) to known pathogens
- Oligonucleotide/Fragment Check: High identity to short, highly conserved pathogenic regions
- GC Content Check: Unusual GC content optimized for mammalian cells (~40-50%)

Risk Scoring:
- High Risk: >85% identity over >1000 bp to Select Agent
- Medium Risk: >85% identity over 100-1000 bp to Select Agent
- Low Risk: >85% identity over <100 bp or lower identity matches
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
import xml.etree.ElementTree as ET


@dataclass
class BlastHit:
    """Represents a single BLAST hit result."""
    subject_id: str
    subject_title: str
    identity: float  # Percentage identity
    alignment_length: int  # Length of alignment
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    e_value: float
    bit_score: float
    query_coverage: float  # Percentage of query covered


@dataclass
class Layer1Result:
    """Results from Layer 1 detection."""
    risk_level: str  # "HIGH", "MEDIUM", "LOW", "NONE"
    risk_score: float  # 0.0 to 1.0
    top_hit: Optional[BlastHit]
    all_hits: List[BlastHit]
    gc_content: float
    query_length: int
    warnings: List[str]
    details: Dict


# Risk thresholds based on DETECTOR.md specifications
HIGH_RISK_IDENTITY = 85.0  # >85% identity
HIGH_RISK_LENGTH = 1000  # >1000 bp
MEDIUM_RISK_LENGTH = 100  # 100-1000 bp
LOW_RISK_LENGTH = 50  # 50-100 bp

# Additional risk calculation thresholds
MEDIUM_IDENTITY_MIN = 60.0  # Minimum identity for medium risk
MODERATE_IDENTITY_MIN = 70.0  # Minimum identity for moderate similarity
DISTANT_IDENTITY_MIN = 50.0  # Minimum identity for distant similarity
SIGNIFICANT_LENGTH = 500  # Significant alignment length for medium risk
REASONABLE_LENGTH = 200  # Reasonable alignment length for low risk
SIGNIFICANT_EVALUE = 0.01  # Statistically significant E-value threshold

# Weak match detection thresholds
WEAK_MATCH_LENGTH = 100  # Below this length is considered weak
WEAK_MATCH_COVERAGE = 1.0  # Below this coverage percentage is considered weak

# Unknown viral detection thresholds
VIRAL_GENOME_MIN = 3000  # Minimum typical viral genome size (bp)
VIRAL_GENOME_MAX = 300000  # Maximum typical viral genome size (bp)
LARGE_GENOME_THRESHOLD = 300000  # Very large genome threshold
FRAGMENT_THRESHOLD = 1000  # Minimum size for viral fragment
GC_MAMMALIAN_MIN = 40.0  # Mammalian-optimized GC content minimum
GC_MAMMALIAN_MAX = 50.0  # Mammalian-optimized GC content maximum
GC_EXTREME_LOW = 30.0  # Very low GC content threshold
GC_EXTREME_HIGH = 60.0  # Very high GC content threshold

# Risk score multipliers
HIGH_RISK_MULTIPLIER = 1.0
MEDIUM_RISK_MULTIPLIER = 0.7
LOW_RISK_MULTIPLIER = 0.4
DISTANT_RISK_MULTIPLIER = 0.3
WEAK_RISK_MULTIPLIER = 0.2

# Unknown viral risk contributions
RISK_VIRAL_LENGTH = 0.25  # Risk contribution for viral-length sequence
RISK_LARGE_GENOME = 0.15  # Risk contribution for very large genome
RISK_FRAGMENT = 0.1  # Risk contribution for potential fragment
RISK_GC_MAMMALIAN = 0.3  # Risk contribution for mammalian-optimized GC
RISK_GC_EXTREME = 0.15  # Risk contribution for extreme GC content
RISK_WEAK_MATCH = 0.2  # Risk contribution for weak matches

# Unknown viral risk level thresholds
UNKNOWN_MEDIUM_THRESHOLD = 0.4  # Baseline risk for medium risk level
UNKNOWN_LOW_THRESHOLD = 0.25  # Baseline risk for low risk level

# file paths
DBC_DIR = "/home/ubuntu/cyan/evilevo/dbc"
DBC_FILE = f"{DBC_DIR}/dbc"  # BLAST database path (without extension)
FASTA_PATH = f"{DBC_DIR}/dbc_sequences.fasta"


def check_blast_installed() -> bool:
    """Check if BLAST+ is installed and accessible."""
    try:
        result = subprocess.run(
            ["blastn", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def calculate_gc_content(sequence: str) -> float:
    """
    Calculate GC content of a DNA sequence.
    
    Args:
        sequence: DNA sequence string
        
    Returns:
        GC content as percentage (0-100)
    """
    return gc_fraction(sequence.upper()) * 100.0


def run_blast(
    query_sequence: str,
    database_path: str,
    output_format: str = "5",  # XML format
    evalue: float = 10.0,  # More permissive E-value to catch distant similarities
    max_target_seqs: int = 50,  # Increased to see more potential matches
    word_size: int = 11,
    task: str = "blastn"
) -> str:
    """
    Run BLAST search against a local database.
    
    Args:
        query_sequence: DNA sequence to search
        database_path: Path to BLAST database (without extension)
        output_format: BLAST output format ("5" = XML)
        evalue: E-value threshold
        max_target_seqs: Maximum number of target sequences to return
        word_size: Word size for BLAST
        task: BLAST task type (blastn, blastn-short, etc.)
        
    Returns:
        BLAST XML output as string
        
    Raises:
        RuntimeError: If BLAST execution fails
    """
    if not check_blast_installed():
        raise RuntimeError("BLAST+ is not installed. Please install ncbi-blast+")
    
    # Check if database exists
    db_files = [f"{database_path}.{ext}" for ext in ["nhr", "nin", "nsq"]]
    missing_files = [f for f in db_files if not os.path.exists(f)]
    if missing_files:
        raise FileNotFoundError(
            f"BLAST database not found at {database_path}. "
            f"Expected files: {', '.join(db_files)}"
        )
    
    # Create temporary file for query
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as tmp_query:
        tmp_query.write(f">query\n{query_sequence}\n")
        tmp_query_path = tmp_query.name
    
    try:
        # Run BLAST
        cmd = [
            "blastn",
            "-query", tmp_query_path,
            "-db", database_path,
            "-outfmt", output_format,
            "-evalue", str(evalue),
            "-max_target_seqs", str(max_target_seqs),
            "-word_size", str(word_size),
            "-task", task
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"BLAST failed with return code {result.returncode}.\n"
                f"Error: {result.stderr}"
            )
        
        return result.stdout
        
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_query_path):
            os.unlink(tmp_query_path)


def parse_blast_xml(xml_output: str, query_length: int) -> List[BlastHit]:
    """
    Parse BLAST XML output and extract hit information.
    
    Args:
        xml_output: BLAST XML output string
        query_length: Length of the query sequence
        
    Returns:
        List of BlastHit objects
    """
    hits = []
    
    try:
        # Parse XML using ElementTree (more robust than NCBIXML for our needs)
        root = ET.fromstring(xml_output)
        
        # Check for BlastOutput_iterations
        iterations = root.findall(".//Iteration")
        
        # Find all hits
        for iteration in iterations:
            hits_in_iteration = iteration.findall(".//Hit")
            for hit in hits_in_iteration:
                subject_id = hit.find("Hit_id").text if hit.find("Hit_id") is not None else "unknown"
                subject_def = hit.find("Hit_def").text if hit.find("Hit_def") is not None else "unknown"
                
                # Process all HSPs (High-Scoring Pairs) for this hit
                for hsp in hit.findall(".//Hsp"):
                    identity = float(hsp.find("Hsp_identity").text) if hsp.find("Hsp_identity") is not None else 0.0
                    align_len = int(hsp.find("Hsp_align-len").text) if hsp.find("Hsp_align-len") is not None else 0
                    query_start = int(hsp.find("Hsp_query-from").text) if hsp.find("Hsp_query-from") is not None else 0
                    query_end = int(hsp.find("Hsp_query-to").text) if hsp.find("Hsp_query-to") is not None else 0
                    subject_start = int(hsp.find("Hsp_hit-from").text) if hsp.find("Hsp_hit-from") is not None else 0
                    subject_end = int(hsp.find("Hsp_hit-to").text) if hsp.find("Hsp_hit-to") is not None else 0
                    evalue = float(hsp.find("Hsp_evalue").text) if hsp.find("Hsp_evalue") is not None else 1.0
                    bit_score = float(hsp.find("Hsp_bit-score").text) if hsp.find("Hsp_bit-score") is not None else 0.0
                    
                    # Calculate percentage identity
                    if align_len > 0:
                        pct_identity = (identity / align_len) * 100.0
                    else:
                        pct_identity = 0.0
                    
                    # Calculate query coverage
                    query_coverage = ((query_end - query_start + 1) / query_length) * 100.0 if query_length > 0 else 0.0
                    
                    hit_obj = BlastHit(
                        subject_id=subject_id,
                        subject_title=subject_def,
                        identity=pct_identity,
                        alignment_length=align_len,
                        query_start=query_start,
                        query_end=query_end,
                        subject_start=subject_start,
                        subject_end=subject_end,
                        e_value=evalue,
                        bit_score=bit_score,
                        query_coverage=query_coverage
                    )
                    
                    hits.append(hit_obj)
    
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse BLAST XML: {e}")
    
    return hits


def _calculate_hit_risk(hit: BlastHit, query_length: int) -> Tuple[str, float]:
    """
    Calculate risk level and score for a single BLAST hit.
    
    Returns:
        Tuple of (risk_level, risk_score)
    """
    # Base score calculation: identity * coverage
    coverage = hit.alignment_length / query_length if query_length > 0 else 0.0
    base_score = (hit.identity / 100.0) * coverage
    
    # Determine risk level and apply multiplier
    if hit.identity >= HIGH_RISK_IDENTITY and hit.alignment_length >= HIGH_RISK_LENGTH:
        return "HIGH", min(1.0, base_score * HIGH_RISK_MULTIPLIER)
    elif hit.identity >= HIGH_RISK_IDENTITY and hit.alignment_length >= MEDIUM_RISK_LENGTH:
        return "MEDIUM", min(MEDIUM_RISK_MULTIPLIER, base_score * MEDIUM_RISK_MULTIPLIER)
    elif (MEDIUM_IDENTITY_MIN <= hit.identity < HIGH_RISK_IDENTITY and 
          hit.alignment_length >= SIGNIFICANT_LENGTH):
        return "MEDIUM", min(MEDIUM_RISK_MULTIPLIER, base_score * MEDIUM_RISK_MULTIPLIER)
    elif hit.identity >= HIGH_RISK_IDENTITY:
        return "LOW", min(LOW_RISK_MULTIPLIER, base_score * LOW_RISK_MULTIPLIER)
    elif hit.identity >= MODERATE_IDENTITY_MIN and hit.alignment_length >= LOW_RISK_LENGTH:
        return "LOW", min(LOW_RISK_MULTIPLIER, base_score * LOW_RISK_MULTIPLIER)
    elif hit.identity >= DISTANT_IDENTITY_MIN and hit.alignment_length >= REASONABLE_LENGTH:
        return "LOW", min(DISTANT_RISK_MULTIPLIER, base_score * DISTANT_RISK_MULTIPLIER)
    elif hit.e_value < SIGNIFICANT_EVALUE:
        return "LOW", min(WEAK_RISK_MULTIPLIER, base_score * WEAK_RISK_MULTIPLIER)
    
    return "NONE", 0.0


def _assess_unknown_viral_risk(
    query_length: int, 
    gc_content: float, 
    is_weak_match: bool
) -> Tuple[float, List[str]]:
    """
    Assess risk for unknown viral sequences based on sequence characteristics.
    
    Returns:
        Tuple of (baseline_risk, risk_factors)
    """
    baseline_risk = 0.0
    risk_factors = []
    
    # Check sequence length
    if VIRAL_GENOME_MIN <= query_length <= VIRAL_GENOME_MAX:
        baseline_risk += RISK_VIRAL_LENGTH
        risk_factors.append(f"Sequence length ({query_length:,} bp) is within typical viral genome range")
    elif query_length > LARGE_GENOME_THRESHOLD:
        baseline_risk += RISK_LARGE_GENOME
        risk_factors.append(f"Very long sequence ({query_length:,} bp) - could be large viral genome")
    elif query_length >= FRAGMENT_THRESHOLD:
        baseline_risk += RISK_FRAGMENT
        risk_factors.append(f"Sequence length ({query_length:,} bp) could be viral fragment")
    
    # Check GC content
    if GC_MAMMALIAN_MIN <= gc_content <= GC_MAMMALIAN_MAX:
        baseline_risk += RISK_GC_MAMMALIAN
        risk_factors.append(
            f"GC content ({gc_content:.1f}%) in mammalian-optimized range "
            f"({GC_MAMMALIAN_MIN}-{GC_MAMMALIAN_MAX}%)"
        )
    elif gc_content < GC_EXTREME_LOW or gc_content > GC_EXTREME_HIGH:
        baseline_risk += RISK_GC_EXTREME
        risk_factors.append(
            f"Unusual GC content ({gc_content:.1f}%) - many viruses have extreme GC content"
        )
    
    # Weak matches are a risk factor
    if is_weak_match:
        baseline_risk += RISK_WEAK_MATCH
        risk_factors.append("Weak/spurious database matches suggest novel or engineered virus")
    
    return baseline_risk, risk_factors


def calculate_risk_score(
    hits: List[BlastHit], 
    query_length: int,
    gc_content: float = 0.0,
    check_unknown_viral: bool = True
) -> Tuple[str, float, List[str]]:
    """
    Calculate risk level and score based on BLAST hits.
    
    Risk levels:
    - HIGH: >85% identity over >1000 bp to Select Agent
    - MEDIUM: >85% identity over 100-1000 bp, OR 60-85% identity over >500 bp, 
              OR unknown viral with suspicious characteristics
    - LOW: >85% identity over <100 bp, OR 50-85% identity over >100 bp, 
           OR unknown viral sequence
    - NONE: No significant hits and no suspicious characteristics
    
    Args:
        hits: List of BLAST hits
        query_length: Length of query sequence
        gc_content: GC content percentage (0-100)
        check_unknown_viral: Whether to check for unknown viral sequences when matches are weak
        
    Returns:
        Tuple of (risk_level, risk_score, warnings)
    """
    warnings = []
    max_risk_score = 0.0
    risk_level = "NONE"
    
    # Check if matches are meaningful or just spurious
    best_match_length = max([hit.alignment_length for hit in hits]) if hits else 0
    best_match_identity = max([hit.identity for hit in hits]) if hits else 0.0
    total_alignment_length = sum([hit.alignment_length for hit in hits])
    query_coverage = (total_alignment_length / query_length * 100.0) if query_length > 0 else 0.0
    
    is_weak_match = (
        hits and 
        best_match_length < WEAK_MATCH_LENGTH and
        query_coverage < WEAK_MATCH_COVERAGE and
        check_unknown_viral
    )
    
    if is_weak_match:
        warnings.append(
            f"Only weak/spurious matches found (best: {best_match_identity:.1f}% identity "
            f"over {best_match_length} bp, coverage: {query_coverage:.2f}%). "
            f"Sequence may be unknown viral pathogen."
        )
    
    # Calculate risk from meaningful BLAST hits
    if hits and not is_weak_match:
        for hit in hits:
            hit_level, hit_score = _calculate_hit_risk(hit, query_length)
            
            # Only update if this hit has higher risk than current
            if hit_score > max_risk_score:
                # Respect risk level hierarchy: HIGH > MEDIUM > LOW > NONE
                if (hit_level == "HIGH" or 
                    (hit_level == "MEDIUM" and risk_level != "HIGH") or
                    (hit_level == "LOW" and risk_level not in ["HIGH", "MEDIUM"])):
                    max_risk_score = hit_score
                    risk_level = hit_level
                    
                    # Generate warning message
                    if hit_level == "HIGH":
                        warnings.append(
                            f"HIGH RISK: {hit.identity:.1f}% identity over {hit.alignment_length} bp "
                            f"to {hit.subject_title}"
                        )
                    elif hit_level == "MEDIUM":
                        if hit.identity < HIGH_RISK_IDENTITY:
                            warnings.append(
                                f"MEDIUM RISK: Moderate similarity ({hit.identity:.1f}% identity over "
                                f"{hit.alignment_length} bp) to {hit.subject_title} - may be related viral sequence"
                            )
                        else:
                            warnings.append(
                                f"MEDIUM RISK: {hit.identity:.1f}% identity over {hit.alignment_length} bp "
                                f"to {hit.subject_title}"
                            )
                    else:  # LOW
                        warnings.append(
                            f"LOW RISK: {hit.identity:.1f}% identity over {hit.alignment_length} bp "
                            f"(E-value: {hit.e_value:.2e}) to {hit.subject_title}"
                        )
    
    # Check for unknown viral characteristics if no meaningful matches
    if (not hits or is_weak_match) and check_unknown_viral:
        baseline_risk, risk_factors = _assess_unknown_viral_risk(
            query_length, gc_content, is_weak_match
        )
        
        if baseline_risk >= UNKNOWN_MEDIUM_THRESHOLD:
            if risk_level in ["NONE", "LOW"] and max_risk_score < baseline_risk:
                risk_level = "MEDIUM"
                max_risk_score = min(MEDIUM_RISK_MULTIPLIER, baseline_risk)
                warnings.append(
                    f"MEDIUM RISK: Unknown viral sequence with suspicious characteristics. "
                    f"Risk factors: {', '.join(risk_factors)}"
                )
        elif baseline_risk >= UNKNOWN_LOW_THRESHOLD:
            if risk_level == "NONE" or (risk_level == "LOW" and max_risk_score < baseline_risk):
                risk_level = "LOW"
                max_risk_score = min(LOW_RISK_MULTIPLIER, baseline_risk)
                warnings.append(
                    f"LOW RISK: Unknown sequence with viral characteristics. "
                    f"Risk factors: {', '.join(risk_factors)}"
                )
        elif baseline_risk > 0.0:
            if risk_level == "NONE":
                risk_level = "LOW"
                max_risk_score = baseline_risk
                warnings.append(
                    f"LOW RISK: Unknown sequence (no database match). "
                    f"Risk factors: {', '.join(risk_factors)}"
                )
        elif not hits:
            warnings.append(
                "No matches found in database and sequence lacks typical viral characteristics. "
                "This does not guarantee safety - sequence may be a novel or engineered virus."
            )
    
    return risk_level, max_risk_score, warnings


def detect_layer1(
    query_sequence: str,
    database_path: str,
    check_gc: bool = True,
    gc_warning_threshold: Tuple[float, float] = (40.0, 50.0)
) -> Layer1Result:
    """
    Main function for Layer 1 detection.
    
    Args:
        query_sequence: DNA sequence to analyze (can be multi-line)
        database_path: Path to BLAST database (without extension)
        check_gc: Whether to check GC content
        gc_warning_threshold: (min, max) GC content range that triggers warning
        
    Returns:
        Layer1Result object with risk assessment
    """
    # Clean and validate sequence
    query_sequence = query_sequence.upper().replace('\n', '').replace(' ', '')
    query_sequence = ''.join(c for c in query_sequence if c in 'ATCGN')
    
    if len(query_sequence) < 20:
        return Layer1Result(
            risk_level="NONE",
            risk_score=0.0,
            top_hit=None,
            all_hits=[],
            gc_content=0.0,
            query_length=len(query_sequence),
            warnings=["Query sequence too short for meaningful BLAST analysis"],
            details={}
        )
    
    query_length = len(query_sequence)
    warnings = []
    details = {}
    
    # Calculate GC content
    gc_content = calculate_gc_content(query_sequence)
    if check_gc:
        if gc_warning_threshold[0] <= gc_content <= gc_warning_threshold[1]:
            warnings.append(
                f"GC content ({gc_content:.1f}%) is in mammalian-optimized range "
                f"({gc_warning_threshold[0]}-{gc_warning_threshold[1]}%), "
                "which may indicate intentional optimization for human cells."
            )
    
    # Run BLAST
    try:
        blast_xml = run_blast(query_sequence, database_path)
        hits = parse_blast_xml(blast_xml, query_length)
        
        # Sort hits by bit score (best first)
        hits.sort(key=lambda x: x.bit_score, reverse=True)
        
        # Calculate risk (pass GC content for unknown viral detection)
        risk_level, risk_score, risk_warnings = calculate_risk_score(
            hits, query_length, gc_content=gc_content, check_unknown_viral=True
        )
        warnings.extend(risk_warnings)
        
        top_hit = hits[0] if hits else None
        
        details = {
            "num_hits": len(hits),
            "blast_evalue_threshold": 10.0,  # More permissive to catch distant similarities
            "gc_content": gc_content,
            "query_length": query_length
        }
        
    except Exception as e:
        warnings.append(f"BLAST analysis failed: {str(e)}")
        hits = []
        top_hit = None
        risk_level = "NONE"
        risk_score = 0.0
        details = {"error": str(e)}
    
    return Layer1Result(
        risk_level=risk_level,
        risk_score=risk_score,
        top_hit=top_hit,
        all_hits=hits,
        gc_content=gc_content,
        query_length=query_length,
        warnings=warnings,
        details=details
    )


def detect_layer1_from_fasta(
    fasta_path: str,
    database_path: str,
    check_gc: bool = True
) -> Dict[str, Layer1Result]:
    """
    Run Layer 1 detection on all sequences in a FASTA file.
    
    Args:
        fasta_path: Path to input FASTA file
        database_path: Path to BLAST database (without extension)
        check_gc: Whether to check GC content
        
    Returns:
        Dictionary mapping sequence IDs to Layer1Result objects
    """
    results = {}
    
    try:
        for record in SeqIO.parse(fasta_path, "fasta"):
            sequence = str(record.seq)
            result = detect_layer1(sequence, database_path, check_gc=check_gc)
            results[record.id] = result
    except Exception as e:
        raise ValueError(f"Failed to read FASTA file {fasta_path}: {e}")
    
    return results


def create_blast_database(
    fasta_path: str,
    database_name: str,
    db_type: str = "nucl"
) -> str:
    """
    Create a BLAST database from a FASTA file.
    
    Args:
        fasta_path: Path to input FASTA file
        database_name: Name for the output database (without extension)
        db_type: Database type ("nucl" for nucleotide, "prot" for protein)
        
    Returns:
        Path to created database (without extension)
    """
    if not check_blast_installed():
        raise RuntimeError("BLAST+ is not installed. Please install ncbi-blast+")
    
    if not os.path.exists(fasta_path):
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")
    
    # Run makeblastdb
    cmd = [
        "makeblastdb",
        "-in", fasta_path,
        "-dbtype", db_type,
        "-out", database_name,
        "-title", f"Database of Concern: {database_name}"
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode != 0:
        raise RuntimeError(
            f"makeblastdb failed with return code {result.returncode}.\n"
            f"Error: {result.stderr}"
        )
    
    return database_name


if __name__ == "__main__":
    # Example usage
    print("Layer 1 BLAST Detection Module")
    print("=" * 50)
    
    # Check BLAST installation
    if check_blast_installed():
        print("✓ BLAST+ is installed")
    else:
        print("✗ BLAST+ is not installed")
        print("  Install with: sudo apt-get install ncbi-blast+")
    
    # Create database if it doesn't exist
    db_files = [f"{DBC_FILE}.{ext}" for ext in ["nhr", "nin", "nsq"]]
    if not all(os.path.exists(f) for f in db_files):
        print(f"\nCreating BLAST database from {FASTA_PATH}...")
        create_blast_database(FASTA_PATH, DBC_FILE)
        print("✓ Database created successfully")
    else:
        print(f"\n✓ BLAST database already exists at {DBC_FILE}")
    
    # Example: Run detection
    print(f"\n{'='*50}")
    print("Running BLAST Detection")
    print(f"{'='*50}")
    
    test_sequence_path = os.path.join(os.path.dirname(__file__), "..",  "test_2.txt")
    test_sequence_path = os.path.abspath(test_sequence_path)

    with open(test_sequence_path, "r") as f:
        # Join all non-empty lines, remove whitespace/newlines, and extract first 500 bp
        test_sequence = "".join([line.strip() for line in f if line.strip()])
    
    result = detect_layer1(test_sequence, DBC_FILE)
    
    print(f"\n{'='*50}")
    print("Results")
    print(f"{'='*50}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Risk Score: {result.risk_score:.3f}")
    print(f"GC Content: {result.gc_content:.1f}%")
    print(f"Query Length: {result.query_length} bp")
    print(f"Number of Hits: {len(result.all_hits)}")
    
    if result.top_hit:
        print(f"\nTop Hit:")
        print(f"  Subject: {result.top_hit.subject_title}")
        print(f"  Identity: {result.top_hit.identity:.2f}%")
        print(f"  Alignment Length: {result.top_hit.alignment_length} bp")
        print(f"  E-value: {result.top_hit.e_value:.2e}")
        print(f"  Bit Score: {result.top_hit.bit_score:.2f}")
    
    if result.details:
        print(f"\nDetails:")
        for key, value in result.details.items():
            print(f"  {key}: {value}")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    else:
        print("\nNo warnings.")

