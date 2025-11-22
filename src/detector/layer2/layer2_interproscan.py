"""
Layer 2: Functional Virulence Detection using InterProScan

This module implements the second layer of the malicious genome detection system.
It uses InterProScan to identify protein domains, virulence factors, and toxins
in translated DNA sequences.

Heuristics:
- Virulence Factor Domains: Presence of conserved protein domains known to be toxins,
  immune modulators, or cell-entry proteins
- Chimeric Constructs: Detection of non-viral domains (like bacterial toxins) fused to
  viral protein backbones

Risk Scoring:
- High Risk: Known toxin or high-risk virulence factor domains detected
- Medium Risk: Moderate-risk domains or immune modulators detected
- Low Risk: Low-risk domains or generic protein domains detected
"""

import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from Bio.Seq import Seq


@dataclass
class InterProHit:
    """Represents a single InterProScan hit result."""
    protein_id: str
    sequence_md5: str
    length: int
    database: str  # e.g., Pfam, ProDom, SMART
    database_accession: str
    database_description: str
    start: int
    end: int
    e_value: Optional[float]
    status: str
    date: str
    interpro_accession: Optional[str]
    interpro_description: Optional[str]
    go_terms: List[str]
    pathway: Optional[str]


@dataclass
class Layer2Result:
    """Results from Layer 2 detection."""
    risk_level: str  # "HIGH", "MEDIUM", "LOW", "NONE"
    risk_score: float  # 0.0 to 1.0
    hits: List[InterProHit]
    virulence_factors: List[str]
    toxins: List[str]
    warnings: List[str]
    details: Dict


# High-risk domain keywords (toxins, virulence factors)
HIGH_RISK_KEYWORDS = [
    'toxin', 'hemolysin', 'enterotoxin', 'neurotoxin', 'cytotoxin',
    'virulence', 'pathogenicity', 'effector', 'invasin', 'adhesin',
    'immune evasion', 'interferon antagonist', 'deubiquitinase',
    'receptor binding', 'cell entry', 'membrane fusion'
]

# Medium-risk domain keywords
MEDIUM_RISK_KEYWORDS = [
    'protease', 'nuclease', 'kinase', 'phosphatase', 'modulator',
    'regulator', 'transcriptional', 'replication'
]


def translate_dna_to_protein(dna_sequence: str, frame: int = 0) -> str:
    """
    Translate DNA sequence to protein in specified reading frame.
    
    Args:
        dna_sequence: DNA sequence string
        frame: Reading frame (0, 1, 2 for forward; 3, 4, 5 for reverse)
        
    Returns:
        Protein sequence string
    """
    seq = Seq(dna_sequence.upper())
    
    if frame >= 3:
        # Reverse complement for frames 3, 4, 5
        seq = seq.reverse_complement()
        frame = frame - 3
    
    # Extract sequence for this frame
    orf_seq = seq[frame:]

    # Pad sequence with 'N's to make it a multiple of 3 (so translation doesn't truncate codons)
    remainder = len(orf_seq) % 3
    if remainder != 0:
        orf_seq += "N" * (3 - remainder)
    
    # Translate (stop at first stop codon)
    protein = orf_seq.translate(to_stop=True)
    
    return str(protein)


def translate_all_frames(dna_sequence: str) -> Dict[int, str]:
    """
    Translate DNA sequence in all 6 reading frames.
    
    Args:
        dna_sequence: DNA sequence string
        
    Returns:
        Dictionary mapping frame number (0-5) to protein sequence
    """
    frames = {}
    for frame in range(6):
        frames[frame] = translate_dna_to_protein(dna_sequence, frame)
    return frames


def check_docker_available() -> Tuple[bool, bool]:
    """
    Check if Docker is available and accessible.
    
    Returns:
        Tuple of (is_available, needs_sudo)
    """
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Check if we can actually access Docker daemon
            test_result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if test_result.returncode == 0:
                return True, False
            else:
                # Permission denied - might need sudo
                if "permission denied" in test_result.stderr.lower() or "permission denied" in test_result.stdout.lower():
                    return True, True
                return False, False
        return False, False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, False


