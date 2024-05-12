from music21 import *
from music21.repeat import Expander
from gensim.models import FastText
import os
import numpy as np
import pickle
import matplotlib.pyplot as plt
import librosa
import warnings

def helpers_partition_measures_slangpolska(scores):
    k = ''
    tokenized_measures = []
    all_measures = []
    partitioned_measures = {}
    for score in scores:
        tmp_measure_set = []
        for measure in scores[score].getElementsByClass(stream.Part)[0].getElementsByClass(stream.Measure):
            tmp_tokenized_measure = []
            tmp_measure = ''
            if measure.flat.keySignature is not None:
                k = measure.flat.keySignature
            for event in measure.notesAndRests:
                try:
                    tmp_tokenized_measure.append((k.name, event.duration.quarterLength, event.beat, event.name))
                    tmp_measure = tmp_measure + " " + str(event.beat) + "_" + str(event.name) + "_" + str(event.duration.quarterLength)
                except:
                    tmp_tokenized_measure.append((k.name, event.duration.quarterLength, event.beat, event.pitchedCommonName))
                    tmp_measure = tmp_measure + " " + str(event.beat) + "_" + str(event.pitchedCommonName) + "_" + str(event.duration.quarterLength)
            tokenized_measures.append(tmp_tokenized_measure)
            all_measures.append(tmp_measure[1:])
            tmp_measure_set.append(tmp_measure[1:])
        partitioned_measures[score] = tmp_measure_set
    return all_measures, partitioned_measures, tokenized_measures

def helpers_partition_measures_oth(scores):
    scores_partitioned_measures = {}
    for score in range(len(scores)):
        tmp_measure_set = []
        for measure in scores[score].getElementsByClass(stream.Measure):
            tmp_measure = ''
            for event in measure.notesAndRests:
                tmp_measure = tmp_measure + " " + str(event.beat) + "_" + str(event.name) + "_" + str(event.duration)
            tmp_measure_set.append(tmp_measure[1:])
        scores_partitioned_measures[score] = tmp_measure_set
    return scores_partitioned_measures

def helpers_partition_measures_wrapper(scores, set_moniker):
    if set_moniker == "orig":
        a, partitioned_measures, c = helpers_partition_measures_slangpolska(scores)
        return a, partitioned_measures, c
    else:
        partitioned_measures = helpers_partition_measures_oth(scores)
        return partitioned_measures

def helpers_train_measure_embedder(max_measure_length, xml_file_location, slangpolska_scores):
    # Create measure 'sentences' to create note embeddings
    all_measures, slangpolska_scores_partitioned_measures, tokenized_measures = helpers_partition_measures_wrapper(slangpolska_scores, "orig")
    tokenized_measures = [measure.split(' ') for measure in all_measures]
    # Train embedding model
    # https://medium.com/@93Kryptonian/word-embedding-using-fasttext-62beb0209db9
    num_words = 3400
    embed_dim = 128
    batch_size = 512
    model = FastText(tokenized_measures, vector_size = 128, window = 5, min_count = 3, workers = 4, epochs = 10, seed = 5, sg = 1)
    encoder_model = model.wv
    model.save('dependencies/fasttext')

def helpers_import_slangpolskas(xml_file_location, keepScoresWithChords = False):
    scores_xml = os.listdir(xml_file_location)
    slangpolska_scores = {}
    excluded = 0
    for si in range(len(scores_xml)):
        if scores_xml[si] != 'conversion.log':
            tmp = converter.parse(xml_file_location + scores_xml[si])
            tmp_meters = tmp.recurse().getElementsByClass(meter.TimeSignature)
            if len(tmp_meters) != 1 or tmp_meters[0].ratioString != '3/4':
                excluded += 1
            elif tmp.recurse().notesAndRests[-1].measureNumber < 8:
                excluded += 1
            else:
                chord_found = 0
                if keepScoresWithChords == False:
                    for event in tmp.recurse().notes:
                        if event.measureNumber > 8:
                            # pass notes test, proceed
                            break
                        try:
                            event.pitchedCommonName
                            chord_found = 1
                        except:
                            pass
                if chord_found == 1:
                    excluded += 1
                else:
                    try:
                        tmp2 = tmp.expandRepeats()
                        slangpolska_scores[scores_xml[si]] = tmp2
                    except:
                        excluded += 1

    return slangpolska_scores

def helpers_embed_measures(partitioned_measures, encoder_model):
    embedded_measures = {}
    for score in partitioned_measures:
        tmp_embedded_measure_set = []
        for measure in partitioned_measures[score]:
            measure_vec = encoder_model[measure] #.replace("|"," ")
            tmp_embedded_measure_set.append(measure_vec)
        embedded_measures[score] = tmp_embedded_measure_set #[0:8]
    return embedded_measures

def helpers_plot_maximizing_transpositions(self_sim_mat_new2, ti_index_ssm):
    carved_ti_index_ssm = np.where(self_sim_mat_new2 > .85, ti_index_ssm, -1)
    carved_ti_index_ssm = np.where(carved_ti_index_ssm > 6, abs(12 - carved_ti_index_ssm), carved_ti_index_ssm)
    min_value_color = 'bisque'
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    cmap = plt.cm.get_cmap('Blues', 6)
    cmap.set_under(min_value_color)

    plt.imshow(carved_ti_index_ssm, cmap=cmap, interpolation='nearest', vmin=0, vmax=6, extent=[0,32,32,0])
    plt.xticks([0, 4, 8, 12, 16, 20, 24, 28, 32], ['0', '4', '8', '12', '16', '20', '24', '28', '32'], fontsize=8)
    plt.yticks([0, 4, 8, 12, 16, 20, 24, 28, 32], ['0', '4', '8', '12', '16', '20', '24', '28', '32'], fontsize=8)
    plt.colorbar()
    plt.title("Similarity-Maximizing Transposition Interval\nMagnitude, High-Similarity Pairings Only")
    plt.show()
    
def helpers_transpose_measure_string(measure_i, transposition_num):
    chroma_12 = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    transposed_measure_list = []
    for note in measure_i.split(" "):
        tmp = note.split("_")
        tmp[1] = chroma_12[(chroma_12.index(tmp[1]) + transposition_num) % len(chroma_12)]
        transposed_measure_list.append('_'.join(tmp))
    return ' '.join(transposed_measure_list)