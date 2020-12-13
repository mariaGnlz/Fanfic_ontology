#!/bin/bash/python3

import sys, time, pandas, numpy, nltk
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from corenlp_wrapper import CoreClient
from stanza.server import Document
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet

from NER_tagger_v3 import NERTagger
from fanfic_util import FanficGetter, FanficHTMLHandler, Fanfic

### VARIABLES ###
TO_CSV = '/home/maria/Documents/Fanfic_ontology/fic_senteces.csv'
CANON_DB = '/home/maria/Documents/Fanfic_ontology/canon_characters.csv'
ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths2.txt'
EXPLICIT_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/explicit_fic_paths.txt'
FRIENDSHIP_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths2.txt'
ENEMY_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths2.txt'

VERB_TAGS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']


### FUNCTIONS ###
def get_lemma(word):
	lemma = wordnet.morphy(word)

	if lemma is None:
		return word
	else: return lemma

STOPWORDS = [get_lemma(word) for word in stopwords.words('english')]

def get_longest_lists(coref_chains): #returns the two longest chains in the coreference graph
	longest = []
	longest.append(max(list(coref_chains), key=len))

	coref_chains.remove(longest[0])

	longest.append(max(list(coref_chains), key=len))

	return longest

def get_lemmatized_verbs(sentence):
	tagged_sent = pos_tag(word_tokenize(sentence))
	#print(tagged_sent) #debug

	verbs = []
	for word, pos in tagged_sent:
		if pos in VERB_TAGS and word not in STOPWORDS:
			#print(word, pos) #debug
			verbs.append(get_lemma(word))

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

def merge_sentences(fic_sentences):

	sen_ids = []
	merged_sentences = []
	for sentence in fic_sentences:
		sent = {}
		if sentence['SenID'] in sen_ids: #If a dict for this sentence already exists
			sent = list(filter(lambda s: s['SenID'] == sentence['SenID'], merged_sentences))
			#print(len(sent)) #debug
			sent = sent[0]

			if sentence['Clusters'] not in sent['Clusters']: sent['Clusters'].append(sentence['Clusters'])

		else: #Create new sentence dict
			sen_ids.append(sentence['SenID'])

			sent['SenID'] = sentence['SenID']
			sent['Sentiment'] = sentence['Sentiment']
			sent['Verbs'] = sentence['Verbs']
			sent['Clusters'] = [sentence['Clusters']]

			merged_sentences.append(sent)

	return merged_sentences		

def extract_sentences_with_corenlp(fic):
	# Declarations for later
	#sentences = []
	chains = []

	character_mentions = []
	character_entities = []
	mention_sentences = []
	#print(fic.chapters[0][:100]) #debug

	# Starting client to CoreNLP
	anns = client.parse(fic.chapters)


	fic_sentences = []
	fic_sentiments = []
	#print("Processing annotation data...")
	#start = time.time()
	
	for ann in anns:
		sentences= ann.sentence
		all_ner_mentions = ann.mentions #NERMention[]
		all_coref_mentions = ann.mentionsForCoref #Mention[]
		chains = ann.corefChain #CorefChain[], made up of CorefMention[]
		

		coref_chains = []
		for i in range(0, len(chains)): #debug
			coref_chains.append(chains[i].mention)
		#coref_chains = get_longest_lists(coref_chains)

			
		## Extract sentences which mention protagonists ##
		for chain in coref_chains:
			for mention in chain:
				sentence = {}
				sen = sentences[mention.sentenceIndex]

				string_sen = ''
				for token in sen.token: 
					string_sen += ' '+token.originalText

				#if ners > 1:
				#print(string_sen) #debug
				sentence['SenID'] = mention.sentenceIndex
				sentence['Sentiment'] = sen.sentiment
				#sentence['Verbs'] = get_lemmatized_verbs(string_sen)
				sentence['Verbs'] = string_sen
				sentence['Clusters'] = all_coref_mentions[mention.mentionID].corefClusterID

				fic_sentences.append(sentence)

				
				#for i in range(mention.beginIndex, mention.endIndex):
				#	print(sen.token[i].originalText)
				
		

		for sentence in sentences:
			

	return fic_sentences

