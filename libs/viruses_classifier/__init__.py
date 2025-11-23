"""
viruses_classifier - Predict host of a virus based on its genomic sequence.

This package classifies viral sequences as either:
- Eucaryota-infecting (eukaryote-infecting viruses)
- phage (bacteriophages)
"""

# Don't import compat at module level to avoid sklearn import issues
# Compatibility shims will be set up when needed (lazy import)

__version__ = '1.0.3'
__all__ = ['classify', 'seq_to_features', 'constants']

