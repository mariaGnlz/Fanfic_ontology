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
from gensim import corpora
import pandas as pd
import matplotlib.pyplot as ptl
from bs4 import BeautifulSoup
from fanfic_util import FanficGetter

import string, html2text, pickle, gensim, sys, time

### VARIABLES ###
#FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
FIC_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/typical_fic_paths_5000nme.txt'
#FIC_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/typical_fic_paths_10000nme.txt'
MODEL_NAME = 'model0.gensim' #default name
MODEL_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_models/'
DICTIONARY_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_dictionaries/'
COLOURS = ["r", "b", "y", "b", "g"]
NUM_TOPICS = 2

INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR','VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives and verbs (all kinds) aka C
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adverbs and verbs (all kinds) aka B
#INTERESTING_POS = ['NN', 'NNS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'UH'] #nouns, adverbs and verbs (all kinds) aka BUH
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #nouns, adjectives, adverbs and verbs (all kinds) aka D
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'UH'] #nouns, adjectives, adverbs and verbs (all kinds) aka DUH
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','UH', 'RP', 'IN', 'CC'] #nouns, adjectives, adverbs and verbs (all kinds) aka DUH2
#INTERESTING_POS = ['NN', 'NNS', 'JJ', 'JJS', 'JJR', 'RB', 'RBR', 'RBS'] #nouns, adjectives and adverbs (all kinds)

UNINTERESTING_TOKENS = ['be', 'are', 'wasn', 'wa', 'have', 'say', 'do', 'don', 'get', 're', 'll', 've', 'd', 'm', 's', 't','_']

### FUNCTIONS ###

def get_fanfics_in_range(start, end): #gets the paths to the fics, opens them
                   #and stores their text in a list
	paths_file = open(FIC_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()
	fic_paths = fic_paths[start:end]

	untagged_fics = []
	#fic_nums = []
	for path in fic_paths:
		text = open(path, 'r').read()
		untagged_fics.append(text)
		#fic_nums.append(num_fic)

	#print(untagged_fics[0]) #debug
	#tagged_fics = tag_fics(untagged_fics)

	#return #zip(tagged_fics, fic_nums)
	return untagged_fics

def get_fanfics(): #gets the paths to the fics, opens them
                   #and stores their text in a list
	paths_file = open(FIC_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()

	untagged_fics = []
	#fic_nums = []
	for path in fic_paths:
		text = open(path, 'r').read()
		untagged_fics.append(text)
		#fic_nums.append(num_fic)

	#print(untagged_fics[0]) #debug
	#tagged_fics = tag_fics(untagged_fics)

	#return #zip(tagged_fics, fic_nums)
	return untagged_fics

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

def process_text(unprocessed_fics):

	#word_tokens = [word_tokenize(fic) for fic in unprocessed_fics]
	
	word_tokens = []
	for fic in unprocessed_fics:
		word_tokens.append(fic_tokenizev2(fic))
	
	
	
	#return [fic_tokenizev2(fic) for fic in unprocessed_fics]
	return word_tokens
	
def plot_stuff():
	vectorizer = CountVectorizer(min_df=5, max_df=0.9)

	#print(processed_fics[0][0])
	data_vectorized = [vectorizer.fit_transform(fic) for fic in processed_fics]

	svd = TruncatedSVD(n_components=2)
	documents_2d = svd.fit_transform(data_vectorized)
 
	df = pd.DataFrame(columns=['x', 'y', 'document'])
	df['x'], df['y'], df['document'] = documents_2d[:,0], documents_2d[:,1], 	range(len(processed_fics))
	df.plot(kind='scatter', x='x', y='y')
	plt.show()

	"""
	source = ColumnDataSource(ColumnDataSource.from_df(df))
	labels = LabelSet(x="x", y="y", text="document", y_offset=8,
                  text_font_size="8pt", text_color="#555555",
                  source=source, text_align='center')
 
	plot = figure(plot_width=600, plot_height=600)
	plot.circle("x", "y", size=12, source=source, line_color="black", fill_alpha=0.8)
	plot.add_layout(labels)
	show(plot, notebook_handle=True)

	"""
### MAIN ###

if len(sys.argv) == 2:
	start_time = time.time()
	MODEL_NAME = (sys.argv[1]).strip()
	print(MODEL_NAME) #debug

	#fanfic_texts = get_fanfics()
	fanfic_getter = FanficGetter()
	fanfic_getter.set_txt_fic_listing_path(FIC_LISTING_PATH)
	fanfic_texts = fanfic_getter.get_all_txt_fanfics()

	#fanfic_texts = ["This is the first document.", "This document is the second document.", "And this is the third one.", "Is this the first document?"]
	#print(len(fanfic_texts)) #debug

	###Processing fanfics
	start_time = time.time()

	processed_fics = process_text(fanfic_texts)
	#print(type(processed_fics)) #debug

	dictionary = corpora.Dictionary(processed_fics)
	corpus = [dictionary.doc2bow(fic) for fic in processed_fics]

	#pickle.dump(corpus, open('corpus.pkl', 'wb'))
	dictionary.save(DICTIONARY_PATH+MODEL_NAME+'_dictionary.gensim')

	end_time = time.time()
	print('Processing elapsed time: ',(end_time-start_time)/60,' minutes')
	
	###LDA model
	start_time = time.time()
	ldamodel = gensim.models.ldamodel.LdaModel(corpus=corpus, num_topics=NUM_TOPICS, id2word=dictionary, passes=20)
	ldamodel.save(MODEL_PATH +'lda_'+MODEL_NAME+'.gensim')

	end_time = time.time()
	print('LDA elapsed time: ',(end_time-start_time)/60,' minutes')

	topics = ldamodel.print_topics(num_words=10)

	print('LDA model:')
	for topic in topics: print(topic)

	###LSI model
	start_time = time.time()

	lsimodel = gensim.models.lsimodel.LsiModel(corpus=corpus, num_topics=NUM_TOPICS, id2word=dictionary)
	lsimodel.save(MODEL_PATH +'lsi_'+MODEL_NAME+'.gensim')

	end_time = time.time()
	print('LSI elapsed time: ',(end_time-start_time)/60,' minutes')

	topics = lsimodel.print_topics(10)

	print('LSI model:')
	for topic in topics: print(topic)
	

	###Plotting stuff with sci-kit


else:
	print('Error. Correct usage: \ntopic.py <MODEL_NAME>')
