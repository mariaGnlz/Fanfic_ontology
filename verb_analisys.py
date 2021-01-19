#!/bin/bash/python3

import sys, time, pandas, numpy, nltk
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.collocations import *
import nltk
from sklearn.cluster import KMeans
from gensim.models import Word2Vec

from NER_tagger import NERTagger
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
ADJECTIVE_TAGS = ['JJ', 'JJR', 'JJS']
COLOURS = ['r','b','y']

### FUNCTIONS ###
def get_lemma(word):
	lemma = wordnet.morphy(word)

	if lemma is None:
		return word
	else: return lemma

STOPWORDS = [get_lemma(word) for word in stopwords.words('english')]
BIGRAM_STOPWORDS = STOPWORDS + ['wa','be','n','t','ha','ve','n’t',"n't",'’ve',"'ve","'re",'’s',"'s","’m", "'m", ',', '’','"','“','”','*','.',':','...','…',"'",'-','~','_','!','/','\\','[',']']
STOPWORDS.extend(['wa','be','n','t','ha','ve','n’t',"n't",'’ve',"'ve", ',', '’','"','“','”','*','.',':','...','…',"'",'-','~','_','!','/','\\','[',']', 'say','go','look','say','make','get','know','see','take','want'])
#STOPWORDS.extend(['wa','be','n','t','ha','ve','n’t',"n't",'’ve',"'ve", ',', '’','"','“','”','*','.',':','...','…',"'",'-','~','_','!','/','\\','[',']'])



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

def get_lemmatized_adjectives(sentence):
	tagged_sent = pos_tag(word_tokenize(sentence))
	#print(tagged_sent) #debug

	adjs = []
	for word, pos in tagged_sent:
		word = get_lemma(word)
		if pos in ADJECTIVE_TAGS and word not in STOPWORDS:
			#print(word, pos) #debug
			adjs.append(word)

	return adjs

def get_sentiment(sentences):
	#fic_ids = sentence_data['ficID'] #get number of different fanfics in database
	sentiment_count = 0
	
	for sentiment in sentences:
		#print(sentiment) #debug

		if sentiment == 'Very positive': sentiment_count += 2
		elif sentiment == 'Positive': sentiment_count += 1
		elif sentiment == 'Neutral': sentiment_count += 1
		elif sentiment == 'Negative': sentiment_count -= 1
		elif sentiment == 'Very negative': sentiment_count -= 2

	if len(sentences) == 0: return 0
	else: return sentiment_count/len(sentences)

def get_RFE_sentences(sentence_data):
	#fic_ids = sentence_data['ficID'] #get number of different fanfics in database

	r_data = sentence_data[sentence_data['ficDataset'] == 'ROMANCE']
	f_data = sentence_data[sentence_data['ficDataset'] == 'FRIENDSHIP']
	e_data = sentence_data[sentence_data['ficDataset'] == 'ENEMY']


	return r_data, f_data, e_data

def find_characters(fic_sentences, fic_id, char_id):
	characters_data = pandas.read_csv(CHARACTERS_TO_CSV)

	fic_characters = characters_data[characters_data['ficID'] == fic_id]
	char_data = fic_characters[fic_characters['canonID'] == char_id]
	#print(char_data) #debug

	char_clusters = char_data['clusterID']
	char_ners = char_data['nerID']

	all_clusters = []
	for cluster_list in char_clusters:
		cluster_list = cluster_list.strip('[]')
		#print('cluster list: ',cluster_list) #debug

		if ',' in cluster_list:
			clusters = [int(cluster_id) for cluster_id in cluster_list.split(',')]
			#print(', in cluster: ',clusters) #debug
			all_clusters.extend(clusters)

		elif '' != cluster_list: all_clusters.append(int(cluster_list))
			

	all_clusters = list(set(all_clusters)) #remove duplicates
	#print('clusters: ', all_clusters) #debug


	all_ners = []
	for ner_list in char_ners:
		ner_list = ner_list.strip('[]')
		#print('ner list: ',ner_list) #debug

		if ',' in ner_list:
			ners = [int(ner_id) for ner_id in ner_list.split(',')]
			#print(', in ner: ',ners) #debug
			all_ners.extend(ners)

		elif '' != ner_list: all_ners.append(int(ner_list))
	
	character_sentences = []
	if len(all_clusters) > 0:
		for cluster in all_clusters:
			for index, sentence in fic_sentences.iterrows():
				sen_clusters = sentence['Clusters'].strip('[]')
				try: sen_clusters = [int(cluster_id) for cluster_id in sen_clusters.split(',') if cluster_id != '']
				except ValueError as e:
					print('row ',index,e) #in case there are incorrectly formatted cells

				#print(sen_clusters) #debug

				if cluster in sen_clusters: character_sentences.append((sentence['Verbs'],sentence['Sentiment']))

		#print(character_sentences[:10])#debug

	
	if len(all_ners) > 0:
		for ner in all_ners:
			for index, sentence in fic_sentences.iterrows():
				sen_ners = sentence['nerIDs'].strip('[]')
				try: sen_ners = [int(ner_id) for ner_id in sen_ners.split(',') if ner_id != '']
				except ValueError as e:
					print('row ',index,e) #in case there are incorrectly formatted cells

				#print(sen_ners) #debug

				if ner in sen_ners: character_sentences.append((sentence['Verbs'],sentence['Sentiment']))

	#print(character_sentences) #debug
	return character_sentences

