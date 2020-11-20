#!/usr/bin/bash/python3

from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer, sent_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim import corpora

import pandas as pd
import matplotlib.pyplot as ptl
from fanfic_util import FanficGetter, Fanfic

import string, html2text, pickle, gensim, sys, time

### VARIABLES ###
#FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths.txt'
RFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths.txt'
FFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths.txt'
EFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths.txt'

MODEL_NAME = 'model0.gensim' #default name
MODEL_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_models/'
DICTIONARY_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_dictionaries/'
NUM_TOPICS = 3

#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR','VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives and verbs (all kinds) aka C
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adverbs and verbs (all kinds) aka B
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'UH'] #nouns, adverbs and verbs (all kinds) aka BUH
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives, adverbs and verbs (all kinds) aka D
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'UH'] #nouns, adjectives, adverbs and verbs (all kinds) aka DUH
INTERESTING_POS = ['JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','UH', 'RP', 'IN', 'CC'] #nouns, adjectives, adverbs and verbs (all kinds) aka DUH2
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS'] #nouns, adjectives and adverbs (all kinds)

UNINTERESTING_POS = ['PRP','PRP$','POS','CC','CD','TO','DT','IN']

### FUNCTIONS ###

def get_lemma(word):
	lemma = wordnet.morphy(word)

	if lemma is None:
		return word
	else: return lemma

def get_stopwords():
	# Tokenize and lemmatize stopwords
	stop = stopwords.words('english')
	#tokenizer = RegexpTokenizer(r'\w+')
	#stop = [tokenizer.tokenize(word) for word in stop]
	stop = [word_tokenize(word) for word in stop]

	words = []
	for item in stop:
		if type(item) == list: 
			for w in item: words.append(w)

		else: words.append(word)


	words = [get_lemma(word) for word in words]
	#print(words[:10]) #debug

	words.extend(["’","“","”","'","``","","''","_","-","--",";",":",".",",","?","!","*","–","‘","(",")"])
	return words


def fic_tokenizev1(fic):
	sent_tokens = sent_tokenize(fic)
	#tokenizer = RegexpTokenizer(r'\w+')
	#word_tokens = [tokenizer.tokenize(sent) for sent in sent_tokens]
	word_tokens = [word_tokenize(sent) for sent in sent_tokens]

	words = []
	for item in word_tokens:
		if type(item) == list:
			for w in item: words.append(w)

		else: words.append(word)
	

	processed_tokens = [get_lemma(word) for word in words]

	return processed_tokens

def fic_tokenizev2(fic):
	sent_tokens = sent_tokenize(fic)
	#tokenizer = RegexpTokenizer(r'\w+')
	#pos_tokens = [pos_tag(tokenizer.tokenize(sent)) for sent in sent_tokens]
	pos_tokens = [pos_tag(word_tokenize(sent)) for sent in sent_tokens]

	interesting_words = []
	for token in pos_tokens:
		for word, pos in token:
			#word = word.strip()
			if pos not in UNINTERESTING_POS: interesting_words.append(word)

	processed_tokens = [get_lemma(word) for word in interesting_words]

	return processed_tokens

def process_text(unprocessed_fics):
	processed_fics = []
	for fic in unprocessed_fics:
		#Get lemmatized tokens
		#tokens = fic_tokenizev1(fic)
		tokens = fic_tokenizev2(fic)

		#Filter out stopwords
		stopwords = get_stopwords()

		word_tokens = [word for word in tokens if word not in stopwords]
		processed_fics.append(word_tokens)

	return processed_fics
	

### MAIN ###

if len(sys.argv) == 2:
	start_time = time.time()
	MODEL_NAME = (sys.argv[1]).strip()
	print(MODEL_NAME) #debug

	
	print('Fetching fic texts...')
	start = time.time()
	
	getter = FanficGetter()

	getter.set_fic_listing_path(EFIC_LISTING_PATH)
	efics = getter.get_fanfics_in_list()

	getter.set_fic_listing_path(FFIC_LISTING_PATH)
	ffics = getter.get_fanfics_in_range(0,180)

	getter.set_fic_listing_path(RFIC_LISTING_PATH)
	rfics = getter.get_fanfics_in_range(0,220) # There are a lot of romance fanfics, so we're going to tone it down a bit

	fics = efics + ffics + rfics


	fanfic_texts = [fic.get_string_chapters() for fic in fics]
	#print(len(fics)) #debug
	#print(len(fanfic_texts), len(name_labels)) #debug

	end = time.time()

	print("...fics fetched. Elapsed time: ",(end-start)/60," mins")


	print('Preprocessing fanfics and creating dictionaries...')
	start_time = time.time()

	processed_fics = process_text(fanfic_texts)
	#print(type(processed_fics), processed_fics[0][:10]) #debug

	dictionary = corpora.Dictionary(processed_fics)
	corpus = [dictionary.doc2bow(fic) for fic in processed_fics]

	#pickle.dump(corpus, open('corpus.pkl', 'wb'))
	dictionary.save(DICTIONARY_PATH+MODEL_NAME+'_dictionary.gensim')

	end_time = time.time()
	print('Processing elapsed time: ',(end_time-start_time)/60,' minutes')
	
	start_time = time.time()
	print('Training LDA model. . .')
	ldamodel = gensim.models.ldamodel.LdaModel(corpus=corpus, num_topics=NUM_TOPICS, id2word=dictionary, passes=20)
	ldamodel.save(MODEL_PATH +'lda_'+MODEL_NAME+'.gensim')
	coherence = gensim.models.coherencemodel.CoherenceModel(model=ldamodel, texts=processed_fics, dictionary=dictionary, coherence='c_v')

	end_time = time.time()
	print('...LDA elapsed time: ',(end_time-start_time)/60,' minutes')

	print('LDA Coherence score: ', coherence.get_coherence())
	topics = ldamodel.print_topics(num_words=10)

	print('Topics in LDA model:')
	for topic in topics: print(topic)


else:
	print('Error. Correct usage: \ntopic.py <MODEL_NAME>')
