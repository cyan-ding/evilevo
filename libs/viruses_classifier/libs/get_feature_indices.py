#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Feature index extraction utilities."""

import numpy as np


def _get_feature_indices(all_features, specific_features):
    """
    Return indices of specific features in list containing all features.
    
    :param all_features: list of all feature names
    :param specific_features: list of specific feature names to find indices for
    :return: numpy array of indices
    """
    return np.array([all_features.index(feat) for feat in specific_features])
