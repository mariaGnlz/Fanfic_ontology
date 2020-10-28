#!/bin/bash/python3


#Tagger for NER tags, using a previously trained NER chunker

import nltk, re, pprint, sys, time, pickle, pandas, numpy
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from collections import Counter
#from nltk.tree import Tree

### VARIABLES ###
POS_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_tags.csv'
POS_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/POS_typical_tags.csv'
NER_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/NER_tags.csv'
NER_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/NER_typical_tags.csv'

### FUNCTIONS ###

def get_tagged_fics_from_csv(start_fic, end_fic):
	#csv_file = pandas.read_csv(POS_TAGGED_FICS_PATH, encoding='ISO-8859-1')
	csv_file = pandas.read_csv(POS_TAGGED_FICS_PATH)

	start_index = csv_file.loc[csv_file['Fic number'] == start_fic].index[0]
	end_index = csv_file.loc[csv_file['Fic number'] == end_fic].index[0]+1
	#end_index = csv_file.loc[csv_file['Fic number'] == end_fic-1].index[0]+1
	print(start_index, end_index) #debug

	i = 0
	sentences = []
	tagged_fics = []
	current_sent = []
	for i in range(start_index, end_index):
		if i == 0:
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i]))
			
		elif csv_file['Sentence number'][i] != csv_file['Sentence number'][i-1]:
			#print(current_sent) #debug
			sentences.append(current_sent)

			if csv_file['Fic number'][i] != csv_file['Fic number'][i-1]:
				tagged_fics.append((sentences, csv_file['Fic number'][i-1])) 

			current_sent = []
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i]))
 
		else:
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i]))

		

	return tagged_fics #returns the fanfics in the form of a list of POS-tagged sentences that NLTK can understand

def traverse(t, num_fic, num_sentence, iob_str):
	rows = []
	
	for node in t:
		if type(node) is nltk.Tree:
			#print(node.label()) #debug

			iob_str = node.label()
			auxrows = traverse(node, num_fic, num_sentence, iob_str)
			rows.extend(auxrows)
	
		else: 
			#print('Word: ',node) #debug
			rows.append((num_fic, num_sentence, node[0], node[1], iob_str))

			iob_str = '-'

	return rows

def start_NER_tagging(tagged_fic, num_fic, typical):
	start = time.time()
	NER_tagged_senteces = [NER_chunker.parse(sent) for sent in tagged_fic] #NER-tagging
	end = time.time()

	print('Parsed ', len(tagged_fic),' in ',(end-start)/60,' minutes')

	# Loop to explore the tagged chunks in tagged_fics
	num_sentence = 0

	per_entities= []
	start = time.time() 
	for sentence in NER_tagged_senteces:
		for t in sentence.subtrees():
			if t.label() == 'per': 
				leaves = t.leaves()
				entity = [word for word, _ in leaves]
				#Clean name
				entity = numpy.char.lstrip(entity, chars="”“’‘_–*")
				entity = ' '.join(entity)
				entity = entity.strip()
				
				per_entities.append(entity)

	print(len(per_entities)) #debug

	named_mentions = set(per_entities)
	numbered_mentions = []
	for name in named_mentions:
		num = per_entities.count(name)
		numbered_mentions.append((num, name))
	
	print(numbered_mentions) #debug
	print(len(numbered_mentions)) #debug
	
	end = time.time()


def get_last_tagged_fics():
	csv_file = pandas.read_csv(NER_TAGGED_FICS_PATH)
	last_tagged = csv_file['Fic number'][len(csv_file['Fic number'])-1]
	num_fics = len(set(csv_file['Fic number']))

	return last_tagged, num_fics


### M A I N ###

class NERTagger():

	def parse(tagged_fic): #fanfic must be pos-tagged previously
		###Load trained chunker and parse sentences
		f = open('NER_training.pickle','rb')
		NER_chunker = pickle.load(f)
		f.close()

		NER_tagged_sentences = [NER_chunker.parse(sent) for sent in tagged_fic] #NER-tagging

		#Explore the tags and create a list of named entities
		per_entities= []
		start = time.time() 
		for sentence in NER_tagged_sentences:
			for t in sentence.subtrees():
				if t.label() == 'per': 
					leaves = t.leaves()
					entity = [word for word, _ in leaves]
					#Clean name
					entity = numpy.char.lstrip(entity, chars="”“’‘_–* ")
					entity = ' '.join(entity)
					entity = entity.strip()
					
					per_entities.append(entity)
				
		#print(len(per_entities)) #debug
		
		named_mentions = set(per_entities)
		numbered_mentions = []
		for name in named_mentions:
			num = per_entities.count(name)
			numbered_mentions.append((num, name))
	
		#print(numbered_mentions) #debug
		#print(len(numbered_mentions)) #debug

		return numbered_mentions, NER_tagged_sentences

### END NERTAGGER CLASS

if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])
	#print(type(start_index), end_index) #debug


	###Load trained chunker and parse sentences
	f = open('NER_training.pickle','rb')
	NER_chunker = pickle.load(f)
	f.close()

	###Get POS-tagged fics
	tagged_fics = get_tagged_fics_from_csv(start_index, end_index)
	#print(len(tagged_fics)) #debug

	###NER-tag fanfics
	for fic, num_fic in tagged_fics:
		start_NER_tagging(fic, num_fic, 1)


elif len(sys.argv) == 2:
	if sys.argv[1] == 'd': 
		last_tagged, num_fics = get_last_tagged_fics()
		print('Number of tagged fics: ',num_fics,'\nID of last tagged fic: ',last_tagged)

	elif sys.argv[1] == 't': #tag typical fics
		###Load trained chunker and parse sentences
		f = open('NER_training.pickle','rb')
		NER_chunker = pickle.load(f)
		f.close()

		###Get POS-tagged fics
		tagged_fics = get_tagged_fics_from_csv(1, 1)
		#print(len(tagged_fics)) #debug

		###NER-tag fanfics
		for fic, num_fic in tagged_fics:
			start_NER_tagging(fic, num_fic)
"""
elif len(sys.argv) == 1:
	###Load trained chunker and parse sentences
	f = open('NER_training.pickle','rb')
	NER_chunker = pickle.load(f)
	f.close()

	###Get POS-tagged fics
	tagged_fics = get_tagged_fics_from_csv(0,10) #debug
	
	#print(len(tagged_fics)) #debug
	#print(tagged_fics[1][0][len(tagged_fics[1][0])-1],) #debug
	
	###NER-tag fanfics
	for fic, num_fic in tagged_fics:
		start_NER_tagging(fic, num_fic, 0)
	
	

else:
	print('Error. Correct usage: \nNER_tagger.py \nNER_tagger.py [start_index] [end_index] \nNER_tagger d')


"""	



