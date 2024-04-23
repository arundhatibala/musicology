import pretty_midi
import random
import argparse


# Constants
SILENCE_DURATION = 0.15
VELOCITY_VARIATION = 5
MAX_VELOCITY = 127
STANDARD_DURATION = (
    0.25  # the duration of a midi note which is not extended nor shortened
)
STACCATO_MULTIPLIER = 0.75
SHORTENED_STACCATO_MULTIPLIER = 0.4
STACCATO_DURATION = 0.05
BREATH_START_MULTIPLIER = 0.1
BREATH_VELOCITY_MULTIPLIER = 0.4


def get_next_notes(note_idx, notes):
    """Return the indexes of the next notes that start after the current note.

    Args:
        note_idx: The index of the current note.
        notes: The list of notes.
    """
    curr_note = notes[note_idx]
    next_notes = []
    next_note_start = None

    # There can be more than one note with the same start time since they can be played together
    for next_node_idx in range(note_idx + 1, len(notes)):
        curr_next_note_start = notes[next_node_idx].start
        if curr_next_note_start > curr_note.start:
            if next_note_start is None:
                next_note_start = curr_next_note_start
            elif curr_next_note_start > next_note_start:
                break
            next_notes.append(next_node_idx)

    return next_notes


def get_previous_notes(note_idx, notes):
    """Return the indexes of the previous notes that end before the current note.

    Args:
        note_idx: The index of the current note.
        notes: The list of notes.
    """
    curr_note = notes[note_idx]
    previous_notes = []
    previous_note_end = None

    # There can be more than one note with the same end time since they can be played together
    for previous_note_idx in range(note_idx - 1, -1, -1):
        curr_previous_note_end = notes[previous_note_idx].end
        if curr_previous_note_end < curr_note.start:
            if previous_note_end is None:
                previous_note_end = curr_previous_note_end
            elif curr_previous_note_end < previous_note_end:
                break
            previous_notes.append(previous_note_idx)

    return previous_notes


def get_notes_playing_together(curr_note, notes):
    """Return the indexes of the notes that are played together with the current note.

    Args:
        curr_note: The current note.
        notes: The list of notes.
    """
    together_notes = []

    for other_note_idx, other_note in enumerate(notes):
        if (
            other_note.pitch != curr_note.pitch
            and other_note.start == curr_note.start
            and other_note.end == curr_note.end
        ):
            together_notes.append(other_note_idx)
        if other_note.start > curr_note.end:
            break
    return together_notes


def get_notes_with_same_start_smaller_end(curr_note, notes):
    """Return the indexes of the notes that start at the same time as the current note and end before the current note.

    Args:
        curr_note: The current note.
        notes: The list of notes.
    """
    same_start_smaller_end_notes = []

    for other_note_idx, other_note in enumerate(notes):
        if (
            other_note.pitch != curr_note.pitch
            and other_note.start == curr_note.start
            and other_note.end < curr_note.end
        ):
            same_start_smaller_end_notes.append(other_note_idx)
        if other_note.start > curr_note.end:
            break
    return same_start_smaller_end_notes


def is_nearby_note_repeated(note_idx, nearby_notes, notes):
    """Return True if some nearby note has the same pitch as the current note, False otherwise.

    Args:
        note_idx: The index of the current note.
        nearby_notes: The indexes of the next notes.
        notes: The list of notes.
    """
    curr_note = notes[note_idx]

    for next_note_idx in nearby_notes:
        if notes[next_note_idx].pitch == curr_note.pitch:
            return True

    return False


def apply_staccato_effect(note, multiplier=STACCATO_MULTIPLIER):
    """Apply the staccato effect to the note.

    Args:
        note: The note to which the staccato effect is applied.
    """
    note.end = note.end - multiplier * (note.end - note.start)
    return note


