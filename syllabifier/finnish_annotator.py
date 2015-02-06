# coding=utf-8
from finnish_functions import (
    split_syllable,
    Stress,
    SYLLABLE_SEPARATOR,
    Weight,
    )
from finnish_syllables import initialize_presyllabified, make_syllables
from finnish_weight import make_weights
from finnish_sonority import make_sonorities
from finnish_stress import make_stresses

from copy import deepcopy

import os.path

# location in list of user files for each file
PRESYLL = 0
INITIAL = 1
SUFFIX = 2
COMPOUND = 3

# default values, in case user input is ill-formed or unavailable
user_files = [
    'presyllabified.txt',
    'initial.txt',
    'suffix.txt',
    'compound.txt',
    ]

config_file = 'config.txt'

initial_compounds = []
suffixes = []
compound_dict = {}


# initialize list l with words from filename, a file with words on individual
# lines
def initialize_list(l, filename):

    try:

        f = open(filename, 'r')
        entries = f.readlines()
        f.close()

        for i in range(len(entries)-1):
            l += [entries[i][:-1].lower()]  # remove final newline character

        l += [entries[-1].lower()]  # final line has no newline

    except IOError:

        print "Error: File not found."


# initialize dict with entries, where key is entry from entries in lowercase
# without separator, and value is list of words in entry split at separator
def initialize_dict(dict, entries, separator):

    for entry in entries:

        entry = entry.lower()
        hyphen_free = entry.replace(separator, '')
        words = entry.split(separator)
        dict[hyphen_free] = words


# initialize a dictionary from a file
# the first line of the file is the separator character
# the remaining lines are words with separations marked by the separator
# character
def initialize_dict_from_file(dict, filename):

    try:

        f = open(filename, 'r')
        entries = f.readlines()
        f.close()

        for i in range(len(entries)-1):
            entries[i] = entries[i][:-1]  # remove final newline character

        separator = entries[0]
        entries = entries[1:]
        initialize_dict(dict, entries, separator)

    except IOError:

        print "Error: File not found."


# initialize configuration
def initialize_config():

    try:

        f = open(config_file, 'r')
        entries = f.readlines()
        f.close()

        if len(entries) != len(user_files):

            return

        for i in range(len(user_files)-1):  # last word does not end in newline

            entries[i] = entries[i][:-1]

        for i in range(len(user_files)):

            if os.path.isfile(entries[i]):

                user_files[i] = entries[i]

    except IOError:

        print "Error: Config file not found."

    initialize_presyllabified(user_files[PRESYLL])
    initialize_list(initial_compounds, user_files[INITIAL])
    initialize_list(suffixes, user_files[SUFFIX])
    initialize_dict_from_file(compound_dict, user_files[COMPOUND])

initialize_config()


# a class representing an annotation
# the constructor assumes that the word contains no compounds
class Annotation:
    def __init__(self, word):
        self.word = word
        self.syllables = make_syllables(word)
        self.split_sylls = [split_syllable(syll) for syll in self.syllables]
        self.weights = make_weights(self.split_sylls)
        self.sonorities = make_sonorities(self.split_sylls)
        self.stresses = make_stresses(self.weights)

    def join(self, annotation):
        self.word += annotation.word
        self.syllables += annotation.syllables
        self.weights += annotation.weights
        self.sonorities += annotation.sonorities

        # only concatenate stresses if there is something to concatenate
        if len(annotation.stresses[0]) > 0:

            total_stresses = []

            for i in range(len(self.stresses)):

                for j in range(len(annotation.stresses)):

                    total_stresses += [deepcopy(self.stresses[i])]
                    total_stresses[-1] += [Stress.secondary]

                    # replace initial (primary) stress of annotation with
                    # secondary stress
                    total_stresses[-1] += annotation.stresses[j][1:]

            self.stresses = total_stresses


# if the final word in the list of words starts with a word in the list of
# compound-initial words, split the word and apply the function again
# (i.e., split off all initial words in initial_compounds)
def split_initial_compounds(words):

    for word in initial_compounds:

        if words[-1].lower().startswith(word):

            return split_initial_compounds(
                words[:-1] +
                [words[-1][:len(word)]] +
                [words[-1][len(word):]]
                )

    return words


