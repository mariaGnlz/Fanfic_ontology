#!/bin/bash/python3

import sys, time, pandas, numpy, nltk
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from sklearn.cluster import KMeans

from NER_tagger_v3 import NERTagger
from fanfic_util import FanficGetter, FanficHTMLHandler, Fanfic

### VARIABLES ###
CHARACTERS_TO_CSV = '/home/maria/Documents/Fanfic_ontology/fic_characters.csv'
SENTENCES_TO_CSV = '/home/maria/Documents/Fanfic_ontology/fic_sentences.csv'
CANON_DB = '/home/maria/Documents/Fanfic_ontology/canon_characters.csv'
#ERRORLOG = '/home/maria/Documents/Fanfic_ontology/TFG_logs/ner_and_sen_extraction_v2_errorlog.txt'

ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths_shortened.txt'
FRIENDSHIP_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths_shortened.txt'
ENEMY_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths3.txt'

VERB_TAGS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']

### FUNCTIONS ###
def get_lemma(word):
	lemma = wordnet.morphy(word)

	if lemma is None:
		return word
	else: return lemma

STOPWORDS = [get_lemma(word) for word in stopwords.words('english')]
STOPWORDS.extend(['wa','be','n','ha','ve',"'nt","'ve","'re","'s", "'m", ',', '’','"','“','”','.',':','...','…',"'",'-','_'])

def get_lemmatized_verbs(sentence):
	tagged_sent = pos_tag(word_tokenize(sentence))
	#print(tagged_sent) #debug

	verbs = []
	for word, pos in tagged_sent:
		word = get_lemma(word)
		if pos in VERB_TAGS and word not in STOPWORDS:
			#print(word, pos) #debug
			verbs.append(word)

	return verbs

def normalize_sentiment(fic_sentiments):
	sentiment_count = 0
	
	for sentiment in fic_sentiments:
		#print(sentiment) #debug

		if sentiment == 'Very positive': sentiment_count += 2
		elif sentiment == 'Positive': sentiment_count += 1
		elif sentiment == 'Negative': sentiment_count -= 1
		elif sentiment == 'Very negative': sentiment_count -= 2

	return sentiment_count

def plot_stuff(sentences):
	vectorizer = TfidfVectorizer(tokenizer=get_lemmatized_verbs, stop_words=STOPWORDS, max_df=0.9, min_df=0.1, lowercase=True)
	vectorized_data = vectorizer.fit_transform(sentences)


	km_model = KMeans(n_clusters=3, init='k-means++', n_init=10)
	data = km_model.fit_transform(vectorized_data)
	centroids = km_model.cluster_centers_

	#scatter_points = model.fit_transform(vectorized_data.toarray())
	kmean_indices = km_model.fit_predict(vectorized_data)

	x_axis = [x[0] for x in vectorized_data]
	y_axis = [y[1] for y in vectorized_data]

	plt.scatter(x_axis, y_axis, c=[COLOURS[d] for d in kmean_indices])

	plt.show()

def get_RFE_sentences(sentence_data):
	#fic_ids = sentence_data['ficID'] #get number of different fanfics in database

	r_data = sentence_data[sentence_data['ficDataset'] == 'ROMANCE']
	f_data = sentence_data[sentence_data['ficDataset'] == 'FRIENDSHIP']
	#e_data = sentence_data[sentence_data['ficDataset'] == 'ENEMY']

	r_sentences = r_data['Verbs']
	f_sentences = f_data['Verbs']
	#e_sentences = e_data['Verbs']

	r_verbs = [get_lemmatized_verbs(sentence) for sentence in r_sentences]
	f_verbs = [get_lemmatized_verbs(sentence) for sentence in f_sentences]
	#e_verbs = [get_lemmatized_verbs(sentence) for sentence in e_sentences]

	all_r_verbs = []
	all_f_verbs = []
	#all_e_verbs = []
	for sentence in r_verbs:
		for verb in sentence: all_r_verbs.append(verb)
	for sentence in f_verbs:
		for verb in sentence: all_f_verbs.append(verb)
	#for sentence in e_verbs:
	#	for verb in sentence: all_e_verbs.append(verb)

	#print(type(sentence_verbs[0]), sentence_verbs[0]) #debug

	return all_r_verbs, all_f_verbs

def find_characters(fic_sentences, fic_id, char1_id, char2_id):
	characters_data = pandas.read_csv(CHARACTERS_TO_CSV)

	fic_characters = characters_data[characters_data['ficID'] == fic_id]]

	char1_clusters = fic_characters[fic_characters['canonID'] == char1_id]['clusterID']
	char2_clusters = fic_characters[fic_characters['canonID'] == char2_id]['clusterID']

	if len(char1_clusters) > 0:
		indexes = []
		for cluster in char1_clusters:
			
			

	char2_sentences = fic_sentences[char2_id in fic_sentences['clusterID']]

	

		

def subtraction_of_sets(set1, set2):
	common_words = []
	for word, freq in set1.items():
		for w, f in set2.items():
			if word == w: common_words.append(word)

	for word in common_words:
		set1.pop(word)
		set2.pop(word)

	return set1, set2


### MAIN ###
sentence_data = pandas.read_csv(SENTENCES_TO_CSV)

r_verbs, f_verbs = get_RFE_sentences(sentence_data)

r_freq = nltk.FreqDist(r_verbs)
f_freq = nltk.FreqDist(f_verbs)
#e_freq = nltk.FreqDist(e_verbs)




r_freq.plot(50)
f_freq.plot(50)
#e_freq.plot(50)








