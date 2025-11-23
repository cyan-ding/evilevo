"""
Compatibility module for loading old pickle files.

This module sets up compatibility shims lazily to avoid import issues.
"""

import sys

# Lazy imports to avoid numpy/scikit-learn compatibility issues
_sklearn_preprocessing = None
_joblib = None


def _setup_compatibility_shims():
    """Set up compatibility shims when needed (lazy import)."""
    global _sklearn_preprocessing, _joblib
    
    if _sklearn_preprocessing is None:
        try:
            import sklearn.preprocessing
            _sklearn_preprocessing = sklearn.preprocessing
            
            # Create compatibility shim for sklearn.preprocessing.data (old sklearn versions)
            if 'sklearn.preprocessing.data' not in sys.modules:
                class MockDataModule:
                    StandardScaler = sklearn.preprocessing.StandardScaler
                sys.modules['sklearn.preprocessing.data'] = MockDataModule()
        except Exception:
            # If sklearn can't be imported, that's okay - we'll handle it later
            pass
    
    if _joblib is None:
        try:
            import joblib
            _joblib = joblib
            
            # Create compatibility shim for sklearn.externals.joblib (old sklearn versions)
            if 'sklearn.externals' not in sys.modules:
                sys.modules['sklearn.externals'] = type(sys)('sklearn.externals')
            if 'sklearn.externals.joblib' not in sys.modules:
                sys.modules['sklearn.externals.joblib'] = joblib
        except Exception:
            pass


# Don't import sklearn/joblib at module level - do it lazily when needed
# This avoids numpy compatibility issues

