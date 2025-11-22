# Test Viruses Not in Database

**IMPORTANT**: Your database downloads by **genus**, which means it includes ALL species in each genus. So if you download `Flavivirus`, you get ALL Flaviviruses (Dengue, Zika, West Nile, Yellow Fever, etc.). 

This means many viruses I initially listed **ARE already in your database** if you downloaded those genera!

## What's Actually Missing (Different Genera/Families)

These are dangerous viruses in **different genera** that won't be in your database:

### 1. **Rabies Virus (Lyssavirus)** ⭐ BEST TEST CASE
- **Why test**: Extremely dangerous (100% fatal if untreated), completely different family
- **Genus**: `Lyssavirus` (NOT in your DB)
- **Species**: `Rabies lyssavirus`
- **Risk**: Very high - causes fatal encephalitis
- **Similarity to DB**: Low - different family, should test "unknown viral" detection
- **NCBI Accession**: NC_001542.1
- **Expected Result**: LOW risk (unknown viral characteristics)

### 2. **Hantavirus (Sin Nombre)**
- **Why test**: Dangerous, different genus from your Bunyaviruses
- **Genus**: `Orthohantavirus` (NOT in your DB - you have `Orthonairovirus` and `Phlebovirus`)
- **Species**: `Sin Nombre orthohantavirus`
- **Risk**: Very high - causes Hantavirus Pulmonary Syndrome (HPS)
- **Similarity to DB**: Low - different genus
- **NCBI Accession**: NC_005216.1
- **Expected Result**: LOW risk (unknown viral characteristics)

### 3. **Hepatitis B Virus**
- **Why test**: Very common, completely different family
- **Genus**: `Orthohepadnavirus` (NOT in your DB)
- **Species**: `Hepatitis B virus`
- **Risk**: High - causes chronic liver disease and cancer
- **Similarity to DB**: Low - different family
- **NCBI Accession**: NC_003977.1
- **Expected Result**: LOW risk (unknown viral characteristics)

### 4. **Hepatitis C Virus**
- **Why test**: Very common, different family
- **Genus**: `Hepacivirus` (NOT in your DB)
- **Species**: `Hepatitis C virus`
- **Risk**: High - causes chronic liver disease
- **Similarity to DB**: Low - different family
- **NCBI Accession**: NC_004102.1
- **Expected Result**: LOW risk

### 5. **Hepatitis E Virus**
- **Why test**: Different family
- **Genus**: `Orthohepevirus` (NOT in your DB)
- **Species**: `Hepatitis E virus`
- **Risk**: Moderate-High - can be severe in pregnant women
- **Similarity to DB**: Low - different family
- **NCBI Accession**: NC_001434.1
- **Expected Result**: LOW risk

### 6. **Measles Virus**
- **Why test**: Different genus from your paramyxoviruses
- **Genus**: `Morbillivirus` (you have this, but only Rinderpest and PPRV - Measles is different species)
- **Species**: `Measles morbillivirus`
- **Risk**: High - causes severe disease
- **Similarity to DB**: Should show HIGH similarity to Rinderpest/PPRV (same genus)
- **NCBI Accession**: NC_001498.1
- **Expected Result**: MEDIUM-HIGH risk (related to Rinderpest)

### 7. **Mumps Virus**
- **Why test**: Different genus from your paramyxoviruses
- **Genus**: `Rubulavirus` (NOT in your DB)
- **Species**: `Mumps rubulavirus`
- **Risk**: Moderate - causes parotitis and complications
- **Similarity to DB**: Low - different genus
- **NCBI Accession**: NC_002200.1
- **Expected Result**: LOW risk

### 8. **Rotavirus**
- **Why test**: Completely different family
- **Genus**: `Rotavirus` (NOT in your DB)
- **Species**: `Rotavirus A` (most common)
- **Risk**: High - causes severe diarrhea in children
- **Similarity to DB**: Low - different family
- **NCBI Accession**: NC_011500.2
- **Expected Result**: LOW risk

## What's Already in Your Database (If You Downloaded by Genus)

Since you download by genus, these **ARE already in your database**:

✅ **All Flaviviruses** (Dengue, Zika, West Nile, Yellow Fever, Japanese Encephalitis, TBEV, KFDV, etc.)
✅ **All Alphaviruses** (Chikungunya, Western Equine Encephalitis, EEEV, VEEV, etc.)
✅ **All Betacoronaviruses** (MERS-CoV, SARS-CoV-2, SARS-CoV, etc.)
✅ **All Mammarenaviruses** (LCMV, Lassa, Lujo, etc.)
✅ **All Henipaviruses** (Nipah, Hendra, etc.)
✅ **All Orthopoxviruses** (Variola, Monkeypox, Vaccinia, etc.)

## Best Test Strategy

Since most viruses in the same genus are already in your DB, focus on testing:

1. **Different families** (Rabies, Hepatitis B/C/E, Rotavirus) - should show LOW risk
2. **Different genera in same family** (Hantavirus vs CCHFV/RVFV) - should show LOW risk
3. **Same genus, different species** (Measles vs Rinderpest) - should show MEDIUM-HIGH risk

## Expected Detection Results

### Should Show MEDIUM-HIGH Risk (Same genus, different species):
- **Measles**: Should match Rinderpest/PPRV (same genus `Morbillivirus`) - 70-85% identity

### Should Show LOW Risk (Unknown but viral characteristics):
- **Rabies**: Different family (`Lyssavirus`), but viral genome characteristics
- **Hantavirus**: Different genus (`Orthohantavirus` vs your `Orthonairovirus`/`Phlebovirus`), but viral characteristics
- **Hepatitis B/C/E**: Different families, but viral characteristics
- **Rotavirus**: Different family, but viral characteristics
- **Mumps**: Different genus (`Rubulavirus`), but viral characteristics

## How to Get Test Sequences

You can download these sequences from NCBI:

```bash
# Example: Download MERS-CoV sequence
efetch -db nucleotide -id NC_019843.3 -format fasta > mers_cov.fasta

# Or use ncbi-genome-download
ncbi-genome-download viral -g Betacoronavirus -s refseq -F fasta
```

## Testing Strategy

1. **Test same-genus viruses** (Measles - same genus as Rinderpest) - should show MEDIUM-HIGH risk
2. **Test different-family viruses** (Rabies, Hepatitis B/C/E, Rotavirus) - should show LOW risk or trigger "unknown viral" detection
3. **Test different-genus viruses** (Hantavirus, Mumps) - should show LOW risk
4. **Test completely unrelated sequences** (bacterial, human DNA) - should show NONE or very LOW risk

This will verify that your system:
- ✅ Detects related viruses in same genus (even if different species)
- ✅ Assigns appropriate risk to unknown viral sequences from different families
- ✅ Doesn't give false positives for non-viral sequences

## Quick Test Commands

```bash
# Download Rabies (best test - different family)
efetch -db nucleotide -id NC_001542.1 -format fasta > test_rabies.fasta

# Download Measles (should match Rinderpest - same genus)
efetch -db nucleotide -id NC_001498.1 -format fasta > test_measles.fasta

# Download Hantavirus (different genus from your Bunyaviruses)
efetch -db nucleotide -id NC_005216.1 -format fasta > test_hantavirus.fasta

# Test with your detector
python3 -m detector.layer1.layer1_blast
# Then modify the test sequence in the script to use one of these
```

