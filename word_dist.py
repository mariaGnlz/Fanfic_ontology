#!/usr/bin/bash/python3

from nltk.tokenize import RegexpTokenizer 
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk.corpus import wordnet
#from fic_processing import FanficGetter
import matplotlib.pyplot as plt
#import numpy as np
import sys, nltk, pandas

### VARIABLES ###
TYPICAL_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/typical_txt_paths.txt'
NER_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/NER_typical_tags.csv'
PRONOUNS = ["i", "you", "he","she"]
NAMED_CHARACTERS = []

### FUNCTIONS ###
def get_named_characters():
	csv_file = pandas.read_csv(NER_TYPICAL_PATH)

	iob = csv_file['IOB']
	word = csv_file['Word']

	inside = True
	characters = []
	for i in range(len(iob)):
		if iob[i] == 'per':
			if inside: 
				characters.append(word[i].lower())
				inside = False
			else: inside = True

	#print(characters) #debug

	NAMED_CHARACTERS.extend(list(set(characters)))
		

def get_lemma(word):
	lemma = wordnet.morphy(word)

	if lemma is None:
		return word
	else: return lemma

def fic_tokenize(fic):
	#tokenize text and filter out stopwords
	en_stop = stopwords.words('english')
	en_stop.extend(PRONOUNS)
	en_stop.extend(NAMED_CHARACTERS)
	tokenizer = RegexpTokenizer(r'\w+')

	#word_tokens = word_tokenize(fic)
	word_tokens = tokenizer.tokenize(fic)
	word_tokens = [word.lower() for word in word_tokens]
	#print(type(word_tokens[0])) #debug
	filtered_tokens = [word for word in word_tokens if word not in en_stop]
	
	#stem words
	#stemmer = PorterStemmer()
	#processed_tokens = [stemmer.stem(t) for t in filtered_tokens]
	processed_tokens = [get_lemma(word) for word in filtered_tokens]
	
	#print(processed_tokens[0:20]) #debug
	#return word_tokenize(fic.translate(string.punctuation))
	return processed_tokens

def get_txt_fanfic(fic_index):
	paths_file = open(TYPICAL_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()

	txt_fic = open(fic_paths[fic_index], 'r').read()
	
	
	return txt_fic
	
### MAIN ###
get_named_characters() 

if len(sys.argv) == 2:
	fic_index = int(sys.argv[1])
	#print(fic_index) #debug
	fic_text = get_txt_fanfic(fic_index)

	# Open and get text from HTML files
	tokens = fic_tokenize(fic_text)

	fd = nltk.FreqDist(tokens)

	fd.plot(30,cumulative=False)
else:
	print('Error. Correct usage: \nword_dist.py [fic_index]')
