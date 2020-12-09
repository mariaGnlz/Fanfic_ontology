#!/usr/bin/bash/python3

from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer, sent_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from gensim import corpora

import pandas as pd
import numpy as np
from fanfic_util import FanficGetter
import string, pickle, gensim, sys, time

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
RFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths.txt'
FFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths.txt'
EFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths.txt'

SAVE_TO_CSV = 'lda_evaluation.csv'

MODEL_NAME = 'model0.gensim' #default name
MODEL_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_models/'
DICTIONARY_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_dictionaries/'
NUM_TOPICS = 3

#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR','VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives and verbs (all kinds) aka C
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adverbs and verbs (all kinds) aka B
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','UH', 'RP', 'IN', 'CC'] #nouns, adverbs and verbs (all kinds) aka BUH
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives, adverbs and verbs (all kinds) aka D
INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','UH', 'RP', 'IN', 'CC'] #nouns, adjectives, adverbs and verbs (all kinds) aka DUH
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

def process_texts(unprocessed_fics):
	processed_fics = []
	for fic in unprocessed_fics:
		#Get lemmatized tokens
		tokens = fic_tokenizev1(fic)
		#tokens = fic_tokenizev2(fic)

		#Filter out stopwords
		stopwords = get_stopwords()

		word_tokens = [word for word in tokens if word not in stopwords]
		processed_fics.append(word_tokens)

	return processed_fics

def get_unfiltered_dataset():
	fanfic_getter = FanficGetter()

	## Fetch unfiltered dataset
	ufics = fanfic_getter.get_fanfics_in_range(0,5000)
	#ufics = fanfic_getter.get_fanfics_in_range(0,10000)

	ufic_texts = [fic.get_string_chapters() for fic in ufics]

	return ufic_texts

def get_RFE_dataset():
	fanfic_getter = FanficGetter()

	## Fetch RFE dataset
	fanfic_getter.set_fic_listing_path(EFIC_LISTING_PATH)
	efics = fanfic_getter.get_fanfics_in_list()

	fanfic_getter.set_fic_listing_path(FFIC_LISTING_PATH)
	ffics = fanfic_getter.get_fanfics_in_range(0,180)

	fanfic_getter.set_fic_listing_path(RFIC_LISTING_PATH)
	rfics = fanfic_getter.get_fanfics_in_range(0,220) # There are a lot of romance fanfics, so we're going to tone it down a bit

	rfe_fics = efics + ffics + rfics

	rfe_texts = [fic.get_string_chapters() for fic in rfe_fics]

	return rfe_texts

def compute_coherence_values(corpus, processed_texts, k, a, b):
	dictionary = corpora.Dictionary(corpus)
	corpus = [dictionary.doc2bow(fic) for fic in corpus]

	ldamodel = gensim.models.LdaMulticore(corpus=corpus, num_topics=k, id2word=dictionary, passes=20, alpha=a, eta=b, chunksize=100)
	#ldamodel = gensim.models.ldamodel.LdaModel.load(MODEL_PATH+MODEL_NAME+'.gensim')

	coherence_model_lda = gensim.models.coherencemodel.CoherenceModel(model=ldamodel, texts=processed_texts, dictionary=dictionary, coherence='c_v')

	return coherence_model_lda.get_coherence()
	
def use_lda():
	## Setting hyperparameters
	# Topics range
	min_topics = 2
	max_topics = 11
	step_size = 1
	topics_range = range(min_topics, max_topics, step_size)

	# Alpha
	alpha = list(np.arange(0.01, 1, 0.3))
	alpha.append('symmetric')
	alpha.append('asymmetric')

	# Beta
	beta = list(np.arange(0.01, 1, 0.3))
	beta.append('symmetric')

	# Validation sets
	print('Fetching and processing fanfics. . .')
	start_time = time.time()

	fic_texts = get_RFE_dataset()
	#processed_fics = get_unfiltered_dataset()

	processed_fics = process_texts(fic_texts)

	fic_datasets = [processed_fics[:int(len(processed_fics)*0.75)], processed_fics[int(len(processed_fics)*0.15):]]
	dataset_titles = ['75% dataset', '15% dataset']

	end_time = time.time()
	print("Fanfics fetched and processed. Elapsed time: ",(end_time-start_time)/60, "minutes")


	#Instantiate model for results
	model_results = {'Validation_Set': [], 'Topics': [], 'Alpha': [], 'Beta': [], 'Coherence': []}

	#Load dictionary	
	#model_dict = MODEL_NAME[4:len(MODEL_NAME)]
	#dictionary = corpora.Dictionary.load(DICTIONARY_PATH+model_dict+'_dictionary.gensim')


	print('Evaluating LDA model. . .')
	start_time = time.time()

	for i in range(len(fic_datasets)):
		print('Evaluating dataset ',i,' of ',len(fic_datasets))

		for k in topics_range:
			for a in alpha:
				for b in beta:

					#Compute coherence score
					cv = compute_coherence_values(fic_datasets[i], processed_fics, k, a, b)

					#Save results
					model_results['Validation_Set'].append(dataset_titles[i])
					model_results['Topics'].append(k)
					model_results['Alpha'].append(a)
					model_results['Beta'].append(b)
					model_results['Coherence'].append(cv)


	end_time = time.time()
	print('...done. Evaluation time: ',(end_time-start_time)/60,' minutes')

	print('Saving evaluation results to CSV. . .')
	pd.DataFrame(model_results).to_csv(SAVE_TO_CSV, mode='a', index=False)
	print('...done')


### MAIN ###
"""
if len(sys.argv) == 2:
	start_time = time.time()
	MODEL_NAME = (sys.argv[1]).strip()
	print(MODEL_NAME) #debug

	alg = MODEL_NAME.split('_')[0]
	#print(alg) #debug

	use_lda()


else:
	print('Error. Correct usage: \ntopic_evaluate.py <MODEL_NAME>')
"""
use_lda()
