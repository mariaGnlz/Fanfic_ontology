#!/bin/bash/python3


#Tagger for NER tags, using a previously trained NER chunker

import nltk, re, pprint, sys, time, pickle, pandas, numpy
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from collections import Counter
from nltk.tree import Tree
from nltk import conlltags2tree, tree2conlltags

### VARIABLES ###
POS_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_tags.csv'
POS_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/POS_typical_tags.csv'
NER_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/NER_tags_v3.csv'
NER_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/NER_typical_tags.csv'

### FUNCTIONS ###

def get_tagged_fics_from_csv(start_fic, end_fic):
	#csv_file = pandas.read_csv(POS_TAGGED_FICS_PATH, encoding='ISO-8859-1')
	csv_file = pandas.read_csv(POS_TAGGED_FICS_PATH)

	start_index = csv_file.loc[csv_file['Fic number'] == start_fic].index[0]
	end_index = csv_file.loc[csv_file['Fic number'] == end_fic].index[0]+1
	#end_index = csv_file.loc[csv_file['Fic number'] == end_fic-1].index[0]+1
	#print(start_index, end_index) #debug

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
	NER_tagged_sentences = [NER_chunker.parse(sent) for sent in tagged_fic] #NER-tagging
	end = time.time()

	print('Parsed ', len(tagged_fic),' in ',(end-start)/60,' minutes')

	tree = Tree ('S',NER_tagged_sentences)
	
	character_names = []
	for chunk in tree.pos():
		if chunk[1] == 'per' and chunk[0][0] not in ["‘", "’", "-", "–", "_"]: character_names.append(chunk[0][0])

	taga = NER_chunker.parse(pos_tag("My name is James Bond"))
	for chunk in taga:
		#print(chunk)
		if chunk[1] == 'per' : print(chunk[1])
	

	#print(character_names) #debug
	
	character_names = [name.strip() for name in character_names]
	character_names = [name.strip("‘") for name in character_names]
	character_names = [name.strip("’") for name in character_names]
	character_names = [name.strip("–") for name in character_names]
	character_names = [name.strip("_") for name in character_names]
	
	
	character_mentions = Counter(character_names) #counting the times a character is mentioned
	
	fic_number = [0] * len(character_mentions.keys())

	###Store character data on CSV
	# Create pandas dataframe to store data
	df = pandas.DataFrame(columns=['Fic number', 'Character name', 'Times mentioned'])
	df['Fic number'] = fic_number
	df['Character name'] = character_mentions.keys()
	df['Times mentioned'] = character_mentions.values()

	#df.to_csv(NER_TAGGED_FICS_PATH, mode='a', index=False)
	df.to_csv(NER_TAGGED_FICS_PATH, index=False)


	"""
	for sentence in NER_tagged_sentences:
		iob_sent = tree2conlltags(sentence)
		#iob_sent = conlltags2tree(sentence)
		#print(iob_sent)
		iob_sentences.append(iob_sent)
	
	"""
	"""
	# Loop to explore the tagged chunks in tagged_fics
	num_sentence = 0

	rows = []
	start = time.time() 
	for sentence in NER_tagged_senteces:
		#auxfic, auxsen, auxwords, auxpos, auxiob = traverse(sentence, count, num_fic, num_sentence)
		auxrows = traverse(sentence, num_fic, num_sentence, '')
		rows.extend(auxrows)
		#print(auxrows) #debug
		
		num_sentence+=1
	
	end = time.time()

	if num_sentence > 0:
		print(num_sentence, 'sentences stored in ',(end-start)/60,'minutes')

		character_data = []
		i=0
		state = False
		name_str = ''
		while i < len(rows):
			if rows[i][4] == 'per':
				if state:
					#character_data.append((rows[0], name_str+rows[i][2], 1))
					character_data.append((rows[0], name_str, 1))
					#(fic number, character name, # of mentions of said name)
					state = False
					name_str = ''
					#i += 1

				else:
					name_str = name_str+rows[i][2]+' '
					state = True

			elif rows[i][4] == '-' and state: name_str = name_str+rows[i][2]+' '
			else: name_str = ''
			i += 1

		### Unzip the tuples into columns
		columns = list(zip(*character_data))
		character_names = [name.strip() for name in columns[1]]
		character_names = [name.strip("‘") for name in character_names]
		character_names = [name.strip("’") for name in character_names]
		character_names = [name.strip('–') for name in character_names]
		character_mentions = Counter(character_names)
		fic_number = [0] * len(character_mentions.keys())
		#print(character_mentions) #debug
		
		###Store character data on CSV
		# Create pandas dataframe to store data
		df = pandas.DataFrame(columns=['Fic number', 'Character name', 'Times mentioned'])
		df['Fic number'] = fic_number
		df['Character name'] = character_mentions.keys()
		df['Times mentioned'] = character_mentions.values()

		#df.to_csv(NER_TAGGED_FICS_PATH, mode='a', index=False)
		df.to_csv(NER_TAGGED_FICS_PATH, index=False)
	"""

	"""
	if num_sentence > 0: 
		print(num_sentence, 'sentences stored in ',(end-start)/60,'minutes')
		### Unzip the tuples into columns and save results to csv file 
		columns = list(zip(*rows))

		df['Fic number'] = columns[0]
		df['Sentence number'] = columns[1]
		df['Word'] = columns[2]
		df['POS'] = columns[3]
		df['IOB'] = columns[4]

		#df.to_csv(NER_TAGGED_FICS_PATH, mode='a', index=False, encoding='ISO-8859-1')
		if typical == 0: df.to_csv(NER_TAGGED_FICS_PATH, mode='a', index=False)
		else: df.to_csv(NER_TYPICAL_PATH, mode='a', index=False)
	
	else:
		print('Ocurrió algún problema procesando el fic ',num_fic)
		f = open('NER_tag_problems.txt','a')
		f.write('Problem ocurred on fic '+str(num_fic)+'\n')
		f.close()
	"""

def get_last_tagged_fics():
	csv_file = pandas.read_csv(NER_TAGGED_FICS_PATH)
	last_tagged = csv_file['Fic number'][len(csv_file['Fic number'])-1]
	num_fics = len(set(csv_file['Fic number']))

	return last_tagged, num_fics


### M A I N ###

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


	