def run_interproscan(
    protein_sequence: str,
    sequence_id: str = "query",
    docker_image: str = "interpro/interproscan:5.76-107.0",
    output_format: str = "tsv",
    temp_dir: Optional[str] = None,
    interproscan_data_dir: Optional[str] = None,
    use_sudo: bool = False
) -> str:
    """
    Run InterProScan on a protein sequence using Docker.
    
    Args:
        protein_sequence: Protein sequence string
        sequence_id: Identifier for the sequence
        docker_image: Docker image to use
        output_format: Output format (tsv, xml, json)
        temp_dir: Temporary directory for files (uses system temp if None)
        interproscan_data_dir: Path to InterProScan data directory (optional,
                              but recommended for full functionality)
        use_sudo: Whether to use sudo for Docker commands (if permission denied)
        
    Returns:
        InterProScan output as string
        
    Note:
        For full functionality, you may need to download InterProScan data files
        and mount them. Example:
        docker run -v /path/to/interproscan/data:/opt/interproscan/data ...
        
        If you get permission denied errors, either:
        1. Add your user to the docker group: sudo usermod -aG docker $USER (then log out/in)
        2. Use use_sudo=True (may require password entry)
    """
    docker_available, needs_sudo = check_docker_available()
    if not docker_available:
        raise RuntimeError("Docker is not available. Please install Docker.")
    
    # Auto-detect if sudo is needed
    if needs_sudo and not use_sudo:
        use_sudo = True
    
    # Create temporary directory if not provided
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    else:
        os.makedirs(temp_dir, exist_ok=True)
    
    # Get absolute paths for Docker volume mounting
    temp_dir_abs = os.path.abspath(temp_dir)
    
    # Write protein sequence to FASTA file
    fasta_path = os.path.join(temp_dir_abs, f"{sequence_id}.fasta")
    with open(fasta_path, 'w') as f:
        f.write(f">{sequence_id}\n{protein_sequence}\n")
    
    # Output file
    output_path = os.path.join(temp_dir_abs, f"{sequence_id}.{output_format}")
    
    # Build Docker command
    # Based on: docker run --rm -w $PWD -v $PWD:$PWD -v $PWD/interproscan-data:/opt/interproscan/data interpro/interproscan:5.76-107.0 --input file.fasta
    cmd = []
    if use_sudo:
        cmd.append("sudo")
    cmd.extend([
        "docker", "run",
        "--rm",
        "--platform", "linux/amd64",
        "-v", f"{temp_dir_abs}:{temp_dir_abs}",
        "-w", temp_dir_abs,
    ])
    
    # Add data directory mount if provided
    if interproscan_data_dir:
        data_dir_abs = os.path.abspath(interproscan_data_dir)
        cmd.extend(["-v", f"{data_dir_abs}:/opt/interproscan/data"])
    
    # Add image and InterProScan arguments
    cmd.extend([
        docker_image,
        "--input", fasta_path,
        "--formats", output_format,
        "--outfile", output_path
    ])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or ""
            # Check for permission denied errors
            if "permission denied" in error_msg.lower() and not use_sudo:
                raise RuntimeError(
                    f"InterProScan failed: Docker permission denied.\n"
                    f"To fix this, run: sudo usermod -aG docker $USER\n"
                    f"Then log out and log back in, or restart your session.\n"
                    f"Alternatively, you can use use_sudo=True parameter.\n"
                    f"Original error: {error_msg}"
                )
            raise RuntimeError(
                f"InterProScan failed: {error_msg}"
            )
        
        # Read output file
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                return f.read()
        else:
            # If no output file, return stdout (some versions may output to stdout)
            return result.stdout
            
    finally:
        # Cleanup (optional - could keep for debugging)
        pass


