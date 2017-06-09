# gend-intel

These are scripts related to a speech-in-noise intelligibility experiment
conducted at the University of Washington.

## Stimuli

The stimuli are recordings of (a subset of) the
[IEEE sentences](https://en.wikipedia.org/wiki/Harvard_sentences). There are 30
talkers, 180 sentences (out of the original 720), and 6 different presentation
SNRs; each of these parameters is stored in `params.yaml`. The noise is white
noise filtered to match the long-term average spectrum of the stimuli. The
particular combination of talker, sentence, and SNR on any given trial are
determined by the script `counterbalance-trials.py`, which writes the
combinations to `design-matrix.csv`.
