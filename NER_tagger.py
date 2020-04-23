#!/bin/bash/python3


#Trainer for an entity recognition process

import nltk, re, pprint, sys, time, pickle, pandas
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.tree import Tree

### VARIABLES ###
POS_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_tags.csv'

### FUNCTIONS ###

def get_tagged_fics_from_csv():
	csv_file = pandas.read_csv(POS_TAGGED_FICS_PATH, encoding='ISO-8859-1')
	
	i = 0
	sentences = []
	current_sent = []
	#while i < len(csv_file['Word']):
	while csv_file['Sentence number'][i] < 1000:
		if i == 0:
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i]))
			
		elif csv_file['Sentence number'][i] != csv_file['Sentence number'][i-1]: 
		
			sentences.append(current_sent) #probably a step in here is needed for NLTK to properly understand the sentence

			current_sent = []
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i]))
 
		else:
			current_sent.append((csv_file['Word'][i], csv_file['POS'][i]))

		i+=1

	return sentences #returns a list of tagged sentences that NLTK can understand

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

def start_POS_tagging(tagged_senteces):
	start = time.time()
	NER_tagged_senteces = [NER_chunker.parse(sent) for sent in tagged_sentences]
	end = time.time()

	print('Parsed ', len(tagged_sentences),' in ',(end-start)/60,' minutes')

	###Store tagged sentences on CSV
	# Create pandas dataframe to store data
	df = pandas.DataFrame(columns=['Fic number', 'Sentence number', 'Word', 'POS', 'IOB'])

	# Loop to explore the tagged chunks in tagged_fics
	num_sentence = 0
	num_fic = 0
	
	rows = []
	start = time.time() 
	for sentence in tagged_sentences:
		auxrows = traverse(sentence, num_fic, num_sentence, '-')
		rows.extend(auxrows)
		
		num_sentence+=1

	end = time.time()

	print(num_sentence, 'sentences stored in ',(end-start)/60,'minutes')

	return rows

### M A I N ###
###Load trained chunker and parse sentences
f = open('bigger_toy_NER.pickle','rb')
NER_chunker = pickle.load(f)
f.close()

tagged_sentences = get_tagged_fics_from_csv()


if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])
	#print(type(start_index), end_index) #debug

	tagged_sentences = tagged_sentences[start_index:end_index]
	print(len(tagged_sentences)) #debug

elif len(sys.argv) == 1:


else:
	print(


### Unzip the tuples into columns and save results to csv file 
columns = list(zip(*rows))

df['Fic number'] = columns[0]
df['Sentence number'] = columns[1]
df['Word'] = columns[2]
df['POS'] = columns[3]
df['IOB'] = columns[4]

df.to_csv('NER_tags.csv', index=False)

	