# if the final word in the list of words ends with a suffix in suffixes, split
# the word at the suffix
def split_suffix(words):

    for suffix in suffixes:

        if words[-1].lower().endswith(suffix):

            boundary = len(words[-1]) - len(suffix)  # TODO

            return words[:-1] + [words[-1][:-len(suffix)]] + \
                [words[-1][-len(suffix):]]

    return words


# split each word in words apart if it appears in the dictionary of compounds
def split_preannotated_compounds(words):

    result = []

    for i in range(len(words)):

        if words[i].lower() in compound_dict:

            result += compound_dict[words[i].lower()]  # TODO

        else:

            result += [words[i]]

    return result

ORTHOGRAPHIC_COMPOUND_MARKER = '-'  # the symbol in Finnish orthography marking
# compound boundaries


# make an annotation for a word
def make_annotation(word):
    words = [word]
    words = split_initial_compounds(words)
    words = words[:-1] + words[-1].split(ORTHOGRAPHIC_COMPOUND_MARKER)
    words = split_suffix(words)
    words = split_preannotated_compounds(words)
    annotations = [Annotation(word) for w in words]

    for i in range(1, len(annotations)):
        annotations[0].join(annotations[i])

    return annotations[0]


# print a representation of an annotation for a word
def print_annotation(word_annotation):
    x = annotation_string(word_annotation)
    print x.encode('utf-8')  # ´ka.la.
    print pattern_string(word_annotation)  # Weight: LL Stress: PU Sonority: AA
    print

    # try:
    #     result = annotation_string(word_annotation).encode('utf-8')
    #     result += pattern_string(word_annotation)

    #     return result

    # except Exception as e:
    #     print e


# annotate and print the annotation for a word
def mark(word):

    return print_annotation(make_annotation(word))


def annotation_string(word_annotation):  # JOSH

    result = u''

    for i in range(len(word_annotation.stresses)):

        result += SYLLABLE_SEPARATOR

        for j in range(len(word_annotation.syllables)):

            # mark stresses
            if word_annotation.stresses[i][j] == Stress.primary:
                result += u'´'

            elif word_annotation.stresses[i][j] == Stress.secondary:
                result += u'`'

            # add syllable content and separator
            result += word_annotation.syllables[j] + SYLLABLE_SEPARATOR

        result += '\n'

    return result[:-1]  # remove final newline


def syllable_annotation(word):  # NAOMI
    # import pdb; pdb.set_trace()
    word_annotation = make_annotation(word)

    result = u''

    for syll in word_annotation.syllables:
        result += syll + SYLLABLE_SEPARATOR

    return result[:-1]


# return a string representing the weight pattern
# e.g. the weights for ".´ny.ky.`en.nus.te." are represented 'LLHHL'
def syll_pattern(weights):

    result = ''

    for w in weights:

        result += Weight.dict[w]

    return result


# return a string representing the stress pattern
# e.g. the stresses for ".´ny.ky.`en.nus.te." are represented 'PUSUU'
def stress_pattern(stresses):

    result = ''

    for i in range(len(stresses)):

        for s in stresses[i]:

            result += Stress.dict[s]

        result += ', '

    return result[:-2]  # remove last comma and space


# return a string representing the sonority pattern
# e.g. the sonority for taloiden is represented 'AAI'
def sonority_pattern(sonorities):

    result = ''

    for s in sonorities:

        result += s

    return result


# print a representation of the weights and stresses
def pattern_string(word_annotation):
    return '\n\tWeight: %s\n\tStress: %s\n\tSonority: %s\n\t' % (
        syll_pattern(word_annotation.weights),
        stress_pattern(word_annotation.stresses),
        sonority_pattern(word_annotation.sonorities),
        )


if __name__ == '__main__':
    import sys
    word = sys.argv[1]
    # mark(word)
    print syllable_annotation(word)
