#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Constants and configuration for viruses_classifier."""

import os
import json
import pickle
from .libs.get_feature_indices import _get_feature_indices

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Load configuration with proper file handling
with open(os.path.join(DIR_PATH, 'conf.json'), 'r') as f:
    CONFIG = json.load(f)

ACID_TO_NUMBER = {'dna': 1.0, 'rna': 0.0}
NUM_TO_CLASS = {0: 'Eucaryota-infecting', 1: 'phage'}

# Load feature indices with proper file handling
with open(os.path.join(DIR_PATH, 'files', CONFIG['all_features_file']), 'rb') as f:
    all_features = pickle.load(f)

with open(os.path.join(DIR_PATH, 'files', CONFIG['features_file']), 'r') as f:
    features_config = json.load(f)

feature_indices = {
    classifier_name: _get_feature_indices(
        all_features,
        features_config[classifier_name]
    )
    for classifier_name in ('qda', 'knn', 'svc', 'lr')
}

classifier_paths = {
    classifier_name: os.path.join(DIR_PATH, 'files', CONFIG['classifier_files'][classifier_name])
    for classifier_name in ('qda', 'knn', 'svc', 'lr')
}
scaler_path = os.path.join(DIR_PATH, 'files', CONFIG['scaler_file'])
