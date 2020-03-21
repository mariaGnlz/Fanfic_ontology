#!/bin/bash/python3


#Bigger toy version of an entity recognition process

import nltk, re, pprint
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.classify import megam
from NER_chunker import NERChunker
from nltk.corpus import conll2002


### NOTAS ###
"""
NLTK no tiene un corpus adecuado para el reconocimiento de entindades en ingles,
de modo que utilizare (de momento) el corpus CoNLL2002 para NER en espanol
"""


### VARIABLES ###
TXT_FIC_LISTING_PATH = '/home/maria/Documents/TFG/txt_fic_paths.txt'
megam.config_megam('/home/maria/Downloads/megam_0.92/megam')

### FUNCTIONS ###
"""
def ie_preprocess(document):	#divide raw text into words and tag them
	sentences = nltk.sent_tokenize(document) #sentence segmentation
	sentences = [nltk.word_tokenize(sent) for sent in sentences] #tokenization
	sentences = [nltk.pos_tag(sent) for sent in sentences] #POS tagging
	
	return sentences

def get_train_fanfics():
	fic_paths = []
	fic_paths_file = open(TXT_FIC_LISTING_PATH, 'r')

	for path in fic_paths_file.readlines():
		if '_train' in path: fic_paths.append(path[:-1])

	fic_paths_file.close()
	
	fic_text=''
	for path in fic_paths:
		txt_file = open(path, 'r')
		fic_text=fic_text+txt_file.read()
		txt_file.close()

	preprocessed_fics = ie_preprocess(fic_text)

	return preprocessed_fics

		
### Open and get text from txt file
train_text = get_train_fanfics()
"""

### Get train and test sentences:
train_sents = conll2002.chunked_sents('esp.train')
test_sents = conll2002.chunked_sents('esp.testa')

### Create chunker:

NER_chunker = NERChunker(train_sents)
print('NER chunker: \n',NER_chunker.evaluate(test_sents))
