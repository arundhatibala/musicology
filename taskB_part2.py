from taskA import *


def plot_expressive_timing_function(
    avg_mult_per_time_sig_per_beat, time_signature, beat_modulo
):
    """
    Take the average multipliers for each beat for a specific time signature and plot the expressive timing function.
    Modularize each beat number by the beat modulo and calculate the average multiplier.
    Plot the expressive timing function with the x-axis being the beat number and the y-axis being the multiplier.
    """
    expressive_timing_multipliers_sum = {i: 0 for i in range(beat_modulo)}
    expressive_timing_multipliers_len = {i: 0 for i in range(beat_modulo)}
    expressive_timing_multipliers = {i: 0 for i in range(beat_modulo)}
    for beat_nr in avg_mult_per_time_sig_per_beat[time_signature]:
        modularized_beat = beat_nr % beat_modulo
        expressive_timing_multipliers_sum[
            modularized_beat
        ] += avg_mult_per_time_sig_per_beat[time_signature][beat_nr]
        expressive_timing_multipliers_len[modularized_beat] += 1

    for beat_nr in expressive_timing_multipliers_sum:
        expressive_timing_multipliers[beat_nr] = (
            expressive_timing_multipliers_sum[beat_nr]
            / expressive_timing_multipliers_len[beat_nr]
        )

    # plot the expressive timing multipliers
    plt.plot(
        expressive_timing_multipliers.keys(),
        expressive_timing_multipliers.values(),
        label=time_signature,
    )
    plt.ylabel("multiplier")
    plt.xlabel("beat number")
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

    plot_expressive_timing_function(avg_mult_per_time_sig_per_beat, "4/4", 5)
    plot_expressive_timing_function(avg_mult_per_time_sig_per_beat, "3/4", 4)
