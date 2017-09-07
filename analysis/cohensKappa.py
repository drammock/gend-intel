"""
Takes a csv of the "compare scores" sheet
Calculated and prints the relaxed and strict Cohen's kappa scores
You'll need to modify the indices and remove a few lines
when you're no longer doing two types of scores
"""

import csv
from sklearn.metrics import cohen_kappa_score

rater1R = []  # First rater, relaxed
rater1S = []  # First rater, strict
rater2R = []  # Second rater, relaxed
rater2S = []  # Second rater, strict

with open("/Users/Laura/Desktop/NIH/gend-intel-scoring/compare.csv") as f:
    reader = csv.reader(f)
    header = next(reader)
    header = next(reader)  # There are two header lines in the spreadsheet
    for line in reader:
        if line[4] != '':  # Skip any sentences that haven't been scored yet
            rater1R.append(int(line[4]) + int(line[7]) + int(line[10]) +
                           int(line[13]) + int(line[16]))
            rater1S.append(int(line[5]) + int(line[8]) + int(line[11]) +
                           int(line[14]) + int(line[17]))
            rater2R.append(int(line[19]) + int(line[22]) + int(line[25]) +
                           int(line[28]) + int(line[31]))
            rater2S.append(int(line[20]) + int(line[23]) + int(line[26]) +
                           int(line[29]) + int(line[32]))
print("Relaxed:", cohen_kappa_score(rater1R, rater2R))
print("Strict:", cohen_kappa_score(rater1S, rater2S))
