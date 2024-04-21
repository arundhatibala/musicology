import os
import matplotlib.pyplot as plt
import argparse


def get_time_signature(lines):
    """
    Get the time signature from the lines of the file.
    """
    time_signature = None
    for line in lines:
        splits = line.split(",")
        if len(splits) < 2:
            continue
        time_signature = line.split(",")[1]
        if "/" in time_signature:
            return time_signature
    return None


def get_durations(lines):
    """
    Get the durations of the beats from the lines of the file.
    """
    durations = []
    for i in range(len(lines) - 1):
        durations.append(
            float(lines[i + 1].split("\t")[0]) - float(lines[i].split("\t")[0])
        )
    return durations


def get_avg_duration(durations):
    """
    Calculate the average duration of the a list of durations.
    """
    return sum(durations) / len(durations)


def get_unperformed_to_performed_multipliers(
    durations_unperformed, durations_performed
):
    """
    Calculate the multipliers for each beat by dividing the duration of the performed file by the duration of the unperformed file.
    """
    multipliers = []
    for i in range(len(durations_unperformed)):
        mult = durations_performed[i] / durations_unperformed[i]
        multipliers.append(mult)
    return multipliers


def calculate_avg_multiplier(subcorpus_path):
    """
    Calculate the average multiplier for each beat for each time signature.
    Loop through all subfolders and for each subfolder, get the durations of the performed and unperformed files.
    Calculate the multipliers for each beat by dividing the duration of the performed file by the duration of the unperformed file.
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
        if unperformed_annotation not in files:
            continue

        unperformed_file_path = os.path.join(subdir, unperformed_annotation)
        unperf_lines = open(unperformed_file_path, "r").readlines()

        annotation_files = [file for file in files if file.endswith("_annotations.txt")]
        for annotation_file in annotation_files:
            if annotation_file == unperformed_annotation:
                continue
            durations_unperformed = get_durations(unperf_lines)
            performed_file_path = os.path.join(subdir, annotation_file)
            perf_lines = open(performed_file_path, "r").readlines()

            durations_performed = get_durations(perf_lines)

            # Make sure the number of beats in the performed and unperformed files is the same
            if len(perf_lines) < len(unperf_lines):
                durations_unperformed = durations_unperformed[: len(perf_lines) - 1]
            elif len(perf_lines) > len(unperf_lines):
                lines_to_add_to_unperf = len(perf_lines) - len(unperf_lines)
                avg_duration = get_avg_duration(durations_unperformed)
                for i in range(lines_to_add_to_unperf):
                    durations_unperformed.append(avg_duration)

            time_signature = get_time_signature(perf_lines).strip()
            # Initialize the time signature dictionary if it is not present
            if time_signature not in sum_mult_per_time_sig_per_beat:
                sum_mult_per_time_sig_per_beat[time_signature] = {}
                nr_of_mult_per_time_sig_per_beat[time_signature] = {}

            multipliers = get_unperformed_to_performed_multipliers(
                durations_unperformed, durations_performed
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


def plot_timing_function(avg_mult_per_time_sig_per_beat, xlabel="multiplier", ylabel="beat number"):
    """
    For each time signature, plot the average multipliers for each beat,
    with the x-axis being the beat number(i.e the number of keys in the dictionary) and
    the y-axis being the multiplier.
    """
    for time_signature in avg_mult_per_time_sig_per_beat:
        plt.plot(
            avg_mult_per_time_sig_per_beat[time_signature].keys(),
            avg_mult_per_time_sig_per_beat[time_signature].values(),
            label=time_signature,
        )

    plt.ylabel(xlabel)
    plt.xlabel(ylabel)
    # set legend text to be the time signature
    plt.legend(title="time signature")
    plt.show()


if __name__ == "__main__":
    # use argparse and take subcorpus path as input
    parser = argparse.ArgumentParser()
    parser.add_argument("subcorpus_path", help="path to the subcorpus")
    args = parser.parse_args()

    # get the subcorpus path folder containing the annotations of the performed and unperformed midi in each subfolder
    subcorpus_path = args.subcorpus_path

    avg_mult_per_time_sig_per_beat = calculate_avg_multiplier(subcorpus_path)
    plot_timing_function(avg_mult_per_time_sig_per_beat)