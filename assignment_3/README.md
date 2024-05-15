# Digital Musicology Assignment 3: Phrases in performance and phrases in the score
In this repository we store the Python scripts to segment a performed MIDI file into phrases using two different methods: the first one based on the score and the second one based on the performance. We focused on the Turkish March from Mozart's Piano Sonata No. 11 in A major, K. 331.

The repository is structured as follows:
- `Stahievitch02.mid`: it is the performed MIDI file that we used as input corresponding to the Turkish March.
- `larger_corpus`: it contains the larger corpus of MIDI files that we used to evaluate the performance-based phrase segmentation. It corresponds to the other Mozart piano sonatas in the original dataset.
- `phrases`: it is the folder where we store the phrases segmented based on the Turkish March performance MIDI file.
- `larger_corpus_phrases`: it is the folder where we store the phrases segmented based on the performance for the larger corpus.
- `phrase_segmentation.py`: it is the Python script that we developed to segment the performed MIDI file into phrases based on the performance.
- `model_p_score.ipynb`: it is the Jupyter notebook that we developed to segment the performed MIDI file into phrases based on the score.
- `ssm_turkish_march.ipynb`: TODO

The script `phrase_segmentation.py` segments the performed MIDI file into phrases based on these performance attributes:
- Silence
- Sudden velocity change
- Trills
- Cadences

The script can be executed from the command line with the following command:
```bash
python phrase_segmentation.py input_midi_path output_phrases_folder
```

The script requires the libraries `pretty_midi` and `music21` to be installed. It can be installed with the following commands:
```bash
pip install pretty_midi
pip install music21
```


The notebook `model_p_score.ipynb` segments the performed MIDI file into phrases based on the score by using self-similarity matrices.
TODO