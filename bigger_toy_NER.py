#!/bin/bash/python3


#Bigger toy version of an entity recognition process

import nltk, re, pprint, time, pickle
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.tree import Tree
from nltk.classify import megam
from NER_chunker import NERChunkerv1, NERChunkerv3
import pandas



### NOTAS ###
"""
NLTK no tiene un corpus adecuado para el reconocimiento de entindades en ingles,
de modo que utilizare una base de datos en csv para NER basada en GMB
"""


### VARIABLES ###
TXT_FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/txt_fic_paths.txt'
NER_DATASET_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_train/ner_dataset.csv'
megam.config_megam('/home/maria/Downloads/megam_0.92/megam')

### FUNCTIONS ###

def ie_preprocess(document):	#divide raw text into words and tag them
	#sentences = nltk.sent_tokenize(document) #sentence segmentation
	#sentences = [nltk.word_tokenize(sent) for sent in sentences] #tokenization
	#sentences = [nltk.pos_tag(sent) for sent in sentences] #POS tagging
	
	sentences = pos_tag(word_tokenize(document))
	return sentences

def get_tagged_tokens_from_csv():
	csv_file = pandas.read_csv(NER_DATASET_PATH, encoding='ISO-8859-1')
	
	i = 0
	sentences = []
	current_sent = []
	while i < len(csv_file['Sentence #']):
		if i == 0:
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i], 	csv_file['Tag'][i]))
			
		elif ':' in str(csv_file['Sentence #'][i]): 
		
			sentences.append(nltk.chunk.conlltags2tree(current_sent))

			current_sent = []
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i], csv_file['Tag'][i]))
 
		else:
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i], csv_file['Tag'][i]))

		i+=1

	return sentences #returns a list of tagged sentences that NLTK can understand
"""
def to_nltk_format(sentences):
	nltk_sentences = [[((w,t),c) for w,t,c in nltk.chunk.tree2conlltags(sent)] for sent in sentences]

	return nltk_sentences
		

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
tagged_sentences = get_tagged_tokens_from_csv()
#print(tagged_sentences[0], tagged_sentences[1], tagged_sentences[2]) #debug
#print(isinstance(tagged_sentences[0], Tree)) #debug

train_sents = tagged_sentences[:int(len(tagged_sentences)*0.1)] #debug, tarda 18 mins
#train_sents = tagged_sentences[:int(len(tagged_sentences)*0.9)] #aprox 4 horas
test_sents = tagged_sentences[int(len(tagged_sentences)*0.9):] 


### Create and train chunker:
start = time.time()
NER_chunker = NERChunkerv1(train_sents)
end = time.time()


### Take our chunker for a spin

trial = NER_chunker.parse(pos_tag(word_tokenize('A friendly dessert community where the sun is hot, the moon is beautiful, and misterious lights pass overhead while we all pretend to sleep. Welcome to Night Vale')))

print('WTNV sentence:\n', trial)

trial = NER_chunker.parse(pos_tag(word_tokenize('It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.')))

print('Austen sentence:\n', trial)

trial = NER_chunker.parse(pos_tag(word_tokenize('I travel to Germany on Monday')))

print('Travel sentence:\n', trial)

print('NER chunker (',(end-start)/60,'mins) \n',NER_chunker.evaluate(test_sents))


### Store trained chunker for later use
f = open('bigger_toy_NER.pickle','wb')
pickle.dump(NER_chunker, f)
f.close()

print('NER_chunker successfully pickled')


"""
### What has the chunker learnt?
postags = sorted(set(pos for sent in train_sents
                     for (word, pos) in sent.leaves()))
print('The chunker has learnt:\n',NER_chunker.tagger.tag(postags))



f = open('/home/maria/Documents/TFG/TFG_fics/txt/BlessedCursed_Retirement_train.txt', 'r')

text_sents = ie_preprocess(f.read())

fic_chunks = NER_chunker.parse(text_sents)
print('first fic chunk:\n',fic_chunks[0])
"""
