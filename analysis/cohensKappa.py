#!/usr/bin/env python3
"""
Takes a csv of the "compare scores" sheet
Calculated and prints the relaxed and strict Cohen's kappa scores
You'll need to modify the indices and remove a few lines
when you're no longer doing two types of scores
"""

import csv
import sys
from sklearn.metrics import cohen_kappa_score

fname = sys.argv[1]
expected_header = 'Listener,Sentence,#,KW1,KW1 (R),KW1 (S),KW2,KW2 (R),KW2 (S),KW3,KW3 (R),KW3 (S),KW4,KW4 (R),KW4 (S),KW5,KW5 (R),KW5 (S),KW1,KW1 (R),KW1 (S),KW2,KW2 (R),KW2 (S),KW3,KW3 (R),KW3 (S),KW4,KW4 (R),KW4 (S),KW5,KW5 (R),KW5 (S)'

rater1R_cols = [4, 7, 10, 13, 16]
rater1S_cols = [5, 8, 11, 14, 17]
rater2R_cols = [19, 22, 25, 28, 31]
rater2S_cols = [20, 23, 26, 29, 32]

rater1R = []  # First rater, relaxed
rater1S = []  # First rater, strict
rater2R = []  # Second rater, relaxed
rater2S = []  # Second rater, strict

with open(fname) as f:
    reader = csv.reader(f)
    _ = next(reader)       # first row is meta-header
    header = next(reader)  # here are the proper column names
    if header != expected_header.split(','):
        raise RuntimeError('header mismatch! Update expected_header and '
                           'double-check column numbers in script.')
    for line in reader:
        # Skip any sentences that haven't been scored yet
        if line[rater1R_cols[0]] != '':
            rater1R.extend([int(line[x]) for x in rater1R_cols])
            rater2R.extend([int(line[x]) for x in rater2R_cols])
            rater1S.extend([int(line[x]) for x in rater1S_cols])
            rater2S.extend([int(line[x]) for x in rater2S_cols])
print("Relaxed:", cohen_kappa_score(rater1R, rater2R))
print("Strict:", cohen_kappa_score(rater1S, rater2S))
