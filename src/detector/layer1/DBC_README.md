# Database of Concern (DBC) Setup Guide

This guide explains how to download Select Agent genomes and create a BLAST database for Layer 1 detection.

## Quick Start

### Option 1: Download Select Agent Genera (Recommended)

This downloads only the genera containing Select Agents, which is faster and more targeted:

```bash
cd /home/ubuntu/cyan/evilevo
python3 -m detector.download_dbc --output-dir dbc --section refseq --database-name dbc
```

### Option 2: Download All Viral Genomes (Comprehensive)

This downloads ALL viral genomes from NCBI, which is more comprehensive but much larger:

```bash
python3 -m detector.download_dbc --output-dir dbc --section refseq --database-name dbc --all-viruses
```

## What Gets Downloaded

The script downloads genomes for these Select Agent genera:

**Filoviruses:**
- Ebolavirus
- Marburgvirus

**Poxviruses:**
- Orthopoxvirus (Variola, Monkeypox)
- Capripoxvirus (Goat pox, Lumpy skin disease, Sheep pox)

**Paramyxoviruses:**
- Henipavirus (Nipah, Hendra)
- Morbillivirus (Rinderpest, PPRV)
- Avulavirus (Newcastle disease)

**Coronaviruses:**
- Betacoronavirus (SARS-CoV)

**Flaviviruses/Togaviruses:**
- Alphavirus (EEEV, VEEV)
- Flavivirus (TBEV, KFDV)

**Arenaviruses:**
- Mammarenavirus (Lassa, Lujo, South American HF viruses)

**Bunyaviruses:**
- Orthonairovirus (CCHFV)
- Phlebovirus (RVFV)

**Influenza:**
- Alphainfluenzavirus (1918 H1N1, Avian flu)

**Picornaviruses:**
- Aphthovirus (FMDV)
- Enterovirus (SVDV)

**Other:**
- Asfivirus (African swine fever)
- Pestivirus (Classical swine fever)

## Output Structure

After running the script, you'll have:

```
dbc/
├── genomes/              # Downloaded genome files
│   └── viral/
│       └── {genus}/
│           └── {species}/
│               └── {accession}/
│                   └── *.fna
├── dbc_sequences.fasta    # Combined FASTA file
├── dbc.nhr               # BLAST database files
├── dbc.nin
└── dbc.nsq
```

## Using the Database

Once created, use the database with Layer 1 detection:

```python
from detector.layer1_blast import detect_layer1

result = detect_layer1(
    query_sequence="ATGCGATCG...",
    database_path="dbc/dbc",  # Path without extension
    check_gc=True
)

print(f"Risk Level: {result.risk_level}")
print(f"Risk Score: {result.risk_score}")
```

## Troubleshooting

### No sequences downloaded

- Check your internet connection
- Try using `--section genbank` instead of `refseq`
- Some genera might not have genomes in RefSeq; try downloading all viruses

### Database creation fails

- Ensure BLAST+ is installed: `sudo apt-get install ncbi-blast+`
- Check that the FASTA file exists and is not empty
- Verify you have write permissions in the output directory

### Download is too slow

- Use `--all-viruses` to download everything at once (parallelized)
- Or download specific genera manually using ncbi-genome-download directly

## Manual Download (Alternative)

If the automated script doesn't work, you can manually download genomes:

```bash
# Download specific genus
ncbi-genome-download viral -g Ebolavirus -F fasta -o genomes/

# Download all viruses
ncbi-genome-download viral -F fasta -o genomes/

# Then combine and create database
python3 -c "
from detector.download_dbc import collect_fasta_files
from detector.layer1_blast import create_blast_database
collect_fasta_files('genomes/viral', 'dbc_sequences.fasta')
create_blast_database('dbc_sequences.fasta', 'dbc', 'nucl')
"
```

## Notes

- The download process can take 30 minutes to several hours depending on your connection
- The final database size will be several GB
- Make sure you have sufficient disk space (at least 10-20 GB free)
- The script uses RefSeq by default, which has higher quality but fewer genomes than GenBank

