# Layer 2: Functional Virulence Detection

Layer 2 uses InterProScan to identify protein domains, virulence factors, and toxins in translated DNA sequences.

## Overview

This module implements functional virulence detection by:
1. Translating DNA sequences to protein (all 6 reading frames)
2. Running InterProScan via Docker to identify protein domains
3. Assessing risk based on detected virulence factors and toxins

## Requirements

- Docker installed and accessible
- InterProScan Docker image (default: `interpro/interproscan:5.76-107.0`)
- Biopython for sequence translation

## Usage

### Basic Usage

```python
from detector.layer2.layer2_interproscan import detect_layer2

# Analyze a DNA sequence
result = detect_layer2(
    dna_sequence="ATGGCCGAGATCGAC...",
    docker_image="interpro/interproscan:5.76-107.0",
    check_all_frames=True
)

print(f"Risk Level: {result.risk_level}")
print(f"Risk Score: {result.risk_score}")
print(f"Virulence Factors: {result.virulence_factors}")
print(f"Toxins: {result.toxins}")
```

### With InterProScan Data Directory

For full functionality, you may need to download and mount InterProScan data files:

```python
result = detect_layer2(
    dna_sequence="ATGGCCGAGATCGAC...",
    interproscan_data_dir="/path/to/interproscan/data"
)
```

### From FASTA File

```python
from detector.layer2.layer2_interproscan import detect_layer2_from_fasta

results = detect_layer2_from_fasta(
    fasta_path="sequences.fasta",
    docker_image="interpro/interproscan:5.76-107.0"
)

for seq_id, result in results.items():
    print(f"{seq_id}: {result.risk_level}")
```

## Risk Assessment

- **HIGH**: Known toxin or high-risk virulence factor domains detected
- **MEDIUM**: Moderate-risk domains or immune modulators detected  
- **LOW**: Low-risk domains or generic protein domains detected
- **NONE**: No significant domains detected

## Docker Image Setup

The wrapper uses Docker to run InterProScan. Make sure you have the image:

```bash
docker pull interpro/interproscan:5.76-107.0
```

For ARM64 systems (like AWS Graviton), you'll need QEMU emulation:

```bash
docker run --privileged --rm tonistiigi/binfmt --install all
```

Then always use `--platform linux/amd64` when running (the wrapper handles this automatically).

## Notes

- InterProScan can be slow for long sequences
- The wrapper checks all 6 reading frames by default
- Minimum protein length is 30 amino acids (90 bp DNA)
- Some InterProScan features require data files to be mounted

