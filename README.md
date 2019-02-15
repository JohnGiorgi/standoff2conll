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
├── example_corpus
│   ├── 23402.ann
│   ├── 23402.txt
│   └── ...
```

To convert to CoNLL format:

```
python2 standoff2conll.py path/to/example_corpus/ > example_corpus.tsv
```

Run `python2 standoff2conll.py --help` to see all command line arguments.
