#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Script 'counterbalance-trials.py'
===============================================================================

This script counterbalances trial parameters.
"""
# @author: drmccloy
# Created on Thu Jun 15 13:38:22 2017
# License: BSD (3-clause)

import sys
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

# sounddevice setup
sd.default.channels = 1
sd.default.samplerate = 44100

# experiment setup
stim_dir = 'stimuli'
live_keys = ['space']
stimuli = glob(op.join(stim_dir, '*.wav'))
design_matrix = pd.read_csv('design-matrix.csv', header=0)
ec_params = dict(exp_name='gend-intel', audio_controller='pyglet',
                 response_device='keyboard', stim_fs=44100, stim_rms=0.01,
                 check_rms=None, output_dir='logs', force_quit=['q'],
                 full_screen=False, window_size=(800, 600), version='dev')

# start experiment controller
with ExperimentController(**ec_params) as ec:
    ec.set_visible(False)
    # create the output directory for recorded responses
    resp_dir = op.join('responses', ec.participant)
    makedirs(resp_dir, exist_ok=True)
    # load stimulus list for this listener
    stimuli = design_matrix.loc[design_matrix['listener'] == int(ec.session),
                                'filename']
    n_stim = len(stimuli)
    if n_stim != 180:
        raise RuntimeError('{} stimuli loaded (should be 180)'.format(n_stim))

    # get starting trial number
    prompt = ('Start at which trial? (leave blank and push ENTER to start at '
              'beginning): ')
    first_trial = get_keyboard_input(prompt, default=0, out_type=int,
                                     valid=range(n_stim))
    ec.set_visible(True)
    # TODO: add training block.
    # instructions
    welcome = ('Press "{0}{2}{1}" to start the first trial. Press "{0}{3}{1}" '
               'any time this window is visible to quit the experiment. '
               'Listener responses will start recording automatically; press '
               '{0}Ctrl+C{1} to stop recording and advance to the next trial '
               '(for recording to work, this window must disappear during the '
               'response so the terminal can catch the Ctrl+C keystroke).'
               ''.format('{color (51, 255, 153, 255)}',
                         '{color (255, 255, 255, 255)}', live_keys[0],
                         ec._response_handler.force_quit_keys[0]))
    ec.screen_prompt(welcome, live_keys=live_keys, font_size=16, attr=True)
    # TODO: remove next line!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    stimuli = stimuli[:3]
    print('Press Ctrl+C when listener has finished responding.')
    # loop over trials
    for ix, stim in enumerate(stimuli):
        # TODO: split into blocks using ix %% blocksize
        # load the wav file
        #wav, fs = read_wav(op.join(stim_dir, stim))
        wav, fs = read_wav(op.join('test-stimuli', 'NWF002_03-10.wav'))
        dur = wav.shape[-1] / fs
        ec.load_buffer(wav)
        # identify trial and save to logfile
        talker, sentence, snr = stim[:6], stim[7:12], stim[14:16]
        trial_id = ' '.join(['trial', str(ix), 'talker', talker,
                             'sentence', sentence, 'snr', snr])
        ec.identify_trial(ec_id=trial_id, ttl_id=[])
        # show current stim info and play stimulus
        message = 'now playing {}\n\n'.format(trial_id)
        ec.screen_text(message, color='gray')
        ec.flip()
        ec.start_stimulus()
        ec.wait_secs(dur)
        # save the listener response
        ec.set_visible(False)
        resp_file = op.join(resp_dir, '{:03}_{}.wav'.format(ix, sentence))
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
        ec.trial_ok()
        ec.set_visible(True)
    ec.screen_prompt('finished! press "{}" to close.'.format(live_keys[0]),
                     max_wait=10, live_keys=live_keys)
