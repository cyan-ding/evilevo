# EvilEvo Detector REST API

FastAPI-based REST API for analyzing DNA sequences using the three-layer detection system.

## Installation

Install dependencies:
```bash
pip install fastapi uvicorn[standard]
```

Or if using the project's dependency management:
```bash
# Install from pyproject.toml (includes FastAPI and uvicorn)
```

## Running the API

### Option 1: Direct Python execution
```bash
cd /home/ubuntu/cyan/evilevo/src/detector
python api.py
```

### Option 2: Using uvicorn directly
```bash
cd /home/ubuntu/cyan/evilevo/src/detector
uvicorn api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET `/`
Root endpoint with API information.

### GET `/health`
Health check endpoint.

### POST `/analyze`
Analyze a DNA sequence using all three detection layers.

**Request Body:**
```json
{
  "sequence": "ATGGCCGAGATCGAC...",
  "layer1_database_path": null,  // Optional, defaults to configured DBC
  "layer2_docker_image": "interpro/interproscan:5.76-107.0",  // Optional
  "layer2_check_all_frames": true  // Optional
}
```

**Response:**
```json
{
  "layer1": {
    "gc_content": 45.2,
    "query_length": 1000,
    "num_hits": 5,
    "top_hit": {
      "subject_id": "...",
      "subject_title": "...",
      "identity": 87.5,
      "alignment_length": 850,
      "query_start": 10,
      "query_end": 860,
      "subject_start": 100,
      "subject_end": 950,
      "e_value": 1e-50,
      "bit_score": 1200.5,
      "query_coverage": 85.0
    },
    "all_hits": [...],
    "warnings": []
  },
  "layer2": {
    "num_hits": 3,
    "hits": [...],
    "virulence_factors": [...],
    "toxins": [...],
    "warnings": [],
    "details": {}
  },
  "layer3": {
    "cai_frame_0": 0.75,
    "cai_frame_1": 0.68,
    "cai_frame_2": 0.72,
    "max_cai": 0.75,
    "warnings": []
  }
}
```

## Example Usage

### Using curl
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "ATGGCCGAGATCGACATCGACATCGAC"
  }'
```

### Using Python requests
```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "sequence": "ATGGCCGAGATCGACATCGACATCGAC"
    }
)

result = response.json()
print(f"GC Content: {result['layer1']['gc_content']}")
print(f"CAI (Frame 0): {result['layer3']['cai_frame_0']}")
```

### Using the interactive API docs
Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Layer Descriptions

### Layer 1: BLAST Similarity
- Compares sequence against Database of Concern (DBC)
- Returns GC content, BLAST hits, and alignment metrics
- No risk scores, only raw metrics

### Layer 2: InterProScan Protein Domains
- Translates DNA to protein (all 6 reading frames)
- Identifies protein domains, virulence factors, and toxins
- Returns domain hits, virulence factors, and toxins detected

### Layer 3: Codon Adaptation Index (CAI)
- Calculates CAI for each reading frame
- Measures codon usage optimization for human cells
- Returns CAI values for frames 0, 1, 2, and maximum CAI

## Notes

- All sequences are automatically cleaned (uppercase, whitespace removed)
- Only valid DNA characters (A, T, C, G, N) are accepted
- Layer 2 requires Docker and InterProScan image
- Layer 1 requires BLAST+ and the DBC database

