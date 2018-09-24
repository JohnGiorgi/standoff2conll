# standoff2conll

A tool for converting a corpora from brat-flavored Standoff to CoNLL format. Requires  `python2`.

## Installation

To use the tool, clone this repository

```
git clone https://github.com/JohnGiorgi/standoff2conll.git
cd standoff2conll
```

## Usage

The tool expects a directory containing a corpus in brat-flavored Standoff, e.g.,

```
.
├── NCBI_Disease
│   ├── 23402.ann
│   ├── 23402.txt
│   └── ...
```

To convert the `train` partition to CoNLL format:

```
python2 standoff2conll path/to/NCBI_Disease/ > NCBI_Disease_CoNLL.tsv
```

Run `python standoff2conll --help` to see all command line arguments.
