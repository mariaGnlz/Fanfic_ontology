#!/usr/bin/bash/python3

from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer, sent_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from sklearn import metrics
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from fanfic_util import FanficGetter, Fanfic
from NER_tagger import NERTagger

from matplotlib import pyplot as plt
from pprint import pprint
import string, time, html2text
import numpy as np

### VARIABLES ###
#FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
RFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths.txt'
FFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths.txt'
EFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths.txt'

COLOURS = ["r", "b", "y", "b", "g"]
NUM_CLUSTERS = 3

INTERESTING_POS = ['NN', 'NNS', 'JJ', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #I choose to only use nouns, adjectives and verbs (all kinds of verbs)
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR']

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

	words.extend(["'","``","","''","_","-","--",";",":","...","*","–","‘","(",")","'m"])
	return words


def fic_tokenizev1(fic):
	sent_tokens = sent_tokenize(fic)
	#tokenizer = RegexpTokenizer(r'\w+')
	word_tokens = [word_tokenize(sen) for sen in sent_tokens]

	#print(character_mentions) #debug
	
	#Remove character names from text
	words = []
	for item in word_tokens:
		if type(item) == list:
			for w in item: words.append(w)

		else: words.append(word)

	#Lemmatize words
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
			if pos in INTERESTING_POS: interesting_words.append(word)

	processed_tokens = [get_lemma(word) for word in interesting_words]

	return processed_tokens

def remove_characters(fic_texts):
	ner_tagger = NERTagger()
	
	for text in fic_texts:
		sent_tokens = sent_tokenize(text)
		pos_tokens = [pos_tag(word_tokenize(sent)) for sent in sent_tokens]
		character_mentions = ner_tagger.parse(pos_tokens)

		for name, _ in character_mentions.items(): text = text.replace(name, '')

	return 	fic_texts

def cluster_texts(texts, name_labels):
	#print(texts[0][:100]) #debug

	print("Creating stopwords and removing character names from texts...")
	start = time.time()

	stop_words = get_stopwords()
	#texts = [remove_characters(text) for text in texts]

	end = time.time()
	print("...done in ", (end-start)/60," mins")

	print("Creating vectorizer, transforming texts to tf-idf coordinates...")
	start = time.time()
	#vectorizer = TfidfVectorizer(tokenizer=fic_tokenizev1, stop_words=stop_words, max_df=0.5, min_df=0.3, lowercase=True)
	vectorizer = TfidfVectorizer(tokenizer=fic_tokenizev2, stop_words=stop_words, max_df=0.5, min_df=0.3, lowercase=True)

	#print(type(texts),type(texts[0])) #debug
	vectorized_data = vectorizer.fit_transform(texts)
	#print(vectorizer.get_feature_names()) #debug

	end = time.time()
	print("...done in ", (end-start)/60," mins")

	print("Creating the K-Means model and fitting data..")
	start = time.time()
	k_labels = np.unique(name_labels).shape[0]
	km_model = KMeans(n_clusters=k_labels, init='k-means++', n_init=10)

	data = km_model.fit_transform(vectorized_data)
	centroids = km_model.cluster_centers_
	#print(len(data)) #debug
	#print(centroids) #debug

	end = time.time()
	print("...done in ", (end-start)/60, "mins")
	print("n_samples: %d, n_features: %d" % data.shape)
	
	print("\n === Metrics ===")
	print("Homogeneity: %0.3f" % metrics.homogeneity_score(name_labels, km_model.labels_))
	print("Completeness: %0.3f" % metrics.completeness_score(name_labels, km_model.labels_))
	print("V-measure: %0.3f" % metrics.v_measure_score(name_labels, km_model.labels_))
	print("Adjusted Rand-Index: %.3f" % metrics.adjusted_rand_score(name_labels, km_model.labels_))
	print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(data, km_model.labels_, sample_size=100))


	print("\nTop terms per cluster:")
	order_centroids = km_model.cluster_centers_.argsort()[:, ::-1]
	terms = vectorizer.get_feature_names()
	for i in range(k_labels):
		print('Cluster %d:' % i)
		all_terms = ''
		for j in order_centroids[i, :10]: all_terms += terms[j]+', '
		print(all_terms+'\n')
 

	### Plot the data

	model = PCA(n_components=2)
	scatter_points = model.fit_transform(vectorized_data.toarray())
	kmean_indices = km_model.fit_predict(vectorized_data)

	x_axis = [x[0] for x in scatter_points]
	y_axis = [y[1] for y in scatter_points]

	plt.scatter(x_axis, y_axis, c=[COLOURS[d] for d in kmean_indices])

	plt.show()



### MAIN ###

print("Fetching fic texts...")
start = time.time()

getter = FanficGetter()

getter.set_fic_listing_path(EFIC_LISTING_PATH)
efics = getter.get_fanfics_in_list()
elabels = ['enemy'] * len(efics)

getter.set_fic_listing_path(FFIC_LISTING_PATH)
ffics = getter.get_fanfics_in_range(0,180)
flabels = ['friendship'] * len(ffics)

getter.set_fic_listing_path(RFIC_LISTING_PATH)
rfics = getter.get_fanfics_in_range(0,220) # There are a lot of romance fanfics, so we're going to tone it down a bit
rlabels = ['romance'] * len(rfics)

fics = efics + ffics + rfics
name_labels = elabels + flabels + rlabels


fanfic_texts = [fic.get_string_chapters() for fic in fics]
#print(len(fics)) #debug
#print(len(fanfic_texts), len(name_labels)) #debug

end = time.time()

print("...fics fetched. Elapsed time: ",(end-start)/60," mins")

cluster_texts(fanfic_texts, name_labels)

