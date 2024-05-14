import pretty_midi
import argparse
import music21

# Constants
SILENCE_DURATION = 0.3
STANDARD_DURATION = (
    0.25  # the duration of a midi note which is not extended nor shortened
)
VELOCITY_THRESHOLD = 0.7
NR_PREV_NOTES_FOR_VELOCITY_CHECK = 5

phrases = []  # list of list of notes composing each phrase


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
        next_notes = list(set(next_notes)) # remove duplicates
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
    """Return True if there is a sudden velocity change between the current notes and the next notes, False otherwise.

    Args:
        curr_notes: The list of current notes.
        next_notes: The list of next notes.
    """
    notes_currently_playing = get_notes_currently_playing(curr_note_idx, notes)
    next_notes = [notes[note_idx] for note_idx in next_notes_idx]
    curr_velocities = [[note.velocity for note in notes_currently_playing]]

    for i in range(NR_PREV_NOTES_FOR_VELOCITY_CHECK):
        if curr_note_idx - i < 0:
            break
        prev_notes = get_notes_currently_playing(curr_note_idx - i, notes)
        curr_velocities.append([note.velocity for note in prev_notes])
    next_velocities = [note.velocity for note in next_notes]
    # print(f"max(curr_velocities): {max(curr_velocities)}")
    # print(f"max(next_velocities): {max(next_velocities)}")
    return abs(max(curr_velocities) - max(next_velocities)) >= 0.3*(max(curr_velocities))


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

def is_trill_and_then_extended(curr_note, notes):
    """Return True if the current note is a trill and extended, False otherwise.

    Args:
        curr_note: The current note.
        notes: The list of notes.
    """
    if curr_note.pitch == 67:
        next_notes = get_next_notes(curr_note, notes)
        if len(next_notes) > 0:
            next_note = notes[next_notes[0]]
            return is_extended(curr_note) and is_extended(next_note)
    return False

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


def split_phrases_followed_by_silence(notes):
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
            notes_currently_playing = concurrent_notes.copy()
            notes_currently_playing.append(curr_note_idx)
            is_there_a_extended_note = any(
                [is_extended(notes[note_idx]) for note_idx in notes_currently_playing]
            )

            print("NOTES CURRENTLY P;AYING")
            for aa in [notes[c] for c in notes_currently_playing]:
                print(aa)

            print("NEXT NOTES")
            for aa in [notes[n] for n in next_notes]:
                print(aa)

            is_there_sudden_velocity_change = sudden_velocity_change(curr_note_idx, next_notes, notes)
    
            if next_note.start - last_concurrent_note.end >= SILENCE_DURATION:# or is_there_sudden_velocity_change:
                already_processed.extend(concurrent_notes)
                already_processed.append(curr_note_idx)
                # print(len(phrases))
                # for c in concurrent_notes:
                #     print(notes[c])
                # print(f"curr_note_idx: {curr_note}")
                # print(f"concurrent_notes: {concurrent_notes}")
                # print(f"next_note: {next_note}")
                # print(f"last_concurrent_note: {last_concurrent_note}")
                # print(
                #     f"next_note.start - last_concurrent_note.end >= SILENCE_DURATION: {next_note.start - last_concurrent_note.end >= SILENCE_DURATION}"
                # )
                # phrase = notes[phrase_start : last_concurrent_note_idx + 1]
                # phrases.append(phrase)
                # phrase_start = last_concurrent_note_idx + 1
    # Add the last phrase
    phrase = notes[phrase_start:]
    phrases.append(phrase)

def is_dominant_chord(chord_obj, key):
    root = chord_obj.root().name
    third = chord_obj.third.name if chord_obj.third is not None else None
    fifth = chord_obj.fifth.name if chord_obj.fifth is not None else None
    seventh = chord_obj.seventh.name if chord_obj.seventh is not None else None

    # Check if the chord is a dominant 7th chord within the given key
    if chord_obj.isDominantSeventh() and root == key.tonic.name:
        return True
    elif key.pitchFromDegree(5).name == root and third == key.pitchFromDegree(7).name \
        and fifth == key.pitchFromDegree(2).name and seventh == key.pitchFromDegree(4).name:
        return True
    else:
        return False

STANDARD_DURATION = 0.05  # Example standard duration threshold