def add_staccato_to_repeated_notes(notes):
    """Iterate through the notes and apply the staccato effect to the repeated notes.

    Args:
        notes: The list of notes.
    """
    velocity_increase = VELOCITY_VARIATION
    for curr_note_idx, curr_note in enumerate(notes):
        next_notes = get_next_notes(curr_note_idx, notes)
        if is_nearby_note_repeated(curr_note_idx, next_notes, notes):
            if not is_shortened(curr_note):
                curr_note = apply_staccato_effect(curr_note)
                curr_note.velocity = min(
                    MAX_VELOCITY, curr_note.velocity + velocity_increase
                )
                velocity_increase += VELOCITY_VARIATION
                notes[curr_note_idx] = curr_note
        else:
            previous_notes = get_previous_notes(curr_note_idx, notes)
            if is_nearby_note_repeated(
                curr_note_idx, previous_notes, notes
            ) and not is_shortened(curr_note):
                curr_note = apply_staccato_effect(curr_note)
                curr_note.velocity = min(
                    MAX_VELOCITY, curr_note.velocity + velocity_increase
                )
                notes[curr_note_idx] = curr_note
            velocity_increase = VELOCITY_VARIATION


def get_avg_velocity(notes):
    """Return the average velocity of the notes.

    Args:
        notes: The list of notes.
    """
    velocity_sum = 0
    for note in notes:
        velocity_sum += note.velocity
    return velocity_sum // len(notes)


def normalize_velocity(velocity, notes):
    """Normalize the velocity of the notes.

    Args:
        velocity: The velocity to which the notes are normalized.
        notes: The list of notes.
    """
    for note in notes:
        note.velocity = velocity


def is_standard_duration(note):
    """Return True if the note has a standard duration, False otherwise.

    Args:
        note: The note to check.
    """
    note_duration = note.end - note.start
    threshold = 0.01
    return abs(note_duration - STANDARD_DURATION) < threshold


def is_extended(note):
    """Return True if the note is extended, False otherwise.

    Args:
        note: The note to check.
    """
    note_duration = note.end - note.start
    threshold = 0.05
    return note_duration > STANDARD_DURATION + threshold


def is_shortened(note):
    """Return True if the note is shortened, False otherwise.

    Args:
        note: The note to check.
    """
    note_duration = note.end - note.start
    threshold = 0.05
    return note_duration < STANDARD_DURATION - threshold


def staccato_before_next_note(curr_note_idx, notes):
    """Return True if there is a staccato before the next note, False otherwise.

    Args:
        curr_note_idx: The index of the current note.
        notes: The list of notes.
    """
    next_notes = get_next_notes(curr_note_idx, notes)
    if len(next_notes) == 0:
        return False
    next_note_start = notes[next_notes[0]].start
    curr_note = notes[curr_note_idx]
    return next_note_start - curr_note.end > STACCATO_DURATION


def add_staccato_to_melody(notes):
    """Iterate through the notes and apply the staccato effect to the melody notes.
    If the note is of standard duration, apply the general staccato effect.
    If the note is shortened, apply the staccato effect with a smaller multiplier.

    Args:
        notes: The list of notes.
    """
    for curr_note_idx, curr_note in enumerate(notes):
        # Apply staccato effect only if there is not already a staccato before the next note
        if staccato_before_next_note(curr_note_idx, notes):
            continue

        if is_standard_duration(curr_note):
            curr_note = apply_staccato_effect(curr_note)
            notes[curr_note_idx] = curr_note
        elif is_shortened(curr_note):
            curr_note = apply_staccato_effect(curr_note, SHORTENED_STACCATO_MULTIPLIER)
            notes[curr_note_idx] = curr_note


def add_general_randomization_on_velocity(notes):
    """Iterate through the notes and add a general randomization on velocity.

    Args:
        notes: The list of notes.
    """
    for note in notes:
        velocity_variation = random.randint(-VELOCITY_VARIATION, VELOCITY_VARIATION)
        note.velocity = min(MAX_VELOCITY, note.velocity + velocity_variation)


def get_concurrent_notes(curr_note, notes):
    """Return the indexes of the notes that are played together with the current note.

    Args:
        curr_note: The current note.
        notes: The list of notes.
    """
    concurrent_notes = []

    for other_note_idx, other_note in enumerate(notes):
        # do not consider notes that are played at the same time as concurrent
        if other_note.start == curr_note.start:
            continue
        if other_note.start <= curr_note.end and other_note.end >= curr_note.start:
            concurrent_notes.append(other_note_idx)
        if other_note.start > curr_note.end:
            break
    return concurrent_notes