def check_verb_frequencies(sentences):
	verbs = [get_lemmatized_verbs(sentence) for sentence in sentences]

	all_verbs = []
	for sentence in verbs:
		for verb in sentence: all_verbs.append(verb)

	#print(type(sentence_verbs[0]), sentence_verbs[0]) #debug

	freq = nltk.FreqDist(all_verbs)
	freq.plot(50)

	return freq

def check_adjective_frequencies(sentences):
	adjectives = [get_lemmatized_adjectives(sentence) for sentence in sentences]

	all_adjectives = []
	for sentence in adjectives:
		for adjective in sentence: all_adjectives.append(adjective)

	#print(type(all_adjectives[0]), all_adjectives[0]) #debug

	freq = nltk.FreqDist(all_adjectives)
	freq.plot(50)

	return freq

def check_ngram_frequencies(sentences, dataset):
	single_string = ''
	for sentence in sentences: single_string += sentence+(' ')

	finder2 = BigramCollocationFinder.from_words(single_string.split(), window_size = 3)
	finder2.apply_word_filter(lambda w: w in BIGRAM_STOPWORDS)
	finder2.apply_freq_filter(2)

	finder3 = TrigramCollocationFinder.from_words(single_string.split(), window_size = 3)
	finder3.apply_word_filter(lambda w: w in STOPWORDS)
	finder3.apply_freq_filter(2)

	bigram_measures = nltk.collocations.BigramAssocMeasures()
	collocations2 = finder2.nbest(bigram_measures.pmi, 20)
	#collocations2 = finder2.nbest(bigram_measures.likelihood_ratio, 20)
	colloc_strings2 = [w1+' '+w2 for w1, w2 in collocations2]

	trigram_measures = nltk.collocations.TrigramAssocMeasures()
	collocations3 = finder3.nbest(trigram_measures.pmi, 20)
	#collocations3 = finder3.nbest(trigram_measures.likelihood_ratio, 20)
	colloc_strings3 = [w1+' '+w2+' '+w3 for w1, w2, w3 in collocations3]

	print('\n\n===== Brigram collocations of '+dataset+' dataset =====\n\n')
	print(colloc_strings2)
	#print(finder2.score_ngrams(bigram_measures.pmi))
	print('\n\n===== Trigram collocations of '+dataset+' dataset =====\n\n')
	print(colloc_strings3)
	#print(finder3.score_ngrams(trigram_measures.pmi))

	return collocations3, collocations3

def get_data_on_pairing_sentences(sentence_data, fic_ids, canon_characters_ids, dataset):
	#print(len(fic_ids), fic_ids[:10]) #debug

	character_tuples = []
	for fic_id in fic_ids:
		fic_sentences = sentence_data[sentence_data['ficID'] == fic_id]

		for char_id in canon_characters_ids:
			sens = find_characters(fic_sentences, fic_id, char_id)
			character_tuples.extend(sens)

	#print(character_sentences[:10]) #debug
	sentences, sentiments = list(zip(*character_tuples))

	duplicates = []
	sentiments = []
	for sentence, sentiment in character_tuples:
		if sentences.count(sentence) > 1: 
			duplicates.append(sentence)
			sentiments.append(sentiment)

	print('Sentiment in '+dataset+' sentences: ',get_sentiment(sentiments))
	check_verb_frequencies(duplicates)
	check_adjective_frequencies(duplicates)
	check_ngram_frequencies(duplicates, dataset)

def substract_sets(set1, set2):
	common_words = []
	for word, freq in set1.items():
		for w, f in set2.items():
			if word == w: common_words.append(word)

	for word in common_words:
		set1.pop(word)
		set2.pop(word)

	return set1, set2


