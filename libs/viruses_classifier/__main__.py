#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Command-line interface for viruses_classifier."""

import sys
import argparse

from . import constants
from .loader import load_joblib_safe
from .classifier import classify, seq_to_features
from .libs import read_sequence


def validate_classifier_name():
    """Validate classifier name."""
    pass  # TODO


def validate_acid_type():
    """Validate nucleic acid type."""
    pass  # TODO


def main(args=None):
    """
    Main entry point for command-line interface.
    
    :param args: command-line arguments (defaults to sys.argv[1:])
    """
    if args is None:
        args = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        description='Predict host of a virus based on its genomic sequence'
    )
    parser.add_argument(
        'sequence',
        type=str,
        help='sequence file in raw or FASTA format'
    )
    parser.add_argument(
        '--nucleic_acid',
        type=str,
        help='nucleic acid: either DNA or RNA',
        choices=['DNA', 'RNA', 'dna', 'rna'],
        required=True
    )
    parser.add_argument(
        '--classifier',
        type=str,
        help='classifier: SVC, kNN, QDA or LR',
        choices=['SVC', 'kNN', 'QDA', 'LR', 'svc', 'knn', 'qda', 'lr'],
        default='svc'
    )
    parser.add_argument(
        '--probas',
        '-p',
        dest='probas',
        action='store_true',
        help='return class probabilities instead of prediction'
    )
    
    parsed_args = parser.parse_args(args)
    classifier_name = parsed_args.classifier.lower()
    nucleic_acid = parsed_args.nucleic_acid.lower()
    
    if classifier_name not in constants.feature_indices:
        raise ValueError(f"Invalid classifier: {classifier_name}")
    
    feature_indices = constants.feature_indices[classifier_name]
    
    # Read sequence
    sequence = read_sequence.read_sequence(parsed_args.sequence)
    
    # Load models
    scaler = load_joblib_safe(constants.scaler_path)
    classifier = load_joblib_safe(constants.classifier_paths[classifier_name])
    
    # Extract features and classify
    seq_features = seq_to_features(sequence, nucleic_acid)
    result = classify(
        seq_features,
        scaler,
        classifier,
        feature_indices,
        parsed_args.probas
    )
    
    print(result)


if __name__ == '__main__':
    main(sys.argv[1:])
