# -*- coding: utf-8 -*-
"""Untitled4.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jTTm8ya94ar9aoCji0KwRyhK5ahTcJcE
"""

# !pip install numpy pandas seaborn music21 iteration_utilities
# !pip install git+https://github.com/quadrismegistus/prosodic.git
# !apt install musescore3

import music21
import os
import pandas as pd

# Pull in the score and listen to it a bit
sample_score_tmp = music21.converter.parse(f'/content/2_4_xml_score.musicxml')
sample_score_tmp.show()

# helper functions

def helpers_simplify_score_for_rhythm_analysis(sample_score_tmp):

    # remove chord charts, metronome mark, dynamics
    for part in sample_score_tmp.parts:
        for measure in part.getElementsByClass('Measure'):
            for event in measure:
                if isinstance(event, music21.harmony.ChordSymbol):
                    measure.remove(event)
                if isinstance(event, music21.tempo.MetronomeMark):
                    measure.remove(event)
                if isinstance(event, music21.dynamics.Dynamic):
                    measure.remove(event)
                if isinstance(event, music21.key.KeySignature):
                    measure.remove(event)

    # combine voice tracks intra-staff (done by extracted staffs and recombining)
    chordified_treble = sample_score_tmp.parts[0].chordify()
    chordified_bass = sample_score_tmp.parts[1].chordify()
    sample_score = music21.stream.Score()
    sample_score.insert(0, chordified_treble)
    sample_score.insert(0, chordified_bass)

    # cast all single-note chord objects (created by chordify) as note objects so students see more typical music21 score object structure
    staff_count = 0
    for part in sample_score.parts:
        staff_count += 1
        for measure in part.getElementsByClass('Measure'):
            for event in measure:
                if isinstance(event, music21.chord.Chord): # and len(event.notes) == 1:
                    note_version = music21.note.Note()
                    if staff_count == 1:
                        note_version.pitch = music21.pitch.Pitch('C4')
                    elif staff_count == 2:
                        note_version.pitch = music21.pitch.Pitch('C3')
                    note_version.duration = event.duration
                    start_found = 0
                    continue_found = 0
                    none_found = 0
                    all_ties_stop = 1
                    for nte in event.notes:
                        try:
                            curr_tie_obj = nte.tie.type
                        except:
                            curr_tie_obj = None
                        if (curr_tie_obj == 'start'):
                            start_found = 1
                        if (curr_tie_obj == 'continue'):
                            continue_found = 1
                        if (curr_tie_obj is None):
                            none_found = 1
                        if (curr_tie_obj != 'stop'):
                            all_ties_stop = 0
                    if start_found == 1:
                        note_version.tie = music21.tie.Tie('start')
                    elif none_found == 1:
                        note_version.tie = None
                    elif all_ties_stop == 1:
                        note_version.tie = music21.tie.Tie('stop')
                    elif continue_found == 1:
                        note_version.tie = music21.tie.Tie('continue')
                    note_version.offset = event.offset
                    note_version.articulations = event.articulations
                    note_version.expressions = event.expressions
                    measure.replace(event, note_version)

    # fix instances where tie start leads to tie None (should be no tie but previous loop isn't built to observe two consecutive elements)
    # the ties are a pain >:"{
    for part in sample_score.parts:
        for measure in part.getElementsByClass('Measure'):
            for i in range(len(measure)-1):
                curr_event = measure[i]
                next_event = measure[i+1]
                if isinstance(curr_event, music21.note.Note) and isinstance(next_event, music21.note.Note):
                    try:
                        curr_tie = curr_event.tie.type
                    except:
                        curr_tie = None
                    try:
                        next_tie = next_event.tie.type
                    except:
                        next_tie = None
                    if (curr_tie == 'start' or curr_tie == 'continue') and (next_tie == 'start' or next_tie is None):
                        measure[i].tie = music21.tie.Tie('stop')
                if isinstance(curr_event, music21.note.Rest):
                    measure[i].tie = None

    # combine tied notes intra-staff
    for part in sample_score.parts:
        active_tie = 0
        for measure in part.getElementsByClass('Measure'):
            for i in range(len(measure)):
                if isinstance(measure[i], music21.note.Note):
                    if measure[i].tie is not None:
                        if measure[i].tie.type == "start":
                            active_tie = 1
                        elif measure[i].tie.type == "stop" and active_tie == 1:
                            active_tie = 0
                        elif measure[i].tie.type == "stop" and active_tie == 0:
                            measure[i].tie = None

    treble = sample_score.parts[0]
    for measure in treble.getElementsByClass('Measure'):
        i = 0
        len_measure = len(measure)
        while i < len_measure-1:
            if isinstance(measure[i], music21.note.Note) and isinstance(measure[i+1], music21.note.Note):
                if measure[i].tie is not None and measure[i+1].tie is not None:
                    measure[i].duration = music21.duration.Duration(measure[i].duration.quarterLength + measure[i+1].duration.quarterLength)
                    if measure[i+1].tie is not None:
                        if measure[i+1].tie.type == "stop":
                            measure[i].tie = None
                    measure.remove(measure[i+1])
            i += 1
            len_measure = len(measure)

    bass = sample_score.parts[1]
    for measure in bass.getElementsByClass('Measure'):
        i = 0
        len_measure = len(measure)
        while i < len_measure-1:
            if isinstance(measure[i], music21.note.Note) and isinstance(measure[i+1], music21.note.Note):
                if measure[i].tie is not None and measure[i+1].tie is not None:
                    measure[i].duration = music21.duration.Duration(measure[i].duration.quarterLength + measure[i+1].duration.quarterLength)
                    if measure[i+1].tie is not None:
                        if measure[i+1].tie.type == "stop":
                            measure[i].tie = None
                    measure.remove(measure[i+1])
            i += 1
            len_measure = len(measure)

    sample_score = music21.stream.Score()
    sample_score.insert(0, treble)
    sample_score.insert(0, bass)

    # deciding against repeat expands for now due to issues with measure number

    return sample_score

