import pretty_midi
import argparse

# Constants
SILENCE_DURATION = 0.3
STANDARD_DURATION = (
    0.25  # the duration of a midi note which is not extended nor shortened
)
VELOCITY_THRESHOLD = 0.5
NR_NOTES_FOR_VELOCITY_CHECK = 5

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

    print(f"abs(curr_velocity - next_velocity) >= VELOCITY_THRESHOLD*(curr_velocity) : {abs(curr_velocity - next_velocity) >= VELOCITY_THRESHOLD*(curr_velocity)}")
    if abs(curr_velocity - next_velocity) >= VELOCITY_THRESHOLD*(curr_velocity):
        print(f"notes currently playing:")
        for n in notes_currently_playing:
            print(n)
        print(f"next notes:")
        for n in next_notes:
            print(n)
    return abs(curr_velocity - next_velocity) >= VELOCITY_THRESHOLD*(curr_velocity)


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
    
            if next_note.start - last_concurrent_note.end >= SILENCE_DURATION or is_there_sudden_velocity_change:
                already_processed.extend(concurrent_notes)
                already_processed.append(curr_note_idx)
                print(len(phrases))
                for c in concurrent_notes:
                    print(notes[c])
                print(f"curr_note_idx: {curr_note}")
                print(f"concurrent_notes: {concurrent_notes}")
                print(f"next_note: {next_note}")
                print(f"last_concurrent_note: {last_concurrent_note}")
                print(
                    f"next_note.start - last_concurrent_note.end >= SILENCE_DURATION: {next_note.start - last_concurrent_note.end >= SILENCE_DURATION}"
                )
                
                phrase = notes[phrase_start : last_concurrent_note_idx + 1]
                phrases.append(phrase)
                phrase_start = last_concurrent_note_idx + 1
    # Add the last phrase
    phrase = notes[phrase_start:]
    phrases.append(phrase)


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



    startsub = 0
    subset = piano_instrument.notes[startsub:startsub+50]
    for i, note in enumerate(subset):
        print(f"Note {i+startsub}: {note}")
        concurrent_notes = get_concurrent_notes_idx(note, piano_instrument.notes)
        print(f"Concurrent notes: ")
        for c in concurrent_notes:
            print(piano_instrument.notes[c])
        next_notes = get_next_notes(i+startsub, piano_instrument.notes)
        print(f"Next notes: ")
        for n in next_notes:
            print(piano_instrument.notes[n])
        print("----------------")
    # save the notes in a file
    phrase_midi = pretty_midi.PrettyMIDI()
    phrase_instrument = pretty_midi.Instrument(program=0)
    phrase_instrument.notes = subset
    phrase_midi.instruments.append(phrase_instrument)
    phrase_midi.write(f"trymio.mid")
    
    
    
    # plot_notes_velocity_by_start(piano_instrument.notes)



    # create a midi file for each phrase
    split_phrases_followed_by_silence(piano_instrument.notes)
    for i, phrase in enumerate(phrases):
        phrase_midi = pretty_midi.PrettyMIDI()
        phrase_instrument = pretty_midi.Instrument(program=0)
        phrase_instrument.notes = phrase
        phrase_midi.instruments.append(phrase_instrument)
        phrase_midi.write(f"tryphrase_{i}.mid")
        print(f"Phrase {i} saved")
