import music21
import pretty_midi
import argparse
import os


# Constants
SILENCE_DURATION = 0.3
STANDARD_DURATION = (
    0.25  # the duration of a midi note which is not extended nor shortened
)
VELOCITY_THRESHOLD = 0.5
NR_NOTES_FOR_VELOCITY_CHECK = 5

phrases = []  # list of list of notes composing each phrase
key = None
tonic_chord_pitches = []
dominant_chord_pitches = []
trills = []


def get_next_notes(note_idx, notes):
    """Return the indexes of the next notes that start after the current note.

    Args:
        note_idx: The index of the current note.
        notes: The list of notes.
    """
    curr_note = notes[note_idx]
    next_notes = []
    next_note_found = False

    curr_concurrent_notes = get_concurrent_notes_idx(curr_note, notes)

    # There can be more than one note with the same start time since they can be played together
    for next_node_idx in range(note_idx + 1, len(notes)):
        if next_note_found:
            break
        if next_node_idx in curr_concurrent_notes:
            continue
        next_note_start = notes[next_node_idx].start
        if next_note_start > curr_note.end:
            next_note_found = True
            next_notes.append(next_node_idx)
    if len(next_notes) > 0:
        next_concurrent_notes = get_concurrent_notes_idx(notes[next_notes[0]], notes)
        next_notes.extend(next_concurrent_notes)
        next_notes = list(set(next_notes))  # remove duplicates
    return next_notes


def is_extended(note):
    """Return True if the note is extended, False otherwise.

    Args:
        note: The note to check.
    """
    note_duration = note.end - note.start
    threshold = 0.05
    return note_duration > STANDARD_DURATION + threshold


def sudden_velocity_change(curr_note_idx, next_notes_idx, notes):
    """Return True if there is a sudden velocity change between the current note and the next notes, False otherwise.

    Args:
        curr_note_idx: The index of the current note.
        next_notes_idx: The indexes of the next notes.
        notes: The list of notes.
    """
    notes_currently_playing = get_notes_currently_playing(curr_note_idx, notes)
    next_notes = [notes[note_idx] for note_idx in next_notes_idx]
    curr_velocities = [[note.velocity for note in notes_currently_playing]]
    next_velocities = [[note.velocity for note in next_notes]]

    i = 0
    velocity_check_cnt = 0
    while velocity_check_cnt < NR_NOTES_FOR_VELOCITY_CHECK:
        if curr_note_idx - i < 0:
            break
        prev_notes = get_notes_currently_playing(curr_note_idx - i, notes)
        # if any of the previous notes is in the current notes, continue
        if any([note in notes_currently_playing for note in prev_notes]):
            i += 1
            continue

        curr_velocities.append([note.velocity for note in prev_notes])
        i += 1
        velocity_check_cnt += 1

    i = 0
    velocity_check_cnt = 0
    next_notes_last_idx = max(next_notes_idx)
    while velocity_check_cnt < NR_NOTES_FOR_VELOCITY_CHECK:
        if next_notes_last_idx + i >= len(notes):
            break
        next_next_notes = get_notes_currently_playing(next_notes_last_idx + i, notes)

        # if any of the next next notes is in the next notes, continue
        if any([note in next_notes for note in next_next_notes]):
            i += 1
            continue

        next_velocities.append([note.velocity for note in next_next_notes])
        i += 1
        velocity_check_cnt += 1

    # Get the avg velocity of the current and next notes of the subarrays and then the array
    curr_velocities = [sum(subarray) / len(subarray) for subarray in curr_velocities]
    next_velocities = [sum(subarray) / len(subarray) for subarray in next_velocities]
    curr_velocity = sum(curr_velocities) // len(curr_velocities)
    next_velocity = sum(next_velocities) // len(next_velocities)

    return abs(curr_velocity - next_velocity) >= VELOCITY_THRESHOLD * (curr_velocity)


