#!/bin/bash/python3


#Tagger for NER tags, using a previously trained NER chunker

import pickle, time, numpy

### VARIABLES ###
MODEL_PATH = '/home/maria/Documents/Fanfic_ontology/NER_training.pickle'

### CLASSES ###

class NERTagger():
	
	def __init__(self):
		self.model_path = MODEL_PATH 
	
	def parse(self, tagged_fic): #fanfic must be pos-tagged previously
		###Load trained chunker and parse sentences
		f = open(self.model_path,'rb')
		NER_chunker = pickle.load(f)
		f.close()

		NER_tagged_sentences = [NER_chunker.parse(sent) for sent in tagged_fic] #NER-tagging

		#Explore the tags and create a list of named entities
		per_entities= []
		#start = time.time() 
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
			if name != '':
				num = per_entities.count(name)
				character_mentions[name] = int(num)
	
		#print(numbered_mentions) #debug
		#print(len(numbered_mentions)) #debug

		return character_mentions

	def get_model_path(self): return self.model_path

	def set_model_path(self, path):
		self.model_path = path

### MAIN ###



