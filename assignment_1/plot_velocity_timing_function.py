from taskA import (
    plot_timing_function,
    get_time_signature,
    get_unperformed_to_performed_multipliers,
)
import mido
import os
import matplotlib.pyplot as plt
import argparse


def get_velocities(midi_file_path):
    mid = mido.MidiFile(midi_file_path)
    velocities = []

    for track in mid.tracks:
        for msg in track:
            if msg.type == "note_on" and msg.velocity != 0:
                velocities.append(msg.velocity)

    return velocities


def get_avg_velocity(velocities):
    return sum(velocities) / len(velocities)


def calculate_avg_multiplier(subcorpus_path):
    """
    Calculate the average multiplier for each beat for each time signature.
    Loop through all subfolders and for each subfolder, get the velocities of the performed and unperformed files.
    Calculate the multipliers for each beat by dividing the velocity of the performed file by the velocity of the unperformed file.
    Update the sum and number of multipliers for each time signature and beat.
    Return the average multiplier for each time signature and beat.
    """
    # for each time signature, for each beat,
    # calculate the average multiplier by dividing the sum of the multipliers by the number of multipliers
    sum_mult_per_time_sig_per_beat = {}
    nr_of_mult_per_time_sig_per_beat = {}
    avg_mult_per_time_sig_per_beat = {}

    # go through all subfolders
    for subdir, dirs, files in os.walk(subcorpus_path):
        unperformed_annotation = "midi_score_annotations.txt"
        unperformed_midi = "midi_score.mid"
        if unperformed_annotation not in files:
            continue

        unperformed_file_path = os.path.join(subdir, unperformed_midi)

        unperformed_annotation_file_path = os.path.join(subdir, unperformed_annotation)
        unperf_lines = open(unperformed_annotation_file_path, "r").readlines()
        time_signature = get_time_signature(unperf_lines).strip()

        midi_files = [file for file in files if file.endswith(".mid")]
        for midi_file in midi_files:
            if midi_file == unperformed_midi:
                continue
            velocities_unperformed = get_velocities(unperformed_file_path)

            performed_file_path = os.path.join(subdir, midi_file)
            velocities_perfomed = get_velocities(performed_file_path)

            # Make sure the number of beats in the performed and unperformed files is the same
            if len(velocities_perfomed) < len(velocities_unperformed):
                velocities_unperformed = velocities_unperformed[
                    : len(velocities_perfomed) - 1
                ]
            elif len(velocities_perfomed) > len(velocities_unperformed):
                lines_to_add_to_unperf = len(velocities_perfomed) - len(
                    velocities_unperformed
                )
                avg_velocity = get_avg_velocity(velocities_unperformed)
                for i in range(lines_to_add_to_unperf):
                    velocities_unperformed.append(avg_velocity)

            # Initialize the time signature dictionary if it is not present
            if time_signature not in sum_mult_per_time_sig_per_beat:
                sum_mult_per_time_sig_per_beat[time_signature] = {}
                nr_of_mult_per_time_sig_per_beat[time_signature] = {}

            multipliers = get_unperformed_to_performed_multipliers(
                velocities_unperformed, velocities_perfomed
            )

            # Update the sum and number of multipliers for each time signature and beat
            for beat, mult in enumerate(multipliers):
                if beat not in sum_mult_per_time_sig_per_beat[time_signature]:
                    sum_mult_per_time_sig_per_beat[time_signature][beat] = mult
                    nr_of_mult_per_time_sig_per_beat[time_signature][beat] = 1
                sum_mult_per_time_sig_per_beat[time_signature][beat] += mult
                nr_of_mult_per_time_sig_per_beat[time_signature][beat] += 1

    # Calculate the average multiplier for each time signature and beat
    for time_signature in sum_mult_per_time_sig_per_beat:
        avg_mult_per_time_sig_per_beat[time_signature] = {}
        for beat in sum_mult_per_time_sig_per_beat[time_signature]:
            avg_mult_per_time_sig_per_beat[time_signature][beat] = (
                sum_mult_per_time_sig_per_beat[time_signature][beat]
                / nr_of_mult_per_time_sig_per_beat[time_signature][beat]
            )

    return avg_mult_per_time_sig_per_beat


if __name__ == "__main__":
    # use argparse and take subcorpus path as input
    parser = argparse.ArgumentParser()
    parser.add_argument("subcorpus_path", help="path to the subcorpus")
    args = parser.parse_args()

    # get the subcorpus path folder containing the annotations of the performed and unperformed midi in each subfolder
    subcorpus_path = args.subcorpus_path

    avg_mult_per_time_sig_per_beat = calculate_avg_multiplier(subcorpus_path)

    plot_timing_function(avg_mult_per_time_sig_per_beat, ylabel="note number")