def substract_three_sets(set1, set2, set3):
	common_words = []
	for word, freq in set1.items():
		for w, f in set2.items():
			if word == w: common_words.append(word)

	for word, freq in set1.items():
		for w, f in set3.items():
			if word == w and w not in common_words: common_words.append(word) 

	for word, freq in set3.items():
		for w, f in set2.items():
			if word == w and w not in common_words: common_words.append(word) 

	for word in common_words:
		set1.pop(word)
		set2.pop(word)
		set3.pop(word)

	return set1, set2, set3

def plot_stuff(sentences, words):
	#words = [word for word, f in freqs]
	vectorizer= Word2Vec(sentences, min_count=10)

	print(type(vectorizer.wv)) #debug

	vectorized_data = vectorizer.wv
	#vectorizer_data = Word2Vec.build_vocab_from_freq(word_freq=freqs)
	#vectorizer_data = vectorizer[vectorizer.vocab]
	#vectorizer = TfidfVectorizer(tokenizer=get_lemmatized_verbs, stop_words=STOPWORDS, max_df=0.99, min_df=0.01)
	#vectorized_data = vectorizer.fit_transform(sentences)


	km_model = KMeans(n_clusters=3, init='k-means++', n_init=5)
	data = km_model.fit_transform(vectorized_data)
	centroids = km_model.cluster_centers_

	#scatter_points = model.fit_transform(vectorized_data.toarray())
	kmean_indices = km_model.fit_predict(vectorized_data)

	x_axis = [x[0] for x in vectorized_data]
	y_axis = [y[1] for y in vectorized_data]

	plt.scatter(x_axis, y_axis, c=[COLOURS[d] for d in kmean_indices])

	plt.show()


### MAIN ###
sentence_data = pandas.read_csv(SENTENCES_TO_CSV)

r_sens, f_sens, e_sens = get_RFE_sentences(sentence_data)

#r_sens = r_sens[:40]
#f_sens = f_sens[:40]
#e_sens = e_sens[:40]

r_verbs_freq = check_verb_frequencies(r_sens['Verbs'])
r2_collocations, r3_collocations = check_ngram_frequencies(r_sens['Verbs'], 'Romance')
r_adjs_freq = check_adjective_frequencies(r_sens['Verbs'])
r_sentiment = get_sentiment(r_sens['Sentiment'])

f_verbs_freq = check_verb_frequencies(r_sens['Verbs'])
f_adjs_freq = check_adjective_frequencies(f_sens['Verbs'])
f2_collocations, f3_collocations = check_ngram_frequencies(f_sens['Verbs'], 'Friendship')
f_sentiment = get_sentiment(f_sens['Sentiment'])

e_verbs_freq = check_verb_frequencies(r_sens['Verbs'])
e_adjs_freq = check_adjective_frequencies(e_sens['Verbs'])
e2_collocations, e3_collocations = check_ngram_frequencies(e_sens['Verbs'], 'Enemy')
e_sentiment = get_sentiment(e_sens['Sentiment'])

#r_verbs, f_verbs, e_verbs = substract_three_sets(r_verbs_freq, f_verbs_freq, e_verbs_freq)

#r_verbs_freq.plot(50)
#f_verbs_freq.plot(50)
#e_verbs_freq.plot(50)

#find_characters(sentence_data, 70, 4) #debug
#find_characters(sentence_data, 70, 8) #debug

"""
#canon_characters_ids = range(40)
canon_characters_ids = [4,8] #debug, trying to find Aziraphale and Crowley's sentences
#print(canon_characters_ids) #debug
romance_fic_ids = list(set(r_sens['ficID']))
get_data_on_pairing_sentences(sentence_data, romance_fic_ids, canon_characters_ids, 'romance ineffable husbands sentences')

friendship_fic_ids = list(set(f_sens['ficID']))
get_data_on_pairing_sentences(sentence_data, friendship_fic_ids, canon_characters_ids, 'friendship ineffable husbands sentences')

enemy_fic_ids = list(set(e_sens['ficID']))
get_data_on_pairing_sentences(sentence_data, enemy_fic_ids, [4,14], 'enemy aziraphale+gabriel sentences')
"""

"""
print('Sentiment of romance fics: ', r_sentiment,'\nSentiment of frienship fics: ',f_sentiment,'\nSentiment of enemy fics: ',e_sentiment)

r_sfreq, e_sfreq = substract_sets(r_freq, e_freq)
r_sfreq, f_sfreq = substract_sets(r_freq, f_freq)
#e_sfreq, f_sfreq = substract_sets(e_sfreq, f_freq)


words = all_freqs.keys()

#print(len(all_freqs), type(all_freqs)) #debug

sentences = sentence_data['Verbs']
#plot_stuff(sentences, words)
"""








