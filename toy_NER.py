#!/bin/bash/python3


#Toy version of an entity recognition process

import nltk, re, pprint
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from toy_chunkers import UnigramChunker
import pandas

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/trial_fic_paths.txt'

### FUNCTIONS ###

def preprocess_fics(fic_list): #divide raw text into words and tag them	
	fic_sentences = [sent_tokenize(fic) for fic in fic_list]	
	processed_fics = [[pos_tag(word_tokenize(sent)) for sent in fic] for fic in fic_sentences]

	return processed_fics

def get_processed_fanfics(): #gets the paths to the fics, opens them
                   #and concatenates their textin a string
	paths_file = open(FIC_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()
	
	fic_list = []
	for path in fic_paths:
		txt_file = open(path, 'r')
		fic_list.append(txt_file.read())
		txt_file.close()

	#print(fic_list[0]) #debug
	return preprocess_fics(fic_list)

def save_to_csv(tagged_fics):
	data = { 'Fic number': range(len(tagged_fics)),
		'Sentence number': [len(fic) for fic in tagged_fics],
	}

	df = pandas.DataFrame(data, columns=['Fic number','Sentence number'])

	df.to_csv('toy_tags.csv', index=False)

def store_in_lists(tagged_sents):
	### Store individual entities in lists ###
	people=[] #Store entities tagged 'PERSON' here
	locations=[] #Store entities tagged 'LOCATION' here
	organizations=[] #Store entities tagged 'ORGANIZATION' Here
	dates=[] #Store entities tagged 'DATE' Here
	gpes=[] #Store entities tagged 'GPE' Here
	facilities=[] #Store entities tagged 'FACILITY' Here

	for chunk in tagged_sents.pos(): #result.pos() returns the leaves of the tree with their tags
		if chunk[1] == 'PERSON':
			#print(chunk[0],chunk[1]) #debug
			people.append(chunk[0][0])

		elif chunk[1] == 'LOCATION':
			locations.append(chunk[0][0])
	
		elif chunk[1] == 'ORGANIZATION':
			organizations.append(chunk[0][0])

		elif chunk[1] == 'DATE':
			dates.append(chunk[0][0])

		elif chunk[1] == 'GPE':
			gpes.append(chunk[0][0])

		elif chunk[1] == 'FACILITY':
			facilities.append(chunk[0][0])
		

	entities=people+locations+organizations+dates+gpes+facilities
	print('PEOPLE: \n', sorted(set(people)))
	print('LOCATIONS: \n', sorted(set(locations)))
	print('ORGANIZATIONS: \n', sorted(set(organizations)))
	print('DATES: \n', sorted(set(dates)))
	print('GPES: \n', sorted(set(gpes)))
	print('FACILITIES: \n', sorted(set(facilities)))
	

	aux=open('./output.txt','w')
	for element in entities:
		aux.write(str(element)+'\n')

	aux.close()


### MAIN
		
### Open and get text from txt file
processed_fics = get_processed_fanfics()
#print(processed_fics[0]) #debug
#print(type(processed_fics), type(processed_fics[0]), type(processed_fics[0][0]), type(processed_fics[0][0][0])) #debug


### NER chunking ###
tagged_fics = [[nltk.ne_chunk(sent) for sent in fic] for fic in processed_fics] #Entity extraction with NLTK NE chunker
#print(tagged_fics[0]) #debug
#print(tagged_fics[0].pos()) #debug


### Save results to a csv file
save_to_csv(tagged_fics)


#result.draw() #requires Tkinter library


