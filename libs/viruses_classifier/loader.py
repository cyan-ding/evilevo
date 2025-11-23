"""
Custom loader for old joblib pickle files with compatibility shims.
"""

import sys


def load_joblib_safe(filepath):
    """
    Safely load joblib pickle files with compatibility shims.
    
    :param filepath: path to the pickle file
    :return: loaded object
    """
    # Lazy imports to avoid numpy/scikit-learn compatibility issues
    try:
        import joblib
    except ImportError:
        raise ImportError("joblib is required. Install with: pip install joblib")
    
    # Set up compatibility shims only when needed
    try:
        import sklearn.preprocessing
        
        if 'sklearn.preprocessing.data' not in sys.modules:
            class MockDataModule:
                StandardScaler = sklearn.preprocessing.StandardScaler
            sys.modules['sklearn.preprocessing.data'] = MockDataModule()
    except Exception:
        # If sklearn can't be imported, continue anyway
        # The pickle files might not need it
        pass
    
    if 'sklearn.externals' not in sys.modules:
        sys.modules['sklearn.externals'] = type(sys)('sklearn.externals')
    if 'sklearn.externals.joblib' not in sys.modules:
        sys.modules['sklearn.externals.joblib'] = joblib
    
    # Now load with joblib
    return joblib.load(filepath)

