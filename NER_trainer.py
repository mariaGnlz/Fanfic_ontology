#!/bin/bash/python3


#Trainer for an entity recognition process

import nltk, re, pprint, time, pickle, pandas
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
#from nltk.tree import Tree
from nltk.classify import megam
from NER_chunker import NERChunkerv1



### NOTAS ###
"""
NLTK no tiene un corpus adecuado para el reconocimiento de entindades en ingles,
de modo que utilizare una base de datos en csv para NER basada en GMB
"""


### VARIABLES ###
NER_DATASET_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_train/ner_dataset.csv'
megam.config_megam('/home/maria/Downloads/megam_0.92/megam')

### FUNCTIONS ###

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

### M A I N ###

### Get train and test sentences:
tagged_sentences = get_tagged_tokens_from_csv()
#print(tagged_sentences[0], tagged_sentences[1], tagged_sentences[2]) #debug
#print(isinstance(tagged_sentences[0], Tree)) #debug

#Database: 70% for training, 30% for testing (in three 'slices' of 10% each)

#train_sents = tagged_sentences[:int(len(tagged_sentences)*0.1)] #debug, tarda 20 mins aprox

train_sents = tagged_sentences[:int(len(tagged_sentences)*0.7)] #aprox 4 horas
#test_sents = tagged_sentences[int(len(tagged_sentences)*0.8):int(len(tagged_sentences)*0.7)] #Test A
#test_sents = tagged_sentences[int(len(tagged_sentences)*0.9):int(len(tagged_sentences)*0.8)] #Test B
test_sents = tagged_sentences[int(len(tagged_sentences)*0.9):] #Test C


### Create and train chunker:
start = time.time()
NER_chunker = NERChunkerv1(train_sents)
end = time.time()


### Test our chunker
print('NER chunker (',(end-start)/60,'mins) \n',NER_chunker.evaluate(test_sents))


### Store trained chunker for later use
print('Preparing to pickle. . .')
f = open('NER_training.pickle','wb')
pickle.dump(NER_chunker, f)
f.close()

print('NER_chunker successfully pickled')
