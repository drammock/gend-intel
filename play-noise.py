#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Script 'play-noise.py'
===============================================================================

This script plays noise for headphone calibration purposes.
"""
# @author: drmccloy
# Created on Tue Jul 25 14:35:40 PDT 2017
# License: BSD (3-clause)

import os.path as op
import numpy as np
import sounddevice as sd
import soundfile as sf
from expyfun import ExperimentController, get_keyboard_input
from expyfun.stimuli import read_wav


# load noise file
noise, fs = read_wav('whitenoise_16bit_44100Hz_70dB.wav')
dur = noise.shape[-1] / fs

ec_params = dict(exp_name='test-noise', participant='noise', session=0,
                 audio_controller='pyglet', response_device='keyboard',
                 stim_fs=44100, stim_rms=0.01, check_rms=None, output_dir=None,
                 force_quit=['q'], full_screen=False, window_size=(800, 600),
                 version='dev')

with ExperimentController(**ec_params) as ec:
    quit_key = ec._response_handler.force_quit_keys[0]
    ec.screen_text('press "{}" to quit'.format(quit_key))
    ec.load_buffer(noise)
    ec.identify_trial(ec_id='noise', ttl_id=[])
    ec.start_stimulus()
    ec.wait_secs(dur)
    ec.trial_ok()