def get_concurrent_notes_idx(curr_note, notes):
    """Return the indexes of the notes that are played together with the current note.

    Args:
        curr_note: The current note.
        notes: The list of notes.
    """
    concurrent_notes = []

    for other_note_idx, other_note in enumerate(notes):
        if other_note.pitch == curr_note.pitch:
            continue
        if other_note.start <= curr_note.end and other_note.end >= curr_note.start:
            concurrent_notes.append(other_note_idx)
        if other_note.start > curr_note.end:
            break
    return concurrent_notes


def get_notes_currently_playing(curr_note_idx, notes):
    """Return the indexes of the notes that are currently playing with the current note.

    Args:
        curr_note_idx: The index of the current note.
        notes: The list of notes.
    """
    curr_note = notes[curr_note_idx]
    concurrent_notes = get_concurrent_notes_idx(curr_note, notes)
    notes_currently_playing = concurrent_notes.copy()
    notes_currently_playing.append(curr_note_idx)
    return [notes[note_idx] for note_idx in notes_currently_playing]


def is_tonic_chord(note_pitches):
    """Return True if the note pitches are a tonic chord, False otherwise.

    Args:
        note_pitches: The pitches of the notes.
    """
    global tonic_chord_pitches

    return set(note_pitches).issubset(set(tonic_chord_pitches))


def is_dominant_chord(note_pitches):
    """Return True if the note pitches are a dominant chord, False otherwise.

    Args:
        note_pitches: The pitches of the notes.
    """
    global dominant_chord_pitches

    return set(note_pitches).issubset(set(dominant_chord_pitches))


def is_octave(note_pitches):
    """Return True if at least two notes with same pitch are the tonic, False otherwise.

    Args:
        note_pitches: The pitches of the notes.
    """
    global key

    tonic_cnt = 0
    if len(note_pitches) >= 2:
        for pitch in note_pitches:
            if str(pitch) == str(key.tonic):
                tonic_cnt += 1
    if tonic_cnt >= 2:
        return True
    return False


def is_cadence(notes_currently_playing_idx, notes):
    """Return True if the notes currently playing are a cadence, False otherwise.

    Args:
        notes_currently_playing_idx: The indexes of the notes currently playing.
        notes: The list of notes.
    """
    global tonic_chord_pitches, dominant_chord_pitches

    notes_currently_playing = [
        notes[note_idx] for note_idx in notes_currently_playing_idx
    ]
    if len(notes_currently_playing) >= 3:
        notes_currently_playing_pitches = [
            pretty_midi.note_number_to_name(note.pitch)[:-1]
            for note in notes_currently_playing
        ]

        if is_tonic_chord(notes_currently_playing_pitches) or is_octave(
            notes_currently_playing_pitches
        ):
            if any([is_extended(n) for n in notes_currently_playing]):
                first_note_idx = min(notes_currently_playing_idx)
                # check if any previous chord is a dominant chord
                for i in range(first_note_idx - 1, -1, -1):
                    previous_notes = get_notes_currently_playing(i, notes)
                    if len(previous_notes) < 3:
                        continue
                    previous_notes_pitches = [
                        pretty_midi.note_number_to_name(n.pitch)[:-1]
                        for n in previous_notes
                    ]
                    if is_dominant_chord(previous_notes_pitches):
                        return True
                    else:
                        break

        # elif is_dominant_chord(notes_currently_playing_pitches):
        #     if any([is_extended(n) for n in notes_currently_playing]):
        #         return True
    return False


