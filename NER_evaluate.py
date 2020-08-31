#!/bin/bash/python3


#Tagger for NER tags, using a previously trained NER chunker

import nltk, re, pprint, sys, time, pickle, pandas
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

#from nltk.tree import Tree

### VARIABLES ###
POS_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_tags.csv'
POS_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/POS_typical_tags.csv'
NER_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/NER_tags.csv'
NER_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/NER_typical_tags.csv'

### FUNCTIONS ###


