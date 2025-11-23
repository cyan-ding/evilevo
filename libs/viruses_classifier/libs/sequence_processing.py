#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Sequence processing functions for feature extraction."""

import itertools
from functools import reduce

NA_IUPAC = {'A':('A',), 'C':('C',), 'G':('G',), 'T':('T',),
            'R':('A','G'), 'Y':('C','T'), 'M':('A','C'), 'K':('G','T'),
            'S':('C','G'), 'W':('A','T'), 'B':('C','G','T'), 'D':('A','G','T'),
            'H':('A','C','T'), 'V':('A','C','G'), 'N':('A','C','G','T')}

transcription_dict={'A':'T', 'C':'G', 'G':'C', 'T':'A', 'U':'A', 'R':'Y',
                    'Y':'R', 'N':'N', 'M':'K', 'K':'M', 'S':'W', 'W':'S',
                    'B':'V', 'V':'B', 'D':'H', 'H':'D'}


def combinations(n, inlist, outlist=None):
    """
    Recursive function that creates all possible combinations
    of characters of specified length.
    
    :param n: length
    :param inlist: list of characters
    :param outlist: result list (internal use)
    :return: list of combinations
    """
    if outlist is None:
        outlist = []
    if n == 0:
        return outlist
    else:
        if outlist:
            new_outlist = []
            for element in outlist:
                new_outlist.extend([element + x for x in inlist])
            return combinations(n - 1, inlist, new_outlist)
        else:
            return combinations(n - 1, inlist, inlist)

def betterCount(sequence, word):
    """
    Return the number of overlapping occurrences of substring 'word' in string 'sequence'.
    
    :param sequence: sequence string
    :param word: substring to count
    :return: number of occurrences
    """
    ret_val = 0
    pos = sequence.find(word)
    if pos == -1:
        return 0
    pos += 1
    while pos:
        pos = sequence.find(word, pos)
        if pos == -1:
            break
        ret_val += 1
        pos += 1
    return ret_val

def frequence(sequence, nuc, count=None):
    """
    Calculate frequency of nucleotide or k-mer in sequence.
    
    :param sequence: sequence string
    :param nuc: nucleotide or k-mer
    :param count: pre-computed count (optional)
    :return: frequency
    """
    if len(sequence) == 0:
        return 0.0
    if len(nuc) == 1:
        count = count if count is not None else sequence.count(nuc)
        return count / float(len(sequence))
    count = count if count is not None else betterCount(sequence, nuc)
    return count / float(len(sequence) - len(nuc) + 1)

def nucList(sequence, length):
    """
    Return overlapping subsequences of specified length.
    
    :param sequence: sequence string
    :param length: desired length
    :return: list of subsequences
    """
    return [sequence[x:x + length] for x in range(len(sequence) - length + 1)]

def makeCombinations(oligo_nuc, iupac=None):
    """
    Return list of actual oligonucleotides based on degenerate nucleotides.
    
    :param oligo_nuc: oligonucleotide with degenerate nucleotides
    :param iupac: IUPAC code dictionary
    :return: set of actual oligonucleotides
    """
    if iupac is None:
        iupac = NA_IUPAC
    oligo_nuc_list = []
    for nuc in oligo_nuc:
        nucs = None
        for key in iupac.keys():
            if nuc in key:
                nucs = iupac[key]
                break
        if nucs is None:
            nucs = (nuc,)  # Fallback for unknown nucleotides
        if oligo_nuc_list:
            new_oligo_nuc_list = []
            for element in oligo_nuc_list:
                new_oligo_nuc_list.extend(['%s%s' % (element, x) for x in nucs])
            oligo_nuc_list = new_oligo_nuc_list
        else:
            oligo_nuc_list = list(nucs)
    return set(oligo_nuc_list)

def reverseComplement(a_string, transcript_dict=None):
    """
    Return reverse complement of a sequence.
    
    :param a_string: sequence string
    :param transcript_dict: transcription dictionary
    :return: reverse complement sequence
    """
    if transcript_dict is None:
        transcript_dict = transcription_dict
    a_list = [transcript_dict.get(s, s) for s in a_string]
    a_list.reverse()
    return ''.join(a_list)

def thirdOrderBias(seq, strand, mono=('A', 'C', 'G', 'T'), transcript_dict=None):
    """
    Relative frequencies of nucleotides depending on mono and di frequencies.
    See: http://www.pnas.org/content/89/4/1358.full.pdf
    
    :param seq: sequence string
    :param strand: strand number (1 or 2)
    :param mono: tuple of mononucleotides
    :param transcript_dict: transcription dictionary
    :return: dictionary of relative frequencies
    """
    if transcript_dict is None:
        transcript_dict = transcription_dict
    assert len(seq) > 2
    assert strand in (1, 2)
    nuc_freqs = nucFrequencies(seq, 2)
    mono_freqs = {k: v for k, v in nuc_freqs.items() if len(k) == 1}
    di_freqs = {k: v for k, v in nuc_freqs.items() if len(k) == 2}
    tri_freqs = {k: v for k, v in nucFrequencies(seq, 3).items() if len(k) == 3}
    ret_dict = {}
    for key in tri_freqs:
        fxyz = tri_freqs[key]
        rev_key = reverseComplement(key, transcript_dict)
        fixyz = tri_freqs.get(rev_key, 0)
        if fxyz == 0 and (strand == 1 or (strand == 2 and fixyz == 0)):
            ret_dict[key] = 0.0
        else:
            fxy = di_freqs.get(key[:2], 0)
            fyz = di_freqs.get(key[1:], 0)
            fxnz = sum(tri_freqs.get('%s%s%s' % (key[0], n, key[2]), 0) for n in mono)
            if strand == 1:
                ret_dict[key] = float(fxyz) * mono_freqs.get(key[0], 0) * mono_freqs.get(key[1], 0) * mono_freqs.get(key[2], 0) / max(fxy * fyz * fxnz, 1e-10)
            else:
                fix = mono_freqs.get(transcript_dict.get(key[0], key[0]), 0)
                fiy = mono_freqs.get(transcript_dict.get(key[1], key[1]), 0)
                fiz = mono_freqs.get(transcript_dict.get(key[2], key[2]), 0)
                fixy = di_freqs.get(reverseComplement(key[:2], transcript_dict), 0)
                fiyz = di_freqs.get(reverseComplement(key[1:], transcript_dict), 0)
                fixnz = sum(tri_freqs.get('%s%s%s' % (transcript_dict.get(key[2], key[2]), n, transcript_dict.get(key[0], key[0])), 0) for n in mono)
                ret_dict[key] = float(fxyz + fixyz) * (mono_freqs.get(key[0], 0) + fix) * (mono_freqs.get(key[1], 0) + fiy) * (mono_freqs.get(key[2], 0) + fiz) / max(2 * (fxy + fixy) * (fyz + fiyz) * (fxnz + fixnz), 1e-10)
    return ret_dict