def split_phrases(notes):
    """Split the notes into phrases. A phrase is a sequence of notes that ends with a silence, a sudden velocity change, a cadence, or a trill.

    Args:
        notes: The list of notes.
    """
    phrase_start = 0
    already_processed = []
    for curr_note_idx, curr_note in enumerate(notes):
        if curr_note_idx in already_processed:
            continue
        concurrent_notes = get_concurrent_notes_idx(curr_note, notes)
        next_notes = get_next_notes(curr_note_idx, notes)

        # get the concurrent note that ends last
        last_concurrent_note_idx = (
            max(concurrent_notes, key=lambda note_idx: notes[note_idx].end)
            if len(concurrent_notes) > 0
            else curr_note_idx
        )
        last_concurrent_note = notes[last_concurrent_note_idx]
        if curr_note.end > last_concurrent_note.end:
            last_concurrent_note = curr_note

        if len(next_notes) > 0:
            next_note = notes[next_notes[0]]
            notes_currently_playing_idx = concurrent_notes.copy()
            notes_currently_playing_idx.append(curr_note_idx)

            is_there_sudden_velocity_change = sudden_velocity_change(
                curr_note_idx, next_notes, notes
            )

            if (
                next_note.start - last_concurrent_note.end >= SILENCE_DURATION
                or is_there_sudden_velocity_change
                or is_cadence(notes_currently_playing_idx, notes)
                or is_trill(last_concurrent_note)
            ):
                already_processed.extend(concurrent_notes)
                already_processed.append(curr_note_idx)

                phrase = notes[phrase_start : last_concurrent_note_idx + 1]
                phrases.append(phrase)
                phrase_start = last_concurrent_note_idx + 1
    # Add the last phrase
    phrase = notes[phrase_start:]
    phrases.append(phrase)


def is_trill_duration(note):
    """Return True if the note is shortened, False otherwise.

    Args:
        note: The note to check.
    """
    note_duration = note.end - note.start
    return note_duration <= 0.05


def identify_trill(notes):
    """
    Identify trills in the given list of notes. Trills are composed of three notes of short duration, followed by a 4th note which is extended.

    Args:
        notes: The list of notes.
    """
    trills = []
    i = 0
    while i < len(notes) - 3:
        if (
            (
                notes[i].pitch == notes[i + 1].pitch
                and notes[i].pitch == notes[i + 2].pitch
            )
            and is_trill_duration(notes[i])
            and is_trill_duration(notes[i + 1])
            and is_trill_duration(notes[i + 2])
        ):
            trills.append((notes[i], notes[i + 1], notes[i + 2], notes[i + 3]))
            i += 4
        else:
            i += 1

    return trills


def is_trill(note):
    """
    Return True if the note is the last note of a trill, False otherwise.

    Args:
        note: The note to check.
    """
    for trill in trills:
        if note == trill[-1]:
            return True
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_midi_file", help="The input MIDI file")
    parser.add_argument("output_folder", help="The output phrases folder")
    args = parser.parse_args()

    input_midi_file = args.input_midi_file
    output_folder = args.output_folder
    filename = input_midi_file.split("/")[-1].split(".")[0]

    # create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load the input MIDI file representing the unperformed version
    piano = pretty_midi.PrettyMIDI(input_midi_file)

    piano_instrument = list(piano.instruments)[0]

    # Identify the key of the piece and the tonic and dominant chords
    score = music21.converter.parse(input_midi_file)
    key = score.analyze("key")

    tonic_chord_pitches = [key.tonic, key.pitchFromDegree(3), key.pitchFromDegree(5)]
    tonic_chord_pitches = [p.name for p in tonic_chord_pitches]

    dominant_chord_pitches = [
        key.pitchFromDegree(5),
        key.pitchFromDegree(7),
        key.pitchFromDegree(2),
        key.pitchFromDegree(4),
    ]
    dominant_chord_pitches = [p.name for p in dominant_chord_pitches]

    trills = identify_trill(piano_instrument.notes)

    split_phrases(piano_instrument.notes)

    avg_beat_length = 0

    # Create a midi file for each phrase
    for i, phrase in enumerate(phrases):
        phrase_midi = pretty_midi.PrettyMIDI()
        phrase_instrument = pretty_midi.Instrument(program=0)
        phrase_instrument.notes = phrase
        phrase_midi.instruments.append(phrase_instrument)
        beat_start = int(phrase[0].start)
        beat_end = int(phrase[-1].end)
        avg_beat_length += beat_end - beat_start
        phrase_midi.write(
            f"{output_folder}/{filename}_phrase_{i}_start_{beat_start}_end_{beat_end}.mid"
        )
        print(f"Phrase {i} saved, beat start: {beat_start}, beat end: {beat_end}")

    avg_beat_length = avg_beat_length / len(phrases)
    print(f"Average beat length: {avg_beat_length}")