import sys
sys.path.append("dependencies")

# Strip out unnecessary elements
sample_score = helpers_simplify_score_for_rhythm_analysis(sample_score_tmp)
sample_score.show()

import music21
print("Data rows will be of the form:\n<type> <onset_in_measure> <duration> <tie> \n")
print("Time Signature: " + sample_score.flat.getElementsByClass('TimeSignature')[0].ratioString + "\n")

for staff in sample_score.parts:
    staff_name = staff.elements[1].clef.name
    for measure in staff.getElementsByClass('Measure'):
        if measure.measureNumber <= 2 and measure.measureNumber > 0:
            print(staff_name + " measure " + str(measure.measureNumber))
            for event in measure.recurse():
                label = ""
                if isinstance(event, music21.note.Note):
                    label = "sounded"
                if isinstance(event, music21.note.Rest):
                    label = "unsounded"
                try:
                    tie_info = "tie_" + event.tie.type
                except:
                    tie_info = ""
                if label != "":
                    print(label, event.offset, event.duration.quarterLength, tie_info)
    print("")

import pandas as pd

## STUDENT SECTION - ##
rhythm_data_list = []
for clef in sample_score.parts:
    global_onset = 0
    clef_name = clef.elements[1].clef.name
    for measure in clef.getElementsByClass('Measure'):
        for event in measure.recurse():
            label = ""
            if isinstance(event, music21.note.Note):
                label = "sounded"
            if isinstance(event, music21.note.Rest):
                label = "unsounded"
            try:
                tie_info = "tie_" + event.tie.type
            except:
                tie_info = ""
            if label != "":
                global_onset = ((measure.measureNumber-1) * 4) + event.offset
                rhythm_data_list.append((clef_name, measure.measureNumber, label, event.offset, global_onset, event.duration.quarterLength, tie_info))
rhythm_data_df = pd.DataFrame(rhythm_data_list, columns=['staff', 'measure_number', 'event_type', 'onset_in_measure', 'onset_in_score', 'duration', 'tie_info'])
## END STUDENT SECTION ##

# Check output with reference photo
pd.concat([rhythm_data_df.head(11), rhythm_data_df.tail(4)], axis = 0)

# helper functions
import matplotlib.pyplot as plt

def helpers_onset_dist(onsets, measure_count = 4):

    if type(onsets) is not list:
        onsets = onsets.tolist()

    beat_locations = [i * 0.5 for i in range(10 * measure_count + 1)]
    beat_frequencies = []
    for loc in beat_locations:
        beat_frequencies.append((onsets.count(loc) / len(onsets)))

    fig, ax = plt.subplots()
    ax.plot(beat_locations, beat_frequencies, color='blue')
    if measure_count == 4:
        ax.set_xlabel('Onset in Measure')
    if measure_count == 8:
        ax.set_xlabel('Onset in Two-Measure Sequence')
        ax.axvline(4, linestyle = '--')
    ax.set_ylabel('')
    ax.set_title('Relative Frequency of Onset Locations')
    ax.set_xlim(0, measure_count)
    ax.set_ylim(0, .5)

subset = rhythm_data_df[rhythm_data_df['staff'] == 'bass']

def extract_onset_in_measure(subset):
    ## STUDENT SECTION -  ##
    return subset[(subset['event_type'] == "sounded") & (subset['tie_info'] != "tie_stop")]['onset_in_measure']
    ## END STUDENT SECTION ##

onsets_bass = extract_onset_in_measure(subset)
helpers_onset_dist(onsets_bass, 4) # graphing function

# helper function

def helpers_onset_dist_overlap_measure_pair(onsets):

    if type(onsets) is not list:
        onsets = onsets.tolist()

    beat_locations = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]

    m1_onsets = [o for o in onsets if o < 4]
    m2_onsets = [o-4 for o in onsets if o >= 4]

    m1_frequencies = []
    m2_frequencies = []
    for loc in beat_locations:
        m1_frequencies.append((m1_onsets.count(loc) / len(onsets)))
        m2_frequencies.append((m2_onsets.count(loc) / len(onsets)))

    fig, ax = plt.subplots()
    ax.plot(beat_locations, m1_frequencies, color='blue')
    ax.plot(beat_locations, m2_frequencies, color='red')
    ax.set_xlabel('Onset in Measure')
    ax.set_ylabel('')
    ax.set_title('Relative Frequency of Onset Locations')
    ax.set_xlim(0, 4)
    ax.set_ylim(0, .5)
    ax.legend(["Odd Measure", "Even Measure"])

sample_score.parts[0].show()