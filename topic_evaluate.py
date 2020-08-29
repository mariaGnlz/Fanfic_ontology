#!/usr/bin/bash/python3

from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer, sent_tokenize
from nltk.tag import pos_tag
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer
from fanfic_util import FanficCleaner
from fanfic_util import FanficHTMLHandler
from gensim import corpora
import pandas as pd
import numpy as np
import matplotlib.pyplot as ptl
from bs4 import BeautifulSoup

import string, html2text, pickle, gensim, sys, time, guidedlda

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
#FIC_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/typical_fic_paths.txt'
MODEL_NAME = 'model0' #default name
MODEL_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_models/'
DICTIONARY_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_dictionaries/'

#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR','VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives and verbs (all kinds) aka C
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adverbs and verbs (all kinds) aka B
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','UH', 'RP', 'IN', 'CC'] #nouns, adverbs and verbs (all kinds) aka BUH
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives, adverbs and verbs (all kinds) aka D
INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','UH', 'RP', 'IN', 'CC'] #nouns, adjectives, adverbs and verbs (all kinds) aka DUH
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
	en_stop.extend(INTERESTING_POS)
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

def use_guidedlda():
	fcleaner = FanficCleaner()
	print(fcleaner.get_fic_listing_path()) #debug
	fic_list = fcleaner.clean_fanfics_in_range(0,1000)
	fic_texts, fic_paths = zip(*fic_list)

	
	###Load trained guidedLDA model
	f = open(MODEL_PATH+MODEL_NAME+'.pickle','rb')
	guidedlda_model = pickle.load(f)
	f.close()

	"""
	###Load guidedLDA model dictionary
	print(MODEL_NAME+'_dictionary.pickle') #debug
	f = open(DICTIONARY_PATH + MODEL_NAME+'_dictionary.pickle', 'rb')
	dictionary = pickle.load(f)
	f.close()
	"""

	###Process fanfics
	start_time = time.time()

	processed_fics = process_text(fic_texts)
	#print(type(processed_fics), len(processed_fics[0]), type(processed_fics[0])) #debug


	###Top words

	###Create term-document matrix
	token_vectorizer = CountVectorizer(tokenizer=fic_tokenizev2, min_df=5, stop_words=UNINTERESTING_TOKENS, ngram_range=(1,4))

	data_vector = token_vectorizer.fit_transform(processed_fics[0])
	
	#print(fic_paths[0]) #debug

	vectors = guidedlda_model.transform(data_vector)
	#needs load vocab?
	
	topic_word = guidedlda_model.topic_word_
	for i, topic_dist in enumerate(topic_word):
		topic_words = np.array(data_vector)[np.argsort(topic_dist)][:-(n_top_words+1):-1]
		print('Topic {}: {}'.format(i, ' '.join(topic_words)))

	#print("topic: {} Document: {}".format(vectors[i].argmax(),', '.join(np.array(vocab)[list(reversed(X[i,:].argsort()))[0:5]])))
	
	#print(type(vectors), vectors.shape) #debug
	#print(len(data_vector)) #debug
	
	"""
	hits = 0
	i = 0
	for vector in vectors:
	#for i in range(len(data_vector)):
		#vector = ldamodel[corpus[i]] #returns topic probability ditribution for topic 0
		#vector = guidedlda_model.transform(data_vector[i])
		if hits == 0: 
			print(vector)
		#vectors.append(vector)
		if len(vector) == 2:
			fic_rating = fhandler.get_rating(fic_paths[i])
			if fic_rating == 'Explicit' or fic_rating == 'Mature':
				if vector[0][1] < vector[1][1]: hits += 1 #rated E, hit
				#else: print('Rated E, miss')
			else: 
				if vector[0][1] > vector[1][1]: hits += 1 #Not rated E, hit
		elif len(vector) ==1:
			fic_rating = fhandler.get_rating(fic_paths[i])
			if fic_rating == 'Explicit' or fic_rating == 'Mature':
				if vector[0][0] == 1: hits += 1 #rated E, hit
				#else: Rated E, miss

			else:
				if vector[0][0] == 0: hits += 1 #not rated E, hit
				#else: not rated E, miss
		else: 
			print(i)
			print(vector)

		i = i+1
	"""

	end_time = time.time()
	print('guidedLDA elapsed time: ',(end_time-start_time)/60,' minutes')

	#print(vectors)
	#print((hits/len(fic_texts))*100,'% hits	with ', MODEL_NAME)
	
def use_lda():
	fcleaner = FanficCleaner()
	print(fcleaner.get_fic_listing_path()) #debug
	fic_list = fcleaner.clean_fanfics_in_range(0,5000)
	fic_texts, fic_paths = zip(*fic_list)
	ldamodel = gensim.models.ldamodel.LdaModel.load(MODEL_PATH+MODEL_NAME+'.gensim')

	###LDA model
	start_time = time.time()

	processed_fics = process_text(fic_texts)

	model_dict = MODEL_NAME[4:len(MODEL_NAME)]
	dictionary = corpora.Dictionary.load(DICTIONARY_PATH+model_dict+'_dictionary.gensim')

	corpus = [dictionary.doc2bow(fic) for fic in processed_fics]
	
	fhandler = FanficHTMLHandler()
	#print(fic_paths[0]) #debug
	hits = 0
	#vectors = []
	for i in range(len(fic_texts)):
		vector = ldamodel[corpus[i]] #returns topic probability ditribution for topic 0
		#print(vector)
		#vectors.append(vector)
		if len(vector) == 2:
			fic_rating = fhandler.get_rating(fic_paths[i])
			if fic_rating == 'Explicit' or fic_rating == 'Mature':
				if vector[0][1] < vector[1][1]: hits += 1 #rated E, hit
				#else: print('Rated E, miss')
			else: 
				if vector[0][1] > vector[1][1]: hits += 1 #Not rated E, hit
		elif len(vector) ==1:
			fic_rating = fhandler.get_rating(fic_paths[i])
			if fic_rating == 'Explicit' or fic_rating == 'Mature':
				if vector[0][0] == 1: hits += 1 #rated E, hit
				#else: Rated E, miss

			else:
				if vector[0][0] == 0: hits += 1 #not rated E, hit
				#else: not rated E, miss
		else: 
			print(i)
			print(vector)

	end_time = time.time()
	print('LDA elapsed time: ',(end_time-start_time)/60,' minutes')

	#print(vectors)
	print((hits/len(fic_texts))*100,'% hits	with ', MODEL_NAME)

def use_lsi():
	fcleaner = FanficCleaner()
	print(fcleaner.get_fic_listing_path()) #debug
	fic_list = fcleaner.clean_fanfics_in_range(0,1000)
	fic_texts, fic_paths = zip(*fic_list)
	lsimodel = gensim.models.lsimodel.LsiModel.load(MODEL_PATH+MODEL_NAME+'.gensim')

	###LSI model
	start_time = time.time()

	processed_fics = process_text(fic_texts)

	model_dict = MODEL_NAME[4:len(MODEL_NAME)]
	dictionary = corpora.Dictionary.load(DICTIONARY_PATH+model_dict+'_dictionary.gensim')

	corpus = [dictionary.doc2bow(fic) for fic in processed_fics]
	
	fhandler = FanficHTMLHandler()
	#print(fic_paths[0]) #debug
	hits = 0
	#vectors = []
	for i in range(len(fic_texts)):
		vector = lsimodel[corpus[i]] #returns topic probability ditribution for topic 0
		#print(vector) #debug
		#vectors.append(vector)
		if len(vector) == 2:
			fic_rating = fhandler.get_rating(fic_paths[i])
			if fic_rating == 'Explicit' or fic_rating == 'Mature':
				if vector[0][1] < vector[1][1]: hits += 1 #rated E, hit
				#else: print('Rated E, miss')
			else: 
				if vector[0][1] > vector[1][1]: hits += 1 #Not rated E, hit
		else: print(i, vector)

	end_time = time.time()
	print('LSI elapsed time: ',(end_time-start_time)/60,' minutes')

	#print(vectors)
	print((hits/len(fic_texts))*100,'% hits	with ', MODEL_NAME)

def process_text(unprocessed_fics):

	#word_tokens = [word_tokenize(fic) for fic in unprocessed_fics]
	
	word_tokens = []
	for fic in unprocessed_fics:
		word_tokens.append(fic_tokenizev2(fic))
	
	
	
	#return [fic_tokenizev2(fic) for fic in unprocessed_fics]
	return word_tokens
	

if len(sys.argv) == 2:
	start_time = time.time()
	MODEL_NAME = (sys.argv[1]).strip()
	print(MODEL_NAME) #debug

	alg = MODEL_NAME.split('_')[0]
	#print(alg) #debug

	if alg == 'lda':
		use_lda()

	elif alg == 'lsi':
		use_lsi()

	elif alg == 'guidedLDA':
		use_guidedlda()

	else: print('Error: algorithm "',alg,'" not recognized')


else:
	print('Error. Correct usage: \ntopic_evaluate.py <MODEL_NAME>')