def parse_interproscan_tsv(tsv_output: str) -> List[InterProHit]:
    """
    Parse InterProScan TSV output.
    
    TSV format columns:
    Protein accession | Sequence MD5 digest | Sequence length | Analysis |
    Signature accession | Signature description | Start location | Stop location |
    Score | Status | Date | InterPro accession | InterPro description | GO terms | Pathway
    
    Args:
        tsv_output: TSV output string from InterProScan
        
    Returns:
        List of InterProHit objects
    """
    hits = []
    
    for line in tsv_output.strip().split('\n'):
        if not line or line.startswith('#'):
            continue
        
        fields = line.split('\t')
        if len(fields) < 11:
            continue
        
        try:
            hit = InterProHit(
                protein_id=fields[0],
                sequence_md5=fields[1],
                length=int(fields[2]) if fields[2] else 0,
                database=fields[3],
                database_accession=fields[4],
                database_description=fields[5],
                start=int(fields[6]) if fields[6] else 0,
                end=int(fields[7]) if fields[7] else 0,
                e_value=float(fields[8]) if fields[8] and fields[8] != '-' else None,
                status=fields[9],
                date=fields[10],
                interpro_accession=fields[11] if len(fields) > 11 and fields[11] else None,
                interpro_description=fields[12] if len(fields) > 12 and fields[12] else None,
                go_terms=[g for g in (fields[13].split('|') if len(fields) > 13 and fields[13] else [])],
                pathway=fields[14] if len(fields) > 14 and fields[14] else None
            )
            hits.append(hit)
        except (ValueError, IndexError) as e:
            # Skip malformed lines
            continue
    
    return hits


def assess_risk_from_hits(hits: List[InterProHit]) -> Tuple[str, float, List[str], List[str]]:
    """
    Assess risk level from InterProScan hits.
    
    Args:
        hits: List of InterProHit objects
        
    Returns:
        Tuple of (risk_level, risk_score, virulence_factors, toxins)
    """
    virulence_factors = []
    toxins = []
    risk_score = 0.0
    
    for hit in hits:
        desc_lower = (hit.database_description or "").lower()
        interpro_desc_lower = (hit.interpro_description or "").lower()
        combined_desc = f"{desc_lower} {interpro_desc_lower}"
        
        # Check for high-risk keywords
        for keyword in HIGH_RISK_KEYWORDS:
            if keyword in combined_desc:
                if 'toxin' in keyword:
                    toxins.append(f"{hit.database_accession}: {hit.database_description}")
                else:
                    virulence_factors.append(f"{hit.database_accession}: {hit.database_description}")
                risk_score = max(risk_score, 0.8)
        
        # Check for medium-risk keywords
        for keyword in MEDIUM_RISK_KEYWORDS:
            if keyword in combined_desc and risk_score < 0.8:
                risk_score = max(risk_score, 0.5)
    
    # Determine risk level
    if risk_score >= 0.8:
        risk_level = "HIGH"
    elif risk_score >= 0.5:
        risk_level = "MEDIUM"
    elif risk_score > 0.0:
        risk_level = "LOW"
    else:
        risk_level = "NONE"
    
    return risk_level, risk_score, virulence_factors, toxins