def identify_trill(notes):
    trills = []
    i = 0
    while i < len(notes) - 3:
        if (notes[i].pitch == notes[i + 1].pitch + 1 and
            notes[i + 1].pitch == notes[i + 2].pitch - 1) or \
           (notes[i].pitch == notes[i + 1].pitch - 1 and
            notes[i + 1].pitch == notes[i + 2].pitch + 1):
            if is_extended(notes[i]):
                trills.append((notes[i], notes[i + 1], notes[i + 2]))
                i += 3  # Skip to the next group of notes
            elif is_extended(notes[i + 2]):
                trills.append((notes[i], notes[i + 1], notes[i + 2]))
                i += 3  # Skip to the next group of notes
            else:
                i += 1  # Move to the next note
        else:
            i += 1  # Move to the next note
    return trills
    return trills
def plot_notes_velocity_by_start(notes):
    import matplotlib.pyplot as plt

    x = [note.start for note in notes]
    y = [note.velocity for note in notes]
    plt.scatter(x, y)
    plt.xlabel("Start time")
    plt.ylabel("Velocity")
    plt.title("Velocity of notes by start time")
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_midi_file", help="The input MIDI file")
    # parser.add_argument("output_midi_file", help="The output MIDI file")
    args = parser.parse_args()

    input_midi_file = args.input_midi_file

    # Load the input MIDI file representing the unperformed version
    piano = pretty_midi.PrettyMIDI(input_midi_file)

    piano_instrument = list(piano.instruments)[0]

    score = music21.converter.parse(input_midi_file)
    key = score.analyze('key')
    print("KEY: ",key.tonic.name, key.mode)

    # get the pitches of the notes belonging to the tonic chord in the key
    tonic_chord_pitches = [key.tonic, key.pitchFromDegree(3), key.pitchFromDegree(5)]
    tonic_chord_pitches = [p.name for p in tonic_chord_pitches]

    dominant_chord_pitches = [key.pitchFromDegree(5), key.pitchFromDegree(7), key.pitchFromDegree(2), key.pitchFromDegree(4)]
    dominant_chord_pitches = [p.name for p in dominant_chord_pitches]
    # print("TONIC CHORD PITCHES: ", tonic_chord_pitches)
    # print("DOMINANT CHORD PITCHES: ", dominant_chord_pitches)
    startsub = 0
    subset = piano_instrument.notes[::]
    print(f"Trills identified: {identify_trill(subset)}")
    for i, note in enumerate(subset):
        # print(f"Note {i+startsub}: {note}")
        notes_currently_playing = get_notes_currently_playing(i, subset)
        if len(notes_currently_playing) >= 2:
            # Check for cadence
            # Get the note names of the notes currently playing(without the octave number)
            notes_currently_playing_pitches = [pretty_midi.note_number_to_name(note.pitch)[:-1] for note in notes_currently_playing]
            # print(f"Notes currently playing: {notes_currently_playing_pitches}")
            # if set(notes_currently_playing_pitches).issubset(set(tonic_chord_pitches)):
            #     print("TONIC CHORD")
            # elif set(notes_currently_playing_pitches).issubset(set(dominant_chord_pitches)):
            #     print("DOMINANT CHORD")

            
            

            # print(f"Concurrent notes: ")
            # for c in concurrent_notes:
            #     print(piano_instrument.notes[c])
            
            # if concurrent notes belong to array
            

            # possible_chord_pitches.sort()

            # chord_obj = music21.chord.Chord(possible_chord_pitches)
            # get the note name from a pitch and check if all the currently playing notes belong to a dominant fifth or tonic chord
            
    # save the notes in a file
    phrase_midi = pretty_midi.PrettyMIDI()
    phrase_instrument = pretty_midi.Instrument(program=0)
    phrase_instrument.notes = subset
    phrase_midi.instruments.append(phrase_instrument)
    phrase_midi.write(f"trymio.mid")
    
    
    
    # # plot_notes_velocity_by_start(piano_instrument.notes)



    # # create a midi file for each phrase
    # # split_phrases_followed_by_silence(piano_instrument.notes)
    # for i, phrase in enumerate(phrases):
    #     phrase_midi = pretty_midi.PrettyMIDI()
    #     phrase_instrument = pretty_midi.Instrument(program=0)
    #     phrase_instrument.notes = phrase
    #     phrase_midi.instruments.append(phrase_instrument)
    #     phrase_midi.write(f"tryphrase_{i}.mid")
    #     print(f"Phrase {i} saved")
