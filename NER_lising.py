#!/usr/bin/bash/python3


import nltk, re, pprint, sys, time, pickle, pandas


### VARIABLES ###
POS_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_tags.csv'
NER_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/NER_tags.csv'
NER_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/NER_listing.csv'

### FUNCTIONS ###

def get_characters_from_csv(start_fic, end_fic):
	#csv_file = pandas.read_csv(POS_TAGGED_FICS_PATH, encoding='ISO-8859-1')
	csv_file = pandas.read_csv(NER_TAGGED_FICS_PATH)

	start_index = csv_file.loc[csv_file['Fic number'] == start_fic].index[0]
	if end_fic == 1: end_index = csv_file.loc[csv_file['Fic number'] == end_fic].index[0]+1
	else: end_index = csv_file.loc[csv_file['Fic number'] == end_fic-1].index[0]
	
	print(start_index, end_index) #debug

	characters = []

	#for i in range(start_index, end_index):
	i = start_index
	while i <  end_index:
	
		if csv_file['IOB'][i] == 'per': 
			characters.append(csv_file['Word'][i])
			i += 1

		i += 1

	return set(characters)

### MAIN ###

characters = get_characters_from_csv(0,1)
print(characters)
