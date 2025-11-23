#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Classification functions for viral sequences."""

import numpy as np
from . import constants
from .libs import sequence_processing


def probas_to_dict(probas, translation_dict):
    """
    Transforms vector of probabilities to dictionary {"type of virus": probability, ...}
    
    :param probas: array of probabilities
    :param translation_dict: dictionary mapping indices to class names
    :return: dictionary mapping class names to probabilities
    """
    return {translation_dict[i]: probas[i] for i in range(len(probas))}


def seq_to_features(seq, nuc_acid):
    """
    Transforms sequence to its features.
    
    :param seq: nucleotide sequence
    :param nuc_acid: either 'dna' or 'rna'
    :return: list of sequence features (numbers)
    """
    acid_code = constants.ACID_TO_NUMBER[nuc_acid]
    nuc_frequencies = sequence_processing.nucFrequencies(seq, 2)
    nuc_frequencies_ = {
        'nuc_frequencies__' + key: value 
        for key, value in nuc_frequencies.items()
    }
    relative_nuc_frequencies_one_strand_ = {
        'relative_nuc_frequencies_one_strand__' + key: value 
        for key, value in sequence_processing.relativeNucFrequencies(nuc_frequencies, 1).items()
    }
    relative_trinuc_freqs_one_strand_ = {
        'relative_trinuc_freqs_one_strand__' + key: value 
        for key, value in sequence_processing.thirdOrderBias(seq, 1).items()
    }
    freqs = nuc_frequencies_
    freqs.update(relative_nuc_frequencies_one_strand_)
    freqs.update(relative_trinuc_freqs_one_strand_)
    vals = [acid_code]
    vals.extend([freqs[k] for k in sorted(freqs)])
    return vals


def classify(sequence_features, scaler, classifier, feature_indices=None, probas=False):
    """
    Classify viral sequence.
    
    :param sequence_features: list of numbers - features of the sequence to be classified
    :param scaler: trained scaler
    :param classifier: trained classifier
    :param feature_indices: indices of selected features
    :param probas: when True function returns class probabilities instead of class
    :return: class name (e.g., "Eucaryota-infecting" or "phage") or class probabilities
    """
    if feature_indices is not None:
        vals = scaler.transform(np.array(sequence_features).reshape(1, -1))[:, feature_indices]
    else:
        # no feature selection
        vals = scaler.transform(np.array(sequence_features).reshape(1, -1))
    if probas:
        clf_val = classifier.predict_proba(vals)[0]
        return probas_to_dict(clf_val, constants.NUM_TO_CLASS)
    return constants.NUM_TO_CLASS[classifier.predict(vals)[0]]