def detect_layer2(
    dna_sequence: str,
    docker_image: str = "interpro/interproscan:5.76-107.0",
    check_all_frames: bool = True,
    min_protein_length: int = 30,
    interproscan_data_dir: Optional[str] = None,
    use_sudo: bool = False
) -> Layer2Result:
    """
    Main function for Layer 2 detection using InterProScan.
    
    Args:
        dna_sequence: DNA sequence to analyze
        docker_image: Docker image to use for InterProScan
        check_all_frames: Whether to check all 6 reading frames
        min_protein_length: Minimum protein length to analyze
        
    Returns:
        Layer2Result object with risk assessment
    """
    # Clean sequence
    dna_sequence = dna_sequence.upper().replace('\n', '').replace(' ', '')
    dna_sequence = ''.join(c for c in dna_sequence if c in 'ATCGN')
    
    if len(dna_sequence) < 90:  # Need at least 30 amino acids
        return Layer2Result(
            risk_level="NONE",
            risk_score=0.0,
            hits=[],
            virulence_factors=[],
            toxins=[],
            warnings=["DNA sequence too short for protein domain analysis"],
            details={"error": "Sequence too short"}
        )
    
    all_hits = []
    warnings = []
    details = {}
    
    # Translate and analyze
    if check_all_frames:
        frames = translate_all_frames(dna_sequence)
        details["frames_analyzed"] = len([f for f in frames.values() if len(f) >= min_protein_length])
    else:
        frames = {0: translate_dna_to_protein(dna_sequence, 0)}
    
    # Analyze each frame with sufficient length
    for frame_num, protein_seq in frames.items():
        if len(protein_seq) < min_protein_length:
            continue
        
        try:
            # Run InterProScan
            output = run_interproscan(
                protein_sequence=protein_seq,
                sequence_id=f"frame_{frame_num}",
                docker_image=docker_image,
                interproscan_data_dir=interproscan_data_dir,
                use_sudo=use_sudo
            )
            
            # Parse results
            frame_hits = parse_interproscan_tsv(output)
            all_hits.extend(frame_hits)
            
        except Exception as e:
            warnings.append(f"InterProScan failed for frame {frame_num}: {str(e)}")
            continue
    
    # Assess risk
    risk_level, risk_score, virulence_factors, toxins = assess_risk_from_hits(all_hits)
    
    details.update({
        "num_hits": len(all_hits),
        "num_frames_analyzed": details.get("frames_analyzed", 1),
        "databases_found": list(set(h.database for h in all_hits))
    })
    
    return Layer2Result(
        risk_level=risk_level,
        risk_score=risk_score,
        hits=all_hits,
        virulence_factors=virulence_factors,
        toxins=toxins,
        warnings=warnings,
        details=details
    )


def detect_layer2_from_fasta(
    fasta_path: str,
    docker_image: str = "interpro/interproscan:5.76-107.0",
    check_all_frames: bool = True,
    use_sudo: bool = False
) -> Dict[str, Layer2Result]:
    """
    Run Layer 2 detection on all sequences in a FASTA file.
    
    Args:
        fasta_path: Path to input FASTA file
        docker_image: Docker image to use
        check_all_frames: Whether to check all 6 reading frames
        
    Returns:
        Dictionary mapping sequence IDs to Layer2Result objects
    """
    from Bio import SeqIO
    
    results = {}
    
    try:
        for record in SeqIO.parse(fasta_path, "fasta"):
            sequence = str(record.seq)
            result = detect_layer2(
                sequence,
                docker_image=docker_image,
                check_all_frames=check_all_frames,
                use_sudo=use_sudo
            )
            results[record.id] = result
    except Exception as e:
        raise ValueError(f"Failed to read FASTA file {fasta_path}: {e}")
    
    return results


if __name__ == "__main__":
    # Example usage
    # Use the first 500 bases from test_sequence.txt for testing
    test_sequence_path = os.path.join(os.path.dirname(__file__), "..",  "test_sequence.txt")
    test_sequence_path = os.path.abspath(test_sequence_path)

    with open(test_sequence_path, "r") as f:
        # Join all non-empty lines, remove whitespace/newlines, and extract first 500 bp
        test_dna = "".join([line.strip() for line in f if line.strip()])
        
    print("Testing Layer 2 InterProScan detection...")
    print(f"Input DNA: {test_dna[:50]}...")
    
    result = detect_layer2(test_dna, check_all_frames=True, use_sudo=True)
    
    print(f"\nRisk Level: {result.risk_level}")
    print(f"Risk Score: {result.risk_score:.2f}")
    print(f"Number of hits: {len(result.hits)}")
    print(f"Virulence factors: {len(result.virulence_factors)}")
    print(f"Toxins: {len(result.toxins)}")
    
    if result.warnings:
        print(f"\nWarnings: {result.warnings}")

