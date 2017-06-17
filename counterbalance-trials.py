#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Script 'counterbalance-trials.py'
===============================================================================

This script counterbalances trial parameters.
"""
# @author: drmccloy
# Created on Thu Jun 08 11:06:09 2017
# License: BSD (3-clause)

import yaml
import numpy as np
import pandas as pd

# set random seed
rand = np.random.RandomState(seed=15485863)  # the one millionth prime

# load external parameter file
paramfile = 'params.yaml'
with open(paramfile, 'r') as pf:
    params = yaml.load(pf)
    snrs = params['snrs']
    talkers = params['talkers']
    sentences = params['sentences']
    n_listeners = params['n_listeners']

# initialize design matrix. at this point we merely establish that each
# listener will hear each sentence exactly once
design_matrix = dict(listener=np.repeat(range(n_listeners), len(sentences)),
                     sentence=np.tile(sentences, n_listeners))
design_matrix = pd.DataFrame(design_matrix)

# assign SNRs to sentences
n_snr_repeats = int(np.ceil(len(sentences) / len(snrs)))
snr_assignments = []
for subj in range(n_listeners):
    # start at a different point in the sequence for each listener
    this_snrs = np.roll(snrs, subj)
    # tile to the right length
    this_snrs = np.tile(this_snrs, n_snr_repeats)[:len(sentences)]
    # save
    snr_assignments.extend(this_snrs)
design_matrix['snr'] = snr_assignments
design_matrix['snr'] = design_matrix['snr'].map(lambda x: '{:+d}'.format(x))

# assign talkers to sentence/SNR pairings. Start at a different point in the
# talker sequence **for each tiling of the talker list** (avoids problems that
# arise when len(snrs) and len(talkers) are integer multiples of one another).
n_talker_repeats = int(np.ceil(design_matrix.shape[0] / len(talkers)))
talker_assignments = []

for rep in range(n_talker_repeats):
    this_talkers = np.roll(talkers, rep)
    talker_assignments.extend(this_talkers)
design_matrix['talker'] = talker_assignments[:design_matrix.shape[0]]

# verify that everything worked
print('\nthis should show different SNRs and talkers for a given sentence:')
print(design_matrix.loc[design_matrix['sentence'] == '01-07'].head(10))
print('\nthis should show different sentences and SNRs for a given talker:')
print(design_matrix.loc[design_matrix['talker'] == 'NWF002'].head(10))
print('\nthis should show different SNRs for a given talker/sentence pairing:')
print(design_matrix.loc[(design_matrix['sentence'] == '01-07') &
                        (design_matrix['talker'] == 'NWF002')])

# each sentence should happen only once per listener
assert all(design_matrix.groupby(['listener', 'sentence']).count() == 1)
# does each combination occur the same number of times?
assert all(design_matrix.groupby(['listener', 'snr']).count().nunique() == 1)
assert all(design_matrix.groupby(['talker', 'snr']).count().nunique() == 1)
assert all(design_matrix.groupby(['listener', 'talker']).count().nunique() == 1)
assert all(design_matrix.groupby(['listener', 'talker', 'snr']).count().nunique() == 1)
# It is possible that the best we could do is to have, say, 30 reps of some
#  sentences and 29 reps of the remaining sentences.  So if any of the above
# "assert" statements failed, try changing the "== 1" to "<= 2". If that works,
# then remove the "assert all" and ".nunique()..." parts of each line, and make
# sure the .min() and .max() of each count are within 1 of each other.

# check proposal against the list of missing sentence / talker combinations
stims = (design_matrix['talker'] + '_' +
         design_matrix['sentence']).values.astype(str)
miss = pd.read_csv('missing-sentences.csv', header=0)
missing_stims = (miss['talker'] + '_' + miss['sentence']).values.astype(str)
missing_stim_indices = np.where(np.in1d(stims, missing_stims))[0]
missing_trials = design_matrix.iloc[missing_stim_indices].copy()
missing_talkers = missing_trials['talker'].values.astype(str)
# for the missing talker/sentence combinations, shuffle the talker assignments
# (preserving the relative number of each). The approach below may not work if
# any(missing_trials.groupby('sentence').aggregate('nunique')['talker'] != 1)
# (i.e., if some sentences are missing for >1 talker)
# NOTE: value_counts() defaults to descending order, which is in our favor here
missing_talker_counts = missing_trials['talker'].value_counts()
shuffled_talkers = np.full_like(missing_talkers, '')
converged, iteration, max_iter = False, 1, 1000
while iteration < max_iter and not converged:
    for talker, count in missing_talker_counts.iteritems():
        legal_indices = np.where(missing_talkers != talker)[0]
        empty_indices = np.where(shuffled_talkers == '')[0]
        available_indices = np.intersect1d(legal_indices, empty_indices)
        try:
            ixs = rand.choice(available_indices, count, replace=False)
            shuffled_talkers[ixs] = talker
            converged = True
        except ValueError:
            iteration += 1
success = ['resolved', 'could not resolve'][int(iteration == max_iter)]
plural = ['', 's'][int(iteration > 1)]
message = '{} missing sentences in {} iteration{}.'.format(success, iteration,
                                                           plural)
if converged:
    print(message)
else:
    raise RuntimeError(message)
# assign the shuffled talker list into the indices of the design matrix that
# were problematic
design_matrix.loc[design_matrix.index[missing_stim_indices],
                  'talker'] = shuffled_talkers

# add a filename column
design_matrix['filename'] = (design_matrix[['talker', 'sentence',
                                            'snr']].apply('_'.join, axis=1) +
                             '.wav')

# now randomize presentation order, then re-sort by listener
design_matrix = design_matrix.sample(frac=1, random_state=rand)
design_matrix.sort_values(by='listener', inplace=True)
design_matrix.reset_index(drop=True, inplace=True)

# write out design matrix
design_matrix.to_csv('design-matrix.csv', index=False)