def nucFrequencies(sequence, length, mono=('A', 'C', 'G', 'T')):
    """
    Return frequencies of oligonucleotides of specified length + mononucleotide frequencies.
    
    :param sequence: sequence string
    :param length: desired oligonucleotide length
    :param mono: tuple of mononucleotides
    :return: dictionary of frequencies
    """
    ret_dict = {}
    seq_len = len(sequence)
    mono_count = dict([(nuc, 0) for nuc in mono])
    desired_nucs = combinations(length, mono)

    for nuc in mono:
        count = betterCount(sequence, nuc)
        ret_dict[nuc] = frequence(sequence, nuc, count)
        mono_count[nuc] = count

    for nuc in desired_nucs:
        ret_dict[nuc] = frequence(sequence, nuc)

    if seq_len != sum(mono_count.values()):
        # mamy zdegenerowane (we have degenerate nucleotides)
        for nuc in sequence:
            if nuc not in mono and nuc in NA_IUPAC:
                for sub_nuc in NA_IUPAC[nuc]:
                    ret_dict[sub_nuc] = ret_dict.get(sub_nuc, 0) + 1.0 / seq_len / len(NA_IUPAC[nuc])
        if length - 1:
            for nuc in nucList(sequence, length):
                if nuc not in desired_nucs:
                    real_nucs = makeCombinations(nuc)
                    for real_nuc in real_nucs:
                        ret_dict[real_nuc] = ret_dict.get(real_nuc, 0) + 1.0 / (seq_len - length + 1) / len(real_nucs)
    return ret_dict

def product(a_list):
    """
    Return product of list elements.
    
    :param a_list: list of numbers
    :return: product
    """
    if not a_list:
        return 1
    return reduce(lambda x, y: x * y, a_list)


def zeroDivision(a, b):
    """
    Safe division that returns 0 on ZeroDivisionError.
    
    :param a: numerator
    :param b: denominator
    :return: a/b or 0 if b is 0
    """
    try:
        return a / b
    except ZeroDivisionError:
        return 0

def relativeNucFrequencies(in_dict, strands, transcript_dict=None):
    """
    Takes result of nucFrequencies. Returns dictionary with relative frequencies.
    Assumes oligo frequency depends only on mono, not e.g. trinuc on dinuc.
    
    :param in_dict: dictionary from nucFrequencies
    :param strands: number of strands (1 or 2)
    :param transcript_dict: transcription dictionary
    :return: dictionary of relative frequencies
    """
    if transcript_dict is None:
        transcript_dict = transcription_dict
    # częstotliwość oligonuc na obu niciach liczona według:
    # http://www.pnas.org/content/89/4/1358.full.pdf
    mono_dict = dict([(x, in_dict[x]) for x in in_dict if len(x) == 1])
    oligo_dict = dict([(x, in_dict[x]) for x in in_dict if len(x) > 1])
    
    if not oligo_dict:
        return in_dict
    
    nuc_len = len(list(oligo_dict.keys())[0])
    assert all(nuc_len == len(k) for k in oligo_dict)
    
    if len(mono_dict) != 4:
        for k in set(['A', 'C', 'G', 'T']) - set(mono_dict):
            mono_dict[k] = 0
    
    # jeśli oligo_dict jest niekompletny, tzn. dla niektórych oligo nie ma wpisów ( powinny być klucz:0 )
    if len(oligo_dict) != nuc_len**2:
        for k in [''.join(x) for x in itertools.product(mono_dict, repeat=nuc_len)]:
            if k not in oligo_dict:
                oligo_dict[k] = 0
    
    if strands - 1:
        try:
            return {
                x: 2**(nuc_len-1) * (oligo_dict[x] + oligo_dict[reverseComplement(x)]) / product([mono_dict[y] + mono_dict[transcript_dict[y]] for y in x])
                for x in oligo_dict
            }
        except ZeroDivisionError:
            return {
                x: 2**(nuc_len-1) * zeroDivision(
                    (oligo_dict[x] + oligo_dict[reverseComplement(x)]),
                    product([mono_dict[y] + mono_dict[transcript_dict[y]] for y in x])
                )
                for x in oligo_dict
            }
    else:
        try:
            return {
                x: float(oligo_dict[x]) / product([mono_dict[y] for y in x])
                for x in oligo_dict
            }
        except ZeroDivisionError:
            return {
                x: float(zeroDivision(oligo_dict[x], product([mono_dict[y] for y in x])))
                for x in oligo_dict
            }