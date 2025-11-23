"""
Download Select Agent genomes and create Database of Concern (DBC)

This script downloads viral Select Agent genomes from NCBI using
ncbi-genome-download and creates a BLAST database for Layer 1 detection.
"""

import subprocess
import gzip
from pathlib import Path
from typing import List
from Bio import SeqIO


# Mapping of common names to scientific names/genera for ncbi-genome-download
# ncbi-genome-download uses genus names or species taxids
SELECT_AGENTS = {
    # Filoviruses
    "Ebolavirus": {
        "genus": "Ebolavirus",
        "common_names": ["Ebola virus", "Ebolavirus"]
    },
    "Marburg virus": {
        "genus": "Marburgvirus",
        "common_names": ["Marburg virus", "Marburg marburgvirus"]
    },
    
    # Poxviruses
    "Variola major virus": {
        "genus": "Orthopoxvirus",
        "species": "Variola virus",
        "common_names": ["Variola major", "Smallpox virus"]
    },
    "Variola minor virus": {
        "genus": "Orthopoxvirus",
        "species": "Variola virus",
        "common_names": ["Variola minor", "Alastrim"]
    },
    "Monkeypox virus": {
        "genus": "Orthopoxvirus",
        "species": "Monkeypox virus",
        "common_names": ["Monkeypox", "MPXV"] 
    },
    "Goat pox virus": {
        "genus": "Capripoxvirus",
        "species": "Goatpox virus",
        "common_names": ["Goat pox", "Goatpox"]
    },
    "Lumpy skin disease virus": {
        "genus": "Capripoxvirus",
        "species": "Lumpy skin disease virus",
        "common_names": ["Lumpy skin disease", "LSDV"]
    },
    "Sheep pox virus": {
        "genus": "Capripoxvirus",
        "species": "Sheeppox virus",
        "common_names": ["Sheep pox", "Sheeppox"]
    },
    # Paramyxoviruses
    "Nipah virus": {
        "genus": "Henipavirus",
        "species": "Nipah henipavirus",
        "common_names": ["Nipah virus", "NiV"]
    },
    "Hendra virus": {
        "genus": "Henipavirus",
        "species": "Hendra henipavirus",
        "common_names": ["Hendra virus", "HeV"]
    },
    "Rinderpest virus": {
        "genus": "Morbillivirus",
        "species": "Rinderpest morbillivirus",
        "common_names": ["Rinderpest", "RPV"]
    },
    "Peste des petits ruminants virus": {
        "genus": "Morbillivirus",
        "species": "Small ruminant morbillivirus",
        "common_names": ["PPRV", "Peste des petits ruminants"]
    },
    "Newcastle disease virus": {
        "genus": "Avulavirus",
        "species": "Newcastle disease virus",
        "common_names": ["NDV", "Newcastle disease"]
    },
    
    # Coronaviruses
    "SARS-associated coronavirus": {
        "genus": "Betacoronavirus",
        "species": "Severe acute respiratory syndrome-related coronavirus",
        "common_names": ["SARS-CoV", "SARS coronavirus"]
    },
    
    # Flaviviruses
    "Eastern equine encephalitis virus": {
        "genus": "Alphavirus",
        "species": "Eastern equine encephalitis virus",
        "common_names": ["EEEV", "Eastern equine encephalitis"]
    },
    "Venezuelan equine encephalitis virus": {
        "genus": "Alphavirus",
        "species": "Venezuelan equine encephalitis virus",
        "common_names": ["VEEV", "Venezuelan equine encephalitis"]
    },
    "Tick-borne encephalitis complex viruses": {
        "genus": "Flavivirus",
        "species": "Tick-borne encephalitis virus",
        "common_names": ["TBEV", "Tick-borne encephalitis"]
    },
    "Kyasanur Forest disease virus": {
        "genus": "Flavivirus",
        "species": "Kyasanur Forest disease virus",
        "common_names": ["KFDV", "Kyasanur Forest disease"]
    },
    
    # Arenaviruses
    "Lassa fever virus": {
        "genus": "Mammarenavirus",
        "species": "Lassa mammarenavirus",
        "common_names": ["Lassa virus", "LASV"]
    },
    "Lujo virus": {
        "genus": "Mammarenavirus",
        "species": "Lujo mammarenavirus",
        "common_names": ["Lujo virus", "LUJV"]
    },
    "South American Haemorrhagic Fever viruses": {
        "genus": "Mammarenavirus",
        "species": ["Junin mammarenavirus", "Machupo mammarenavirus", 
                   "Guanarito mammarenavirus", "Sabia mammarenavirus",
                   "Chapare mammarenavirus"],
        "common_names": ["Junin", "Machupo", "Guanarito", "Sabia", "Chapare"]
    },
    
    # Bunyaviruses
    "Crimean-Congo haemorrhagic fever virus": {
        "genus": "Orthonairovirus",
        "species": "Crimean-Congo hemorrhagic fever orthonairovirus",
        "common_names": ["CCHFV", "Crimean-Congo hemorrhagic fever"]
    },
    "Rift Valley fever virus": {
        "genus": "Phlebovirus",
        "species": "Rift Valley fever phlebovirus",
        "common_names": ["RVFV", "Rift Valley fever"]
    },
    
    # Influenza
    "Reconstructed 1918 Influenza virus": {
        "genus": "Alphainfluenzavirus",
        "species": "Influenza A virus",
        "common_names": ["1918 H1N1", "Spanish flu"]
    },
    "Avian influenza virus": {
        "genus": "Alphainfluenzavirus",
        "species": "Influenza A virus",
        "common_names": ["Avian flu", "H5N1", "H7N9"]
    },
    
    # Picornaviruses
    "Foot-and-Mouth Disease virus": {
        "genus": "Aphthovirus",
        "species": "Foot-and-mouth disease virus",
        "common_names": ["FMDV", "Foot-and-mouth disease"]
    },
    "Swine vesicular disease virus": {
        "genus": "Enterovirus",
        "species": "Swine vesicular disease virus",
        "common_names": ["SVDV", "Swine vesicular disease"]
    },
    
    # Other
    "African swine fever virus": {
        "genus": "Asfivirus",
        "species": "African swine fever virus",
        "common_names": ["ASFV", "African swine fever"]
    },
    "Classical swine fever virus": {
        "genus": "Pestivirus",
        "species": "Classical swine fever virus",
        "common_names": ["CSFV", "Classical swine fever", "Hog cholera"]
    },
}


