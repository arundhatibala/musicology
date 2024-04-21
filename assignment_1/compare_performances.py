from taskA import *


def compare_different_performances(performances_folder_path):
    """
    Compare the timing functions of different performances of the same piece.
    """
    total_multipliers = {}
    for subdir, dirs, files in os.walk(performances_folder_path):
        unperformed_annotation = "midi_score_annotations.txt"
        unperf_lines = open(
            performances_folder_path + "/" + unperformed_annotation, "r"
        ).readlines()
        durations_unperformed = get_durations(unperf_lines)
        for annot_file in files:
            # if it is a performance annotation file
            if annot_file.endswith(".txt") and annot_file != unperformed_annotation:
                perf_lines = open(
                    performances_folder_path + "/" + annot_file, "r"
                ).readlines()
                durations_performed = get_durations(perf_lines)
                # Make sure the number of beats in the performed and unperformed files is the same
                if len(perf_lines) < len(unperf_lines):
                    durations_unperformed = durations_unperformed[: len(perf_lines) - 1]
                elif len(perf_lines) > len(unperf_lines):
                    lines_to_add_to_unperf = len(perf_lines) - len(unperf_lines)
                    avg_duration = get_avg_duration(durations_unperformed)
                    for i in range(lines_to_add_to_unperf):
                        durations_unperformed.append(avg_duration)
                multipliers = get_unperformed_to_performed_multipliers(
                    durations_unperformed, durations_performed
                )

                total_multipliers[annot_file] = {
                    i: multipliers[i] for i in range(len(multipliers))
                }

    # plot total_multupliers
    for annot_file in total_multipliers:
        plt.plot(
            total_multipliers[annot_file].keys(),
            total_multipliers[annot_file].values(),
            label=annot_file,
        )

    plt.ylabel("multiplier")
    plt.xlabel("beat number")
    # set legend text to be the time signature
    plt.legend(title="performance")
    plt.show()


if __name__ == "__main__":
    # use argparse and take performances path as input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "performances_folder_path", help="path to the performances annotations folder"
    )
    args = parser.parse_args()

    # get the subcorpus path folder containing the annotations of the performed and unperformed midi in each subfolder
    performances_folder_path = args.performances_folder_path
    compare_different_performances(performances_folder_path)
