"""
Layer 2: Virus Host Type Detection using viruses_classifier

This module uses the viruses_classifier to determine if a viral sequence
infects eukaryotes or is a phage. This can help identify potential threats
by distinguishing between viruses that target eukaryotic cells (like humans)
versus bacteriophages.

Note: The pre-trained models are Python 2 format and may not load with Python 3.10+.
Feature extraction works perfectly and can be used for custom analysis.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
from pathlib import Path

# Import from local copy in libs/ directory
try:
    from libs.viruses_classifier.classifier import seq_to_features, classify
    from libs.viruses_classifier import constants
    from libs.viruses_classifier.loader import load_joblib_safe
    VIRUSES_CLASSIFIER_AVAILABLE = True
except ImportError:
    # Fallback to venv version if local copy not available
    try:
        from viruses_classifier.classifier import seq_to_features, classify
        from viruses_classifier import constants
        from viruses_classifier.loader import load_joblib_safe
        VIRUSES_CLASSIFIER_AVAILABLE = True
    except ImportError:
        VIRUSES_CLASSIFIER_AVAILABLE = False


@dataclass
class VirusHostResult:
    """Results from virus host type detection."""
    host_type: Optional[str] = None  # "Eucaryota-infecting" or "phage"
    probabilities: Optional[Dict[str, float]] = None
    features_extracted: bool = False
    feature_count: int = 0
    classifier_used: Optional[str] = None
    warnings: List[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def detect_virus_host_type(
    sequence: str,
    nucleic_acid: str = "DNA",
    classifier_type: str = "svc",
    use_models: bool = True
) -> VirusHostResult:
    """
    Detect if a viral sequence infects eukaryotes or is a phage.
    
    Args:
        sequence: DNA or RNA sequence
        nucleic_acid: "DNA" or "RNA" (default: "DNA")
        classifier_type: "svc", "knn", "qda", or "lr" (default: "svc")
        use_models: If True, try to load and use pre-trained models.
                   If False, only extract features.
    
    Returns:
        VirusHostResult with classification results
    """
    if not VIRUSES_CLASSIFIER_AVAILABLE:
        return VirusHostResult(
            error="viruses_classifier package not available",
            warnings=["Install with: uv pip install --no-deps git+https://github.com/wojciech-galan/viruses_classifier.git"]
        )
    
    warnings = []
    result = VirusHostResult()
    
    # Normalize inputs
    nucleic_acid = nucleic_acid.lower()
    classifier_type = classifier_type.lower()
    
    # Validate inputs
    if nucleic_acid not in ["dna", "rna"]:
        return VirusHostResult(
            error=f"Invalid nucleic_acid: {nucleic_acid}. Must be 'DNA' or 'RNA'",
            warnings=warnings
        )
    
    if classifier_type not in ["svc", "knn", "qda", "lr"]:
        return VirusHostResult(
            error=f"Invalid classifier_type: {classifier_type}",
            warnings=warnings
        )
    
    # Extract features (this always works!)
    try:
        seq_features = seq_to_features(sequence, nucleic_acid)
        result.features_extracted = True
        result.feature_count = len(seq_features)
    except Exception as e:
        return VirusHostResult(
            error=f"Feature extraction failed: {str(e)}",
            warnings=warnings
        )
    
    # Try to use models if requested
    if use_models:
        try:
            # Load models
            scaler = load_joblib_safe(constants.scaler_path)
            classifier = load_joblib_safe(constants.classifier_paths[classifier_type])
            feature_indices = constants.feature_indices[classifier_type]
            
            # Classify
            host_type = classify(
                seq_features,
                scaler,
                classifier,
                feature_indices,
                probas=False
            )
            probabilities = classify(
                seq_features,
                scaler,
                classifier,
                feature_indices,
                probas=True
            )
            
            result.host_type = host_type
            result.probabilities = probabilities
            result.classifier_used = classifier_type.upper()
            
        except Exception as e:
            warnings.append(
                f"Model loading failed (Python 2 pickle format): {str(e)}. "
                f"Feature extraction succeeded ({result.feature_count} features)."
            )
            result.warnings = warnings
            # Return partial result with features
            return result
    
    # If we only extracted features, return that
    if not use_models:
        warnings.append("Models not used - only features extracted")
    
    result.warnings = warnings
    return result


def get_virus_host_features(sequence: str, nucleic_acid: str = "DNA") -> Dict:
    """
    Extract features from a viral sequence without classification.
    
    This function always works, even if models can't be loaded.
    
    Args:
        sequence: DNA or RNA sequence
        nucleic_acid: "DNA" or "RNA"
    
    Returns:
        Dictionary with extracted features and metadata
    """
    if not VIRUSES_CLASSIFIER_AVAILABLE:
        return {
            "error": "viruses_classifier not available",
            "features": None
        }
    
    try:
        features = seq_to_features(sequence, nucleic_acid.lower())
        return {
            "features": features,
            "feature_count": len(features),
            "nucleic_acid": nucleic_acid,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "features": None,
            "success": False
        }

