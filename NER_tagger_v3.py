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


### M A I N ###

class NERTagger():
	"""
	def parse(self, tagged_fic): #fanfic must be pos-tagged previously
		###Load trained chunker and parse sentences
		f = open('NER_training.pickle','rb')
		NER_chunker = pickle.load(f)
		f.close()

		NER_tagged_sentences = [NER_chunker.parse(sent) for sent in tagged_fic] #NER-tagging

		return nltk.chunk.tree2conlltags(NER_tagged_sentences)
	"""
	def parse(self, tagged_fic): #fanfic must be pos-tagged previously
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
		
		names = set(per_entities)
		character_mentions = {}
		for name in names:
			num = per_entities.count(name)
			character_mentions[name] = num
	
		#print(numbered_mentions) #debug
		#print(len(numbered_mentions)) #debug

		return character_mentions
	

### END NERTAGGER CLASS
