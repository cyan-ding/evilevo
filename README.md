# EvilEvo

EvilEvo is an end-to-end platform designed for synthesis companies to detect potentially malicious viral genomes. The project fine-tuned Evo 2 1B on eukaryotic viruses, demonstrating both the generation of eukaryotic viruses and comprehensive detection methods for identifying them.

## Overview

This platform implements a multi-layer detection system that analyzes DNA sequences for characteristics indicative of malicious intent, particularly focusing on sequences optimized for eukaryotic (human) cell expression. The system combines traditional bioinformatics approaches with modern machine learning capabilities.

### Key Achievements

- **Fine-tuned Evo 2 1B** on eukaryotic viruses, enabling the model to understand and generate viral sequences optimized for eukaryotic hosts
- **Demonstrated generation** of eukaryotic viruses using the fine-tuned model
- **Developed detection methods** to identify potentially malicious viral genomes through multiple analytical layers

# Running

The main webapp that unifies this project is located in `/webapp`. This is a simple Vite app that can be run with `npm run dev` after installing the dependencies with `npm i`. Require `node >= 20`.

Then, run the `nvcr.io/nvidia/clara/bionemo-framework:2.7` docker container with the `evo2/` directory mounted. Inside `evo2/webapi/app.py` is a Flask app. Run this file with Python inside the docker container. Port `5000` must be exposed.

Then, follow directions below to run the detection web server.

## Detection Layers

### Layer 1: Direct Threat Similarity Detection

Layer 1 uses BLAST+ to search query sequences against a curated "Database of Concern" (DBC) containing known viral Select Agents and Public Health Emergency of International Concern (PHEIC) pathogens.

#### Capabilities

- **Whole-Genome Homology Detection**: Identifies high sequence identity (>85% over >1000 bp) to known pathogens
- **Oligonucleotide/Fragment Analysis**: Detects high identity matches to short, highly conserved pathogenic regions (e.g., viral packaging signals, replication initiation sites)
- **GC Content Analysis**: Flags sequences with GC content optimized for mammalian cells (~40-50%), which may indicate intentional optimization for human cells
- **Unknown Viral Sequence Detection**: Identifies sequences with viral characteristics even when not matching known pathogens in the database

#### Risk Scoring

- **HIGH Risk**: >85% identity over >1000 bp to Select Agent
- **MEDIUM Risk**: >85% identity over 100-1000 bp to Select Agent
- **LOW Risk**: >85% identity over <100 bp or lower identity matches
- **NONE**: No significant matches

#### Database of Concern (DBC)

The DBC includes viral Select Agents such as:
- Filoviruses (Ebola, Marburg)
- Poxviruses (Variola, Monkeypox, Capripoxviruses)
- Paramyxoviruses (Nipah, Hendra, Rinderpest)
- Coronaviruses (SARS-CoV)
- Alphaviruses (EEEV, VEEV)
- Flaviviruses (TBEV, KFDV)
- Arenaviruses (Lassa, Lujo, South American HF viruses)
- Bunyaviruses (CCHFV, RVFV)
- Influenza viruses (1918 H1N1, Avian influenza)
- Picornaviruses (FMDV, SVDV)
- And other high-risk pathogens

### Layer 3: Host Adaptability Analysis

Layer 3 evaluates sequences for optimization toward eukaryotic (human) cell expression, which is a strong indicator of malicious intent.

#### Capabilities

- **Codon Adaptation Index (CAI) Calculation**: Implements the Sharp & Li (1987) algorithm to measure codon optimization
  - Calculates CAI for multiple reading frames (0, 1, 2)
  - Uses human optimal codon usage table derived from highly expressed genes
  - CAI values close to 1.0 indicate high optimization for human cells
- **Multi-Frame Analysis**: Evaluates all three forward reading frames to detect optimization regardless of sequence orientation
- **ORF Detection**: Identifies and analyzes open reading frames within the sequence

#### CAI Algorithm

The CAI is calculated as the geometric mean of relative adaptiveness (w) values:
- `w = frequency(codon) / max_frequency(synonymous_codons)`
- `CAI = (w1 × w2 × ... × wn)^(1/n)`

High CAI values (>0.7) suggest intentional codon optimization for human expression, which is unusual for naturally occurring viruses and may indicate synthetic design.

## Evo2

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or using uv
uv sync
```

### Requirements

- Python 3.8+
- BLAST+ (command-line tool)
- Biopython
- ncbi-genome-download

## Usage

### Setting Up the Database of Concern

```bash
# Download Select Agent genomes and create BLAST database
python -m layer1.download_dbc --output-dir dbc --section refseq
```

### Running Detection

```python
from layer1.layer1_blast import detect_layer1
from layer3.cai_calculator import calculate_cai_for_orf

# Analyze a sequence
sequence = "ATGCGATCGATCG..."

# Layer 1: BLAST detection
layer1_result = detect_layer1(
    query_sequence=sequence,
    database_path="dbc/dbc",
    check_gc=True
)

print(f"Risk Level: {layer1_result.risk_level}")
print(f"Risk Score: {layer1_result.risk_score}")
print(f"GC Content: {layer1_result.gc_content}%")

# Layer 3: CAI calculation
cai_frame_0 = calculate_cai_for_orf(sequence, frame=0)
cai_frame_1 = calculate_cai_for_orf(sequence, frame=1)
cai_frame_2 = calculate_cai_for_orf(sequence, frame=2)

max_cai = max(cai_frame_0, cai_frame_1, cai_frame_2)
print(f"Maximum CAI: {max_cai:.4f}")
```

### API Usage

The platform includes a FastAPI REST API for programmatic access:

```bash
# Start the API server
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={"sequence": "ATGCGATCGATCG..."}
)

results = response.json()
print(results)
```

## Project Structure

```
evilevo/
├── src/
│   ├── layer1/              # Layer 1: BLAST-based detection
│   │   ├── layer1_blast.py  # Main detection logic
│   │   └── download_dbc.py  # DBC creation utilities
│   ├── layer3/              # Layer 3: CAI calculation
│   │   └── cai_calculator.py
│   └── api.py               # FastAPI REST API
├── evo2/                    # Evo 2 1B fine-tuning code
└── docs/                    # Documentation
```

## References

- Sharp, P. M., & Li, W. H. (1987). The Codon Adaptation Index - a measure of directional synonymous codon usage bias, and its potential applications. *Nucleic Acids Research*, 15(3), 1281-1295.

## License

[MIT]

## Contributing

[Add contribution guidelines here]

