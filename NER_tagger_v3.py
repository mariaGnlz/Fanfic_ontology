#!/bin/bash/python3


#Tagger for NER tags, using a previously trained NER chunker

import pickle, time, pandas, re, nltk

### VARIABLES ###
MODEL_PATH = '/home/maria/Documents/Fanfic_ontology/NER_training.pickle'
CANON_DB = '/home/maria/Documents/Fanfic_ontology/canon_characters.csv'
MAX_EDIT_DISTANCE = 3

### FUNCTIONS ###

def get_max_edit_distance(name):
	if ' ' in name:
		subnames = [n.strip() for n in name.split(' ')]

		lengths = [len(name) for name in subnames]

		min_length = min(lengths)

	else: min_length = len(name.strip())

	if min_length > 4: return 3
	elif min_length == 4: return 2
	else: return 0

def get_edit_distance(name1, name2):
	if ' ' in name1:
		name_and_surname1 = [n.strip().lower() for n in name1.split(' ')]

		distance = []
		if ' ' in name2:
			name_and_surname2 = [n.strip().lower() for n in name2.split(' ')]

			for n1 in name_and_surname1:
				for n2 in name_and_surname2: distance.append(nltk.edit_distance(n1, n2))

		else:
			for n in name_and_surname1: distance.append(nltk.edit_distance(n, name2.lower()))

		return min(distance)

	elif ' ' in name2:
		name_and_surname2 = [n.strip().lower() for n in name2.split(' ')]

		distance = []
		for n in name_and_surname2: distance.append(nltk.edit_distance(name1.lower(), n))

		return min(distance)

	else: return nltk.edit_distance(name1.lower(), name2.lower())

def link_to_canon(ner_entities):
	#Get canon_db
	canon_db = pandas.read_csv(CANON_DB)

	for character in ner_entities:
		better_fit = {}

		for index, canon_character in canon_db.iterrows():
			if type(canon_character['Other names']) == str:
				other_canon_names = [name.strip().lower() for name in canon_character['Other names'].split(',')]
				#print(other_canon_names) #debug


			else: other_canon_names = ['']

			distance = get_edit_distance(canon_character['Name'], character['Name'])
			max_edit_distance = min(get_max_edit_distance(canon_character['Name']), get_max_edit_distance(character['Name']))

			if  distance == 0:
				character['Canon ID'] = index
				break

			elif distance < max_edit_distance:
				#print(canon_character['Name'].lower(), character['Name'].lower()) #debug
				#character['Canon ID'] = index

				better_fit[index] = distance
				#break

			else:
				for other_name in other_canon_names:
					distance = get_edit_distance(other_name, character['Name'])
					max_edit_distance = min(get_max_edit_distance(other_name), get_max_edit_distance(character['Name']))

					if distance == 0:
						character['Canon ID'] = index
						break

					elif distance < max_edit_distance:
						#character['Canon ID'] = index

						better_fit[index] = distance
						#break

		if character['Canon ID'] < 0 and better_fit:
			better_fit_name = min(better_fit.items(), key=lambda x: x[1])
			character['Canon ID'] = better_fit_name[0]
			
	return ner_entities

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
					#print(entity) #debug

					entity = ' '.join(entity)
					entity = re.sub(r'[^A-Za-z0-9 ]+', '', entity).strip() #Clean name
					
					per_entities.append(entity)
				
		#print(len(per_entities)) #debug
		
		names = set(per_entities)
		ner_entities = []
		for name in names:
			num = per_entities.count(name)
			ner_entities.append({'Name':name, 'Mentions':num, 'Canon ID':-1})

		#print(ner_entities) #debug

		canonized_ner_entities = link_to_canon(ner_entities)

		return canonized_ner_entities

	def get_model_path(self): return self.model_path

	def set_model_path(self, path):
		self.model_path = path

### MAIN ###