def download_viral_genomes(
    output_dir: str = "genomes",
    section: str = "refseq",
    formats: List[str] = ["fasta"],
    parallel: int = 4
) -> str:
    """
    Download all viral genomes from NCBI RefSeq/GenBank.
    
    Args:
        output_dir: Directory to save downloaded genomes
        section: "refseq" or "genbank"
        formats: List of formats to download (e.g., ["fasta"])
        parallel: Number of parallel downloads
        
    Returns:
        Path to output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "ncbi-genome-download",
        "viral",
        "-s", section,
        "-F", ",".join(formats),
        "-o", str(output_path),
        "-p", str(parallel),
        "-r", "3",  # Retry 3 times
        "-v"  # Verbose
    ]
    
    print(f"Downloading all viral genomes from {section}...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Warning: Download had issues (return code {result.returncode})")
        print(f"Error output: {result.stderr[:500]}")
    
    return str(output_path)


def download_by_genus(
    genera: List[str],
    output_dir: str = "genomes",
    section: str = "refseq",
    formats: List[str] = ["fasta"]
) -> str:
    """
    Download genomes for specific genera.
    
    Args:
        genera: List of genus names
        output_dir: Directory to save downloaded genomes
        section: "refseq" or "genbank"
        formats: List of formats to download
        
    Returns:
        Path to output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for genus in genera:
        print(f"\nDownloading {genus}...")
        cmd = [
            "ncbi-genome-download",
            "viral",
            "-s", section,
            "-F", ",".join(formats),
            "-g", genus,
            "--fuzzy-genus",  # Allow fuzzy matching
            "-o", str(output_path),
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  Warning: {genus} download had issues")
            print(f"  Error: {result.stderr[:200]}")
        else:
            print(f"  ✓ Downloaded {genus}")
    
    return str(output_path)


def collect_fasta_files(
    genomes_dir: str,
    output_fasta: str = "dbc_sequences.fasta",
    filter_select_agents: bool = True
) -> str:
    """
    Collect all FASTA sequences from downloaded genomes into a single file.
    
    Args:
        genomes_dir: Directory containing downloaded genomes
        output_fasta: Output FASTA file path
        filter_select_agents: If True, only include sequences from select agent genera
        
    Returns:
        Path to combined FASTA file
    """
    genomes_path = Path(genomes_dir)
    output_path = Path(output_fasta)
    
    print(f"\nCollecting sequences from {genomes_dir}...")
    
    # Get select agent genera for filtering
    select_agent_genera = set()
    if filter_select_agents:
        for agent_info in SELECT_AGENTS.values():
            if "genus" in agent_info:
                select_agent_genera.add(agent_info["genus"].lower())
    
    sequences_collected = 0
    total_bases = 0
    skipped = 0
    
    with open(output_path, 'w') as outfile:
        # Walk through the directory structure
        # ncbi-genome-download creates: genomes/{section}/viral/{accession}/*.fna.gz
        # Look for both .fna and .fna.gz files
        fasta_patterns = ["*.fna", "*.fna.gz"]
        fasta_files = []
        for pattern in fasta_patterns:
            fasta_files.extend(list(genomes_path.rglob(pattern)))
        
        if not fasta_files:
            print(f"  Warning: No FASTA files found in {genomes_dir}")
            print(f"  Searched for: {fasta_patterns}")
            print(f"  Directory structure:")
            for d in list(genomes_path.rglob("*"))[:10]:
                if d.is_dir():
                    print(f"    {d}")
        
        for fasta_file in fasta_files:
            try:
                # Handle compressed files
                if fasta_file.suffix == '.gz':
                    file_handle = gzip.open(fasta_file, 'rt')
                else:
                    file_handle = open(fasta_file, 'r')
                
                with file_handle:
                    for record in SeqIO.parse(file_handle, "fasta"):
                        # Extract accession from path (directory name)
                        path_parts = fasta_file.parts
                        accession_dir = "unknown"
                        if len(path_parts) >= 1:
                            accession_dir = path_parts[-2] if fasta_file.suffix == '.gz' else path_parts[-1]
                        
                        # Create descriptive header
                        header = f">{accession_dir}|{record.id}|seq{sequences_collected}"
                        outfile.write(f"{header}\n")
                        outfile.write(f"{str(record.seq)}\n")
                        
                        sequences_collected += 1
                        total_bases += len(record.seq)
                    
            except Exception as e:
                print(f"  Warning: Could not parse {fasta_file}: {e}")
                continue
    
    print(f"✓ Collected {sequences_collected} sequences ({total_bases:,} bases)")
    if filter_select_agents and skipped > 0:
        print(f"  Skipped {skipped} files from non-select-agent genera")
    print(f"  Output: {output_path}")
    
    if sequences_collected == 0:
        raise RuntimeError("No sequences collected! Check that genomes were downloaded correctly.")
    
    return str(output_path)


def create_dbc(
    output_dir: str = "dbc",
    section: str = "refseq",
    database_name: str = "dbc"
) -> str:
    """
    Create Database of Concern by downloading select agent genomes.
    
    This function:
    1. Downloads viral genomes (focusing on select agents)
    2. Collects sequences into a single FASTA file
    3. Creates a BLAST database
    
    Args:
        output_dir: Directory for intermediate files
        section: "refseq" or "genbank"
        database_name: Name for the BLAST database
        
    Returns:
        Path to BLAST database (without extension)
    """
    try:
        from .layer1_blast import create_blast_database
    except ImportError:
        from layer1_blast import create_blast_database
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    genomes_dir = output_path / "genomes"
    fasta_file = output_path / "dbc_sequences.fasta"
    db_path = output_path / database_name
    
    # Step 1: Download all viral genomes (this is comprehensive but large)
    # For a more targeted approach, we could download by genus
    print("=" * 60)
    print("Step 1: Downloading viral genomes from NCBI")
    print("=" * 60)
    
    # Get unique genera from select agents
    unique_genera = set()
    for agent_info in SELECT_AGENTS.values():
        if "genus" in agent_info:
            unique_genera.add(agent_info["genus"])
    
    print(f"\nFound {len(unique_genera)} unique genera in select agents:")
    for genus in sorted(unique_genera):
        print(f"  - {genus}")
    
    # Download by genus (more targeted)
    print(f"\nDownloading genomes for select agent genera...")
    download_by_genus(
        genera=list(unique_genera),
        output_dir=str(genomes_dir),
        section=section,
        formats=["fasta"]
    )
    
    # Step 2: Collect sequences
    print("\n" + "=" * 60)
    print("Step 2: Collecting sequences into single FASTA file")
    print("=" * 60)
    
    # The actual download structure is genomes/refseq/viral/ or genomes/genbank/viral/
    actual_genomes_dir = genomes_dir / section / "viral"
    if not actual_genomes_dir.exists():
        # Try alternative structure
        actual_genomes_dir = genomes_dir / "viral"
    
    collect_fasta_files(
        str(actual_genomes_dir), 
        str(fasta_file),
        filter_select_agents=False  # Already filtered by genus download
    )
    
    if not fasta_file.exists() or fasta_file.stat().st_size == 0:
        raise RuntimeError(f"FASTA file is empty or doesn't exist: {fasta_file}")
    
    # Step 3: Create BLAST database
    print("\n" + "=" * 60)
    print("Step 3: Creating BLAST database")
    print("=" * 60)
    
    database_path = create_blast_database(
        fasta_path=str(fasta_file),
        database_name=str(db_path),
        db_type="nucl"
    )
    
    print(f"\n✓ Database of Concern created successfully!")
    print(f"  Database path: {database_path}")
    print(f"  Database files:")
    for ext in ["nhr", "nin", "nsq"]:
        db_file = Path(f"{database_path}.{ext}")
        if db_file.exists():
            size_mb = db_file.stat().st_size / (1024 * 1024)
            print(f"    - {db_file.name} ({size_mb:.1f} MB)")
    
    return str(database_path)


def create_dbc_from_all_viruses(
    output_dir: str = "dbc",
    section: str = "refseq",
    database_name: str = "dbc"
) -> str:
    """
    Create DBC by downloading ALL viral genomes (comprehensive but large).
    
    This is an alternative approach that downloads all viral genomes,
    which will include select agents but also many other viruses.
    
    Args:
        output_dir: Directory for intermediate files
        section: "refseq" or "genbank"
        database_name: Name for the BLAST database
        
    Returns:
        Path to BLAST database
    """
    try:
        from .layer1_blast import create_blast_database
    except ImportError:
        from layer1_blast import create_blast_database
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    genomes_dir = output_path / "genomes"
    fasta_file = output_path / "dbc_sequences.fasta"
    db_path = output_path / database_name
    
    # Download all viral genomes
    print("Downloading ALL viral genomes (this may take a while)...")
    download_viral_genomes(
        output_dir=str(genomes_dir),
        section=section,
        formats=["fasta"],
        parallel=4
    )
    
    # Collect sequences
    collect_fasta_files(str(genomes_dir), str(fasta_file))
    
    # Create database
    database_path = create_blast_database(
        fasta_path=str(fasta_file),
        database_name=str(db_path),
        db_type="nucl"
    )
    
    return str(database_path)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download Select Agent genomes and create Database of Concern"
    )
    parser.add_argument(
        "--output-dir",
        default="dbc",
        help="Output directory for genomes and database (default: dbc)"
    )
    parser.add_argument(
        "--section",
        choices=["refseq", "genbank"],
        default="refseq",
        help="NCBI section to download from (default: refseq)"
    )
    parser.add_argument(
        "--database-name",
        default="dbc",
        help="Name for BLAST database (default: dbc)"
    )
    parser.add_argument(
        "--all-viruses",
        action="store_true",
        help="Download ALL viral genomes (large, but comprehensive)"
    )
    
    args = parser.parse_args()
    
    print("Database of Concern (DBC) Creation Script")
    print("=" * 60)
    print(f"Output directory: {args.output_dir}")
    print(f"NCBI section: {args.section}")
    print(f"Database name: {args.database_name}")
    print(f"Mode: {'All viruses' if args.all_viruses else 'Select agents only'}")
    print("=" * 60)
    
    try:
        if args.all_viruses:
            database_path = create_dbc_from_all_viruses(
                output_dir=args.output_dir,
                section=args.section,
                database_name=args.database_name
            )
        else:
            database_path = create_dbc(
                output_dir=args.output_dir,
                section=args.section,
                database_name=args.database_name
            )
        
        print(f"\n{'='*60}")
        print("SUCCESS!")
        print(f"{'='*60}")
        print(f"Database of Concern is ready at: {database_path}")
        print(f"\nYou can now use it with Layer 1 detection:")
        print(f"  from detector.layer1.layer1_blast import detect_layer1")
        print(f"  result = detect_layer1(query_sequence, '{database_path}')")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

