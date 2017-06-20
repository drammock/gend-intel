#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Script 'run-experiment.py'
===============================================================================

This script plays stimuli and records verbal responses.
"""
# @author: drmccloy
# Created on Thu Jun 15 13:38:22 2017
# License: BSD (3-clause)

import sys
import yaml
import queue
import os.path as op
from os import makedirs
import numpy as np
import pandas as pd
import sounddevice as sd
import soundfile as sf
from glob import glob
from expyfun import ExperimentController, get_keyboard_input
from expyfun.stimuli import read_wav

# load external parameter file
paramfile = 'params.yaml'
with open(paramfile, 'r') as pf:
    params = yaml.load(pf)
    block_len = params['block_len']
    sentences = params['sentences']
n_blocks = int(np.ceil(len(sentences) / block_len))

# load design matrices
design_matrix = pd.read_csv('design-matrix.csv', header=0)
training_stimuli = pd.read_csv('training-list.csv', header=0)

# experiment setup
stim_dir = 'stimuli'
train_dir = op.join(stim_dir, 'training')
live_keys = ['space']
stimuli = glob(op.join(stim_dir, '*.wav'))
sd.default.channels, sd.default.samplerate = (1, 44100)
ec_params = dict(exp_name='gend-intel', audio_controller='pyglet',
                 response_device='keyboard', stim_fs=44100, stim_rms=0.01,
                 check_rms=None, output_dir='logs', force_quit=['q'],
                 full_screen=False, window_size=(1024, 768), version='dev')

# messages
msg = {'first_trial': ('Start at which trial? (leave blank and push ENTER to '
                       'start at beginning): '),
       'welcome': ('Press "{0}{3}{1}" any time this window is visible to quit '
                   'the experiment.\n\nListener responses will start recording'
                   ' automatically after each stimulus; press "{0}Ctrl+C{1}" '
                   'to stop recording and advance to the next trial (for '
                   'recording to work, this window must disappear during the '
                   'response so the terminal can catch the Ctrl+C keystroke). '
                   '\n\nTalk to the subject, then press "{0}{2}{1}" when they '
                   'are ready to begin the training block.'),
       'end_training': ('End of training.\n\nTalk to the subject, then press '
                        '"{0}{2}{1}" when they are ready to start the first '
                        'real trial.'),
       'end_block': ('Finished block {} of {}.\n\nTalk to the subject and '
                     'press "{}" when they are ready to continue.'),
       'now_playing': ('now playing:\n\n{2} {0}{3}{1}\n{4} {0}{5}{1}\n{6} '
                       '{0}{7}{1}\n{8} {0}{9}{1}'),
       'finished': 'Finished!\n\nPress "{0}{2}{1}" to close.'}
# common formatting strings
white = '{color (255, 255, 255, 255)}'
green = '{color (51, 255, 153, 255)}'

# start experiment controller
with ExperimentController(**ec_params) as ec:
    ec.set_visible(False)
    # create the output directory for recorded responses
    resp_dir = op.join('responses', ec.participant)
    makedirs(resp_dir, exist_ok=True)

    # load stimulus list for this listener
    stimuli = design_matrix.loc[design_matrix['listener'] == int(ec.session),
                                ['filename']]
    n_stim = len(stimuli)
    if n_stim != 180:
        raise RuntimeError('{} stimuli loaded (should be 180)'.format(n_stim))

    # run training?
    run_training = get_keyboard_input('Run training [Y/n]?', default='y',
                                      out_type=str, valid=['y', 'Y', 'n', 'N'])
    run_training = run_training in ['y', 'Y']
    if run_training:  # prepend training stimuli
        n_training_stims = training_stimuli.shape[0]
        all_stimuli = pd.concat([training_stimuli, stimuli], ignore_index=True)

    # get starting trial number
    first_trial = get_keyboard_input(msg['first_trial'], default=0,
                                     out_type=int, valid=range(n_stim))

    # experimenter instructions
    ec.set_visible(True)
    fmt = [green, white, live_keys[0], ec._response_handler.force_quit_keys[0]]
    prompt = msg['welcome'].format(*fmt)
    ec.screen_prompt(prompt, live_keys=live_keys, font_size=18, attr=True)
    # put a reminder in the terminal window
    print('Press Ctrl+C when listener has finished responding.')

    # loop over trials
    for ix, stim in all_stimuli.itertuples():
        # are we done with training?
        if run_training and ix == n_training_stims:
            fmt = [green, white, live_keys[0]]
            ec.screen_prompt(msg['end_training'].format(*fmt))

        # break between blocks
        trial_num = ix - n_training_stims if run_training else ix
        if trial_num > 0 and trial_num % block_len == 0:
            block_num = trial_num // block_len
            fmt = [block_num, n_blocks, live_keys[0]]
            ec.screen_prompt(msg['end_block'].format(*fmt))

        # load the wav file
        #wav, fs = read_wav(op.join(stim_dir, stim))
        wav, fs = read_wav(op.join('test-stimuli', 'NWF002_03-10.wav'))
        # TODO: fix previous two lines when done testing
        dur = wav.shape[-1] / fs
        ec.load_buffer(wav)

        # identify trial and save to logfile
        talker, sentence, snr = stim[:6], stim[7:12], stim[13:15]
        trial_id_parts = ['trial:', str(trial_num), 'talker:', talker,
                          'sentence:', sentence, 'SNR:', snr]
        ec.identify_trial(ec_id=' '.join(trial_id_parts), ttl_id=[])

        # show current stim info and play stimulus
        fmt = [green, white] + trial_id_parts
        if trial_num < 0:
            fmt[2] = 'training:'
            fmt[3] = fmt[3] + n_training_stims
        ec.screen_text(msg['now_playing'].format(*fmt))
        ec.start_stimulus()
        # wait a little less than stim duration, to make sure buffer is open
        # when listener starts responding
        ec.wait_secs(dur - 0.1)

        # save the listener response
        ec.set_visible(False)
        tn = 'training' if trial_num < 0 else '{:03}'.format(trial_num)
        resp_file = op.join(resp_dir, '{}_{}.wav'.format(tn, sentence))
        try:
            q = queue.Queue()
            def sd_callback(data_in, frames, time, status):
                if status:
                    print(status, file=sys.stderr)
                q.put(data_in.copy())
            sf_args = dict(mode='x', samplerate=44100, channels=1)
            with sf.SoundFile(resp_file, **sf_args) as sfile:
                with sd.InputStream(callback=sd_callback):
                    while True:
                        sfile.write(q.get())
        except KeyboardInterrupt:
            pass

        # finalize trial and restore experimenter interface
        ec.trial_ok()
        ec.set_visible(True)
    ec.screen_prompt(msg['finished'].format(green, white, live_keys[0]),
                     max_wait=10, live_keys=live_keys)