def get_fanfics(start, end):
	fGetter = FanficGetter()

	fGetter.set_fic_listing_path(ROMANCE_LISTING_PATH)
	r_fics = fGetter.get_fanfics_in_range(start, end) #get ROMANCE fanfics
	fGetter.set_fic_listing_path(EXPLICIT_LISTING_PATH)
	e_fics = fGetter.get_fanfics_in_range(start, end) #get EXPLICIT fanfics
	fGetter.set_fic_listing_path(FRIENDSHIP_LISTING_PATH)
	f_fics = fGetter.get_fanfics_in_range(start, end) #get FRIENDSHIP fanfics
	#fGetter.set_fic_listing_path(ENEMY_LISTING_PATH)
	#n_fics = fGetter.get_fanfics_in_range(start, end) #get ENEMY fanfics

	return r_fics + e_fics + f_fics

### MAIN ###

# Initializing getters and taggers...
client = CoreClient()

# Loading canon DB...
canon_db = pandas.read_csv(CANON_DB)

if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])

	print('Fetching fic texts...')
	start = time.time()

	fic_list = get_fanfics(start_index, end_index)

	end = time.time()
	print("...fics fetched. Elapsed time: ",(end-start)/60," mins")

	print('\n###### Starting CoreNLP server and processing fanfics. . .######\n')
	start= time.time()

	all_sentences = []
	for fic in fic_list:
		print('Processing fic #', fic.index)
		# Extract sentences with CoreNLP
		character_entities, character_mentions = extract_sentences_with_corenlp(fic)
	
		# Merge all character mentions into unique characters
		#unique_characters = merge_character_mentions(character_entities, character_mentions, tagger_characters)

		# Link characters to their canon version, if it has one
		#canonized_characters = link_characters_to_canon(unique_characters, canon_db)
		#print(canonized_characters[:10])
		#print(canonized_characters) #debug

		# Decide genders for all characters
		#canonized_characters = decide_gender(canonized_characters, canon_db)

		#all_sentences.extend(canonized_characters)
		
	end = time.time()
	print("Client closed. "+ str((end-start)/60) +" mins elapsed")

	# Create dataframe from dicts and save to csv
	#df = pandas.DataFrame.from_dict(all_characters)

	#df.to_csv(TO_CSV, mode='a', index=False, header=True)


elif len(sys.argv) == 1:
	print('Fetching fic texts...')
	start = time.time()
	
	fic_list = get_fanfics(0, 1)
	#print(len(fic_list), fic_list[0].chapters[0][:100]) #debug

	end = time.time()
	print("...fics fetched. Elapsed time: ",(end-start)/60," mins")

	print('\n###### Starting CoreNLP server and processing fanfics. . .######\n')
	start= time.time()

	all_characters = []
	for fic in fic_list:
		print('Processing fic #', fic.index)
		# Extract sentences with CoreNLP
		fic_sentences = extract_sentences_with_corenlp(fic)
		merged_sentences = merge_sentences(fic_sentences)

		print(len(fic_sentences), len(merged_sentences))
		#print(merged_sentences)

		for sen in merged_sentences:
			if len(sen['Clusters']) > 1: print(sen)
		
		#sentiment = normalize_sentiment(fic_sentiments)

		#print(len(fic_sentiments),sentiment)

		#if len(fic_verbs) > 0:
		#	verb_freq = nltk.FreqDist(fic_verbs)
		#	verb_freq.plot()
	
		
	end = time.time()
	print("Client closed. "+ str((end-start)/60) +" mins elapsed")
	
	# Create dataframe from dicts and save to csv
	#df = pandas.DataFrame.from_dict(all_characters)

	#df.to_csv(TO_CSV, mode='a', index=False, header=True)