def apply_breath_effect(note, multiplier=BREATH_START_MULTIPLIER):
    """Apply the breath effect to the note.

    Args:
        note: The note to which the breath effect is applied.
        multiplier: The multiplier for the start delay.
    """
    start_delay = multiplier * (note.end - note.start)
    note.start += start_delay
    note.velocity = max(
        5, round(note.velocity - BREATH_VELOCITY_MULTIPLIER * note.velocity)
    )
    return start_delay


def apply_delay(note, delay):
    """Apply the delay to the note.

    Args:
        note: The note to which the delay is applied.
        delay: The delay to apply.
    """
    note.start += delay
    note.end += delay
    note.velocity = max(
        5, round(note.velocity - BREATH_VELOCITY_MULTIPLIER * note.velocity)
    )


def adjust_notes_followed_by_silence(melody_notes, bass_notes):
    """Iterate through the notes and extend the notes that are followed by silence, if not already extended.
    Additionally, delay the start and decrease the velocity to add a sense of breath.

    Args:
        melody_notes: The list of melody notes.
        bass_notes: The list of bass notes.
    """
    breath_effect_indexes = []
    for curr_note_idx, curr_note in enumerate(melody_notes):
        if curr_note_idx in breath_effect_indexes:
            continue
        next_notes = get_next_notes(curr_note_idx, melody_notes)

        if len(next_notes) > 0:
            next_note_start = melody_notes[next_notes[0]].start

            if (
                next_note_start - curr_note.start > SILENCE_DURATION
                and is_extended(curr_note)
                and len(get_concurrent_notes(curr_note, melody_notes)) == 0
                and len(get_concurrent_notes(curr_note, bass_notes)) == 0
            ):
                melody_notes_played_together = get_notes_playing_together(
                    curr_note, melody_notes
                )
                start_delay = None
                for note_idx in melody_notes_played_together:
                    note = melody_notes[note_idx]
                    start_delay = apply_breath_effect(note)
                    melody_notes[note_idx] = note
                    breath_effect_indexes.append(note_idx)

                bass_notes_played_together = get_notes_playing_together(
                    curr_note, bass_notes
                )
                for note_idx in bass_notes_played_together:
                    note = bass_notes[note_idx]
                    start_delay = apply_breath_effect(note)
                    bass_notes[note_idx] = note

                if (
                    len(melody_notes_played_together) > 0
                    or len(bass_notes_played_together) > 0
                ):
                    same_start_notes_melody = get_notes_with_same_start_smaller_end(
                        curr_note, melody_notes
                    )
                    for note_idx in same_start_notes_melody:
                        note = melody_notes[note_idx]
                        apply_delay(note, start_delay)
                        melody_notes[note_idx] = note
                        breath_effect_indexes.append(note_idx)

                    same_start_notes_bass = get_notes_with_same_start_smaller_end(
                        curr_note, bass_notes
                    )
                    for note_idx in same_start_notes_bass:
                        note = bass_notes[note_idx]
                        apply_delay(note, start_delay)
                        bass_notes[note_idx] = note

                apply_breath_effect(curr_note)
                melody_notes[curr_note_idx] = curr_note
                breath_effect_indexes.append(curr_note_idx)


def main(input_midi_file, output_midi_file):
    # Load the input MIDI file representing the unperformed version
    piano = pretty_midi.PrettyMIDI(input_midi_file)

    right_hand_melody = list(piano.instruments)[0]
    left_hand_bass = list(piano.instruments)[1]

    # Normalize volume of left hand to be lower than right hand
    normalize_velocity(
        get_avg_velocity(right_hand_melody.notes) - 20, left_hand_bass.notes
    )

    add_staccato_to_repeated_notes(left_hand_bass.notes)

    add_staccato_to_melody(right_hand_melody.notes)

    add_general_randomization_on_velocity(right_hand_melody.notes)

    adjust_notes_followed_by_silence(right_hand_melody.notes, left_hand_bass.notes)

    add_staccato_to_repeated_notes(right_hand_melody.notes)

    # Update the instruments
    piano.instruments[0] = right_hand_melody
    piano.instruments[1] = left_hand_bass

    # Save the new MIDI file
    piano.write(output_midi_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_midi_file", help="The input MIDI file")
    parser.add_argument("output_midi_file", help="The output MIDI file")
    args = parser.parse_args()

    input_midi_file = args.input_midi_file
    output_midi_file = args.output_midi_file

    main(input_midi_file, output_midi_file)
