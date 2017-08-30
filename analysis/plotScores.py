"""
This script takes as input a CSV (with headers) containing the subject ID,
SNR, and five keyword scores for each sentence.
It outputs a boxplot for each subject's average score by SNR, as well as a
boxplot for all speakers combined.
"""

import argparse
import csv
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv', type=str,
                        help='a CSV file (with headers) \
                        containing the scores for each subject')
    return parser.parse_args()


def makeDicts(data):
    # Makes TWO dictionaries
    # subjDict is a dictionary of the scores for EACH subject
    # Key: Listener ID
    # Value: Dictionary (Key: SNR; Value: List of scores)
    # allDict is a dictionary of the scores for ALL subjects
    # Key: SNR
    # Value: List of scores
    subjDict = {}
    allDict = {}
    with open(data) as f:
        reader = csv.reader(f)
        header = next(reader)
        for line in reader:
            subj = line[1]
            snr = int(line[3])
            # The following indices assume that we did two rounds of scoring, \
            # relaxed and strict
            # You'll probably wind up changing these indices to get the scores
            kw1 = int(line[6])
            kw2 = int(line[9])
            kw3 = int(line[12])
            kw4 = int(line[15])
            kw5 = int(line[18])
            score = kw1 + kw2 + kw3 + kw4 + kw5
            # Append to subjDict
            if subj not in subjDict:
                subjDict[subj] = {}
            if snr not in subjDict[subj]:
                subjDict[subj][snr] = []
            subjDict[subj][snr].append(score)
            # Append to allDict
            if snr not in allDict:
                allDict[snr] = []
            allDict[snr].append(score)
    return subjDict, allDict


def plot(data, caption):
    plt.boxplot(data, labels=["-3", "-2", "-1", "0", "1", "2"], showmeans=True)
    plt.title(caption)
    plt.ylabel("Words Correct")
    plt.xlabel("SNR")
    plt.ylim([0, 6])
    plt.show()


def main():
    args = parse_args()
    subjDict, allDict = makeDicts(args.input_csv)
    # Loop through subjects in the dictionary and plot their individual scores
    for subj in subjDict:
        data = []
        for snr in range(-3, 3):
            data.append(subjDict[subj][snr])
        plot(data, subj)
    # Plot all
    toplot = [allDict[-3], allDict[-2], allDict[-1],
              allDict[0], allDict[1], allDict[2]]
    plot(toplot, "All Subjects")

if __name__ == "__main__":
    main()
