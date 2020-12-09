#!/bin/bash/python3


#Tagger for NER tags, using a previously trained NER chunker

import nltk, re, pprint, sys, time, pandas, numpy
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from fanfic_util import FanficGetter
from NER_tagger_v3 import NERTagger

### VARIABLES ###
RFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths.txt'
FFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths.txt'
EFIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths.txt'

#NER_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/NER_tags_v2.csv'
NER_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/NER_tags_RFE.csv'

### FUNCTIONS ###


def save_characters(characters, fic_index):
	###Store character data on CSV
	# Create pandas dataframe to store data
	name_col = []
	mentions_col = []
	for name, num in characters.items():
		name_col.append(name)
		mentions_col.append(num)

	df_format = {'Name': name_col, 'Mentions': mentions_col}
	df = pandas.DataFrame.from_dict(df_format)
	df.insert(loc=0, column='Fic index', value=fic_index)

	df.to_csv(NER_TAGGED_FICS_PATH, mode='a', index=False)
	#df.to_csv(NER_TAGGED_FICS_PATH, index=False)


def get_last_tagged_fics():
	csv_file = pandas.read_csv(NER_TAGGED_FICS_PATH)
	last_tagged = csv_file['Fic number'][len(csv_file['Fic number'])-1]
	num_fics = len(set(csv_file['Fic number']))

	return last_tagged, num_fics

def tag_characters(tag_fics, fic_indexes):
	ner_tag = NERTagger()

	start = time.time()
	print("Starting NER tagging. . .")
	for num, fic in enumerate(tag_fics):
		#print(fic[:10]) #debug
		characters = ner_tag.parse(fic)
		save_characters(characters, fic_indexes[num])


	end = time.time()
	print('Parsed and saved ', len(tag_fics),' fics in ',(end-start)/60,' minutes')


### M A I N ###

fanfic_getter = FanficGetter()

if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])
	#print(type(start_index), end_index) #debug

	print("Fetching fanfics, tokenizing and pos-tagging them. . .")
	fics = fanfic_getter.get_fanfics_in_range(start_index, end_index)

	"""
	fanfic_getter.set_fic_listing_path(RFIC_LISTING_PATH)
	rfics = fanfic_getter.get_fanfics_in_range(start_index, end_index)
	fanfic_getter.set_fic_listing_path(FFIC_LISTING_PATH)
	ffics = fanfic_getter.get_fanfics_in_range(start_index, end_index)
	fanfic_getter.set_fic_listing_path(EFIC_LISTING_PATH)
	efics = fanfic_getter.get_fanfics_in_range(start_index, end_index)

	fics = rfics + ffics + efics
	"""
	tag_fics = []
	for fic in fics:
		sent_tokens = sent_tokenize(fic.get_string_chapters())
		word_tokens = [word_tokenize(sent) for sent in sent_tokens]
		tag_fics.append([pos_tag(word) for word in word_tokens])

	#print(len(tag_fics)) #debug
	fic_indexes = [fic.index for fic in fics]

	print("...done")
	tag_characters(tag_fics, fic_indexes)





elif len(sys.argv) == 2:
	if sys.argv[1] == 'd': 
		last_tagged, num_fics = get_last_tagged_fics()
		print('Number of tagged fics: ',num_fics,'\nID of last tagged fic: ',last_tagged)

	elif sys.argv[1] == 'p': #show path for FanficGetter
		print('FanficGetter path: ', fanfic_getter.get_fic_listing_path())

elif len(sys.argv) == 1:
	start = time.time()
	###Get fanfics, tokenize and pos-tag them
	fic = fanfic_getter.get_fanfics_in_range(8,9)

	sent_fic = sent_tokenize(fic[0].get_string_chapters())
	word_fic = [word_tokenize(sent) for sent in sent_fic]
	tag_fic = [pos_tag(word) for word in word_fic]

	#print(len(tag_fic), tag_fic[:10]) #debug

	###NER-tag fanfics
	ner_tag = NERTagger()
	characters = ner_tag.parse(tag_fic)
	#print(characters) #debug
	save_characters(characters, fic[0].index)

	end = time.time()
	print('Parsed and saved ', len(fic),' fics in ',(end-start)/60,' minutes')




else:
	print('Error. Correct usage: \nNER_tagger.py \nNER_tagger.py [start_index] [end_index] \nNER_tagger d')


	



