# Digital Musicology Assignment 1: Expressive Timing in Performance
In this repository, we store the scripts that we used to develop our mapping functions and carry on the empirical analyses, with a specific focus on Mozart’s Piano Sonatas subcorpus. 
The repository is structured as follows:
- `figs/`: contains the plots that we produced in the course of our analyses.
- `compare_performances.py`: addresses the question of comparing performers against the unperformed rendition to determine who demonstrates a tendency to employ expressive timing in their performances.
- `onset_dist.py`: analyzes the distribution of note onsets within measures, identifying their likely occurrences within the metrical grid.
- `plot_velocity_timing_function.py`: extracts the velocities for each piece in our subcorpus and plots the timing function, based on the velocity multipliers for each beat.
- `taskA.py`: analyzes the annotation file for each piece in our subcorpus and plots the timing function, based on the duration multipliers for each beat.  
- `taskB_part2.py`: addresses the question of where in the metrical grid expressive timing is most likely to occur by modularizing the beat based on the time signature and taking the average of the duration multipliers.
