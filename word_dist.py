#!/usr/bin/bash/python3

from nltk.tokenize import RegexpTokenizer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk.tag import pos_tag

import matplotlib.pyplot as plt
import numpy as np
import sys, nltk, time

### VARIABLES ###
#TXT_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/typical_txt_paths.txt'
#TXT_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/romance_txt_paths.txt'
TXT_NE_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/trial_ne_txt_paths2.txt'
TXT_E_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/trial_e_txt_paths2.txt'

#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR','VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives and verbs (all kinds) aka C
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adverbs and verbs (all kinds) aka B
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','UH'] #nouns, adverbs and verbs (all kinds) aka BUH
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives, adverbs and verbs (all kinds) aka D
INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','UH'] #nouns, adjectives, adverbs and verbs (all kinds) aka DUH

#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS'] #nouns, adjectives and adverbs (all kinds)

UNINTERESTING_TOKENS = ['be', 'are', 'wasn', 'wa', 'have', 'say', 'do', 'don', 'get', 're', 'll', 've', 'd', 'm', 's', 't','_']
### FUNCTIONS ###
def get_lemma(word):
	lemma = wordnet.morphy(word)

	if lemma is None:
		return word
	else: return lemma

def fic_tokenize(fic):
	#tokenize text and filter out stopwords
	en_stop = stopwords.words('english')
	#en_stop.extend(PRONOUNS)
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

def fic_tokenizev2(fic):
	sent_tokens = sent_tokenize(fic)
	tokenizer = RegexpTokenizer(r'\w+')
	pos_tokens = [pos_tag(tokenizer.tokenize(sent)) for sent in sent_tokens]
	#pos_tokens = [pos_tag(word_tokenize(sent)) for sent in sent_tokens]

	interesting_words = []
	for token in pos_tokens:
		for word, pos in token:
			#word = word.strip()
			if pos in INTERESTING_POS: interesting_words.append(word)

	processed_tokens = [get_lemma(word) for word in interesting_words if get_lemma(word) not in UNINTERESTING_TOKENS]
	
	return processed_tokens
	
def get_txt_fanfics(single_group):

	if single_group:
		paths_file = open(TXT_LISTING_PATH, 'r')
		fic_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()

		txt_fic = ''
		for path in fic_paths:
			text = open(path, 'r').read()
			txt_fic = txt_fic + text
			#print(i)

		return txt_fic

	else:
		paths_file = open(TXT_E_LISTING_PATH, 'r')
		efics_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()
		#efics_paths[0:788]

		paths_file = open(TXT_NE_LISTING_PATH, 'r')
		nefics_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()
		#nefics_paths[0:2409]

		txt_efic=''
		for path in efics_paths:
			text = open(path, 'r').read()
			txt_efic = txt_efic + text

	
		txt_nefic=''
		for path in nefics_paths:
			text = open(path, 'r').read()
			txt_nefic = txt_nefic + text
	
		return (txt_efic, txt_nefic)


def get_txt_fanfics_in_range(start, end):
	paths_file = open(TXT_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()

	txt_fic = ''
	for i in range(start, end):
		text = open(fic_paths[i], 'r').read()
		txt_fic = txt_fic + text
		#print(i)

	return txt_fic
		
def get_grouped_txt_fanfics_in_range(estart, eend, nstart, nend):
	paths_file = open(TXT_E_LISTING_PATH, 'r')
	efics_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()

	paths_file = open(TXT_NE_LISTING_PATH, 'r')
	nefics_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()

	txt_efic=''
	for i in range(estart, eend):
		text = open(efics_paths[i], 'r').read()
		txt_efic = txt_efic + text

	
	txt_nefic=''
	for i in range(nstart, nend):
		text = open(nefics_paths[i], 'r').read()
		txt_nefic = txt_nefic + text
	
	return (txt_efic, txt_nefic)
		
	
### MAIN ###
if len(sys.argv) == 1:
	start_time = time.time()
	efic_text, nefic_text = get_txt_fanfics(False)

	etokens = fic_tokenizev2(efic_text)
	netokens = fic_tokenizev2(nefic_text)

	efd = nltk.FreqDist(etokens)
	nefd = nltk.FreqDist(netokens)

	ewords = efd.keys()
	newords = nefd.keys()

	#distinctive_words=[word for word in ewords if word not in newords]
	distinctive_words=[word for word in newords if word not in ewords]	
	print(len(distinctive_words), '\n',distinctive_words[:10])
	dic_words = {word : nefd[word] for word in distinctive_words}
	
	lists = sorted(dic_words.items())
	
	karam = [(word, freq) for word, freq in lists if freq >34] 
	x, y = zip(*karam)
	
	
	end_time = time.time()
	print('Elapsed time: ',(end_time-start_time)/60,' minutes')

	plt.plot(x,y)

	plt.show()
	
	
elif len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])
	#print(start_index, end_index) #debug

	start_time = time.time()
	fic_text = get_txt_fanfics_in_range(start_index, end_index)
	
	# Open and get text from HTML files
	#tokens = fic_tokenize(fic_text)
	tokens = fic_tokenizev2(fic_text)

	#print(tokens[:10]) #debug

	fd = nltk.FreqDist(tokens)

	end_time = time.time()
	print('Elapsed time: ',(end_time-start_time)/60,' minutes')

	fd.plot(60,cumulative=False)
		

elif len(sys.argv) == 5:
	estart_index = int(sys.argv[1])
	eend_index = int(sys.argv[2])
	nstart_index = int(sys.argv[3])
	nend_index = int(sys.argv[4])
	print(estart_index, eend_index, nstart_index, nend_index) #debug

	start_time = time.time()
	efic_text, nefic_text = get_txt_fanfics_in_range(estart_index, eend_index, nstart_index, nend_index)

	etokens = fic_tokenizev2(efic_text)
	netokens = fic_tokenizev2(nefic_text)

	efd = nltk.FreqDist(etokens)
	nefd = nltk.FreqDist(netokens)

	ewords = efd.keys()
	newords = nefd.keys()

	distinctive_words=[word for word in ewords if word not in newords]
	#print(len(distinctive_words), '\n',distinctive_words[:10])
	dic_words = {word : efd[word] for word in distinctive_words}
	
	lists = sorted(dic_words.items())
	
	karam = [(word, freq) for word, freq in lists if freq >19] 
	x, y = zip(*karam)
	
	
	end_time = time.time()
	print('Elapsed time: ',(end_time-start_time)/60,' minutes')

	plt.plot(x,y)

	plt.show()

else:
	print('Error. Correct usage: \nword_dist.py <start> <end>')
