"""
REST API for EvilEvo Detector

This FastAPI application provides endpoints to analyze DNA sequences
using the detection system:
- Layer 1: BLAST similarity to known pathogens
- Layer 3: Codon Adaptation Index (CAI) calculation
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from layer1.layer1_blast import detect_layer1, BlastHit, DBC_FILE
from layer3.cai_calculator import calculate_cai, calculate_cai_for_orf

app = FastAPI(
    title="EvilEvo Detector API",
    description="API for analyzing DNA sequences using multi-layer detection",
    version="0.1.0"
)


class SequenceRequest(BaseModel):
    """Request model for sequence analysis."""
    sequence: str = Field(..., description="DNA sequence to analyze", min_length=1)
    layer1_database_path: Optional[str] = Field(
        None, 
        description="Path to BLAST database (defaults to configured DBC)"
    )


class BlastHitResponse(BaseModel):
    """Response model for BLAST hit."""
    subject_id: str
    subject_title: str
    identity: float
    alignment_length: int
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    e_value: float
    bit_score: float
    query_coverage: float


class Layer1Metrics(BaseModel):
    """Raw metrics from Layer 1 detection."""
    gc_content: float
    query_length: int
    num_hits: int
    top_hit: Optional[BlastHitResponse] = None
    all_hits: List[BlastHitResponse] = []
    warnings: List[str] = []


class Layer3Metrics(BaseModel):
    """Raw metrics from Layer 3 detection."""
    cai_frame_0: Optional[float] = None
    cai_frame_1: Optional[float] = None
    cai_frame_2: Optional[float] = None
    max_cai: Optional[float] = None
    warnings: List[str] = []


class AnalysisResponse(BaseModel):
    """Complete analysis response with all layer metrics."""
    layer1: Layer1Metrics
    layer3: Layer3Metrics


def blast_hit_to_response(hit: BlastHit) -> BlastHitResponse:
    """Convert BlastHit to response model."""
    return BlastHitResponse(
        subject_id=hit.subject_id,
        subject_title=hit.subject_title,
        identity=hit.identity,
        alignment_length=hit.alignment_length,
        query_start=hit.query_start,
        query_end=hit.query_end,
        subject_start=hit.subject_start,
        subject_end=hit.subject_end,
        e_value=hit.e_value,
        bit_score=hit.bit_score,
        query_coverage=hit.query_coverage
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "EvilEvo Detector API",
        "version": "0.1.0",
        "endpoints": {
            "/analyze": "POST - Analyze a DNA sequence",
            "/health": "GET - Health check"
        },
        "layers": {
            "layer1": "BLAST similarity to known pathogens",
            "layer3": "Codon Adaptation Index (CAI) calculation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_sequence(request: SequenceRequest):
    """
    Analyze a DNA sequence using detection layers.
    
    Returns raw metrics from each layer without risk scores.
    """
    sequence = request.sequence.strip().upper()
    
    if not sequence:
        raise HTTPException(status_code=400, detail="Sequence cannot be empty")
    
    # Validate sequence contains only valid DNA characters
    valid_chars = set('ATCGN')
    if not all(c in valid_chars for c in sequence.replace('\n', '').replace(' ', '')):
        raise HTTPException(
            status_code=400, 
            detail="Sequence contains invalid characters. Only A, T, C, G, and N are allowed."
        )
    
    # Clean sequence
    sequence = sequence.replace('\n', '').replace(' ', '')
    
    results = {}
    
    # Layer 1: BLAST detection
    try:
        db_path = request.layer1_database_path or DBC_FILE
        layer1_result = detect_layer1(
            query_sequence=sequence,
            database_path=db_path,
            check_gc=True
        )
        
        layer1_metrics = Layer1Metrics(
            gc_content=layer1_result.gc_content,
            query_length=layer1_result.query_length,
            num_hits=len(layer1_result.all_hits),
            top_hit=blast_hit_to_response(layer1_result.top_hit) if layer1_result.top_hit else None,
            all_hits=[blast_hit_to_response(hit) for hit in layer1_result.all_hits],
            warnings=layer1_result.warnings
        )
        results['layer1'] = layer1_metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Layer 1 analysis failed: {str(e)}"
        )
    
    # Layer 3: CAI calculation
    try:
        layer3_warnings = []
        cai_frame_0 = None
        cai_frame_1 = None
        cai_frame_2 = None
        
        # Calculate CAI for each reading frame
        for frame in [0, 1, 2]:
            try:
                cai = calculate_cai_for_orf(sequence, frame)
                if frame == 0:
                    cai_frame_0 = cai
                elif frame == 1:
                    cai_frame_1 = cai
                elif frame == 2:
                    cai_frame_2 = cai
            except ValueError as e:
                # Sequence too short or invalid - not an error, just skip
                layer3_warnings.append(f"Frame {frame}: {str(e)}")
            except Exception as e:
                layer3_warnings.append(f"Frame {frame} CAI calculation failed: {str(e)}")
        
        max_cai = max([c for c in [cai_frame_0, cai_frame_1, cai_frame_2] if c is not None], default=None)
        
        layer3_metrics = Layer3Metrics(
            cai_frame_0=cai_frame_0,
            cai_frame_1=cai_frame_1,
            cai_frame_2=cai_frame_2,
            max_cai=max_cai,
            warnings=layer3_warnings
        )
        results['layer3'] = layer3_metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Layer 3 analysis failed: {str(e)}"
        )
    
    return AnalysisResponse(**results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

