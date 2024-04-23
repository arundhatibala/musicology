# Digital Musicology Assignment 2: Generate Expressive Performance
In this repository, we store the Python script to tranform an unperformed MIDI file into an expressive performance using the library `pretty_midi`. We focused on the Turkish March from Mozart's Piano Sonata No. 11 in A major, K. 331.

The repository is structured as follows:
- `midi_score.mid`: it is the unperformed MIDI file that we used as input.
- `transform.py`: it is the Python script that we developed to generate the expressive performance.
- `output.mid`: it is the generated performed MIDI file.

The script `transform.py` works as follows:
- Load the input MIDI file representing the unperformed version.
- Extract the right hand, representing the melody, and the left hand, representing the bass.
- Normalize the volume of the left hand to be lower than the right hand.
- Add staccato to repeated notes in the left hand.
- Add staccato to melody notes in the right hand.
- Add general randomization on velocity in the right hand.
- Adjust notes followed by silence in the right hand and left hand, adding breath effect.
- Add staccato to repeated notes in the right hand.
- Update the instruments  with modified notes.
- Save the new MIDI file with the expressive performance techniques applied.

The script can be executed from the command line with the following command:
```bash
python transform.py midi_score.mid output.mid
```

The script requires the library `pretty_midi` to be installed. It can be installed with the following command:
```bash
pip install pretty_midi
```