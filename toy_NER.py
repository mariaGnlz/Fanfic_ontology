#!/bin/bash/python3


#Toy version of an entity recognition process

import nltk, re, pprint, time, pandas
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from toy_chunkers import UnigramChunker

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


### M A I N ###
		
### Open and get text from txt file
processed_fics = get_processed_fanfics()
#print(processed_fics[0]) #debug
#print(type(processed_fics), type(processed_fics[0]), type(processed_fics[0][0]), type(processed_fics[0][0][0])) #debug


### NER chunking ###
tagged_fics = [[nltk.ne_chunk(sent) for sent in fic] for fic in processed_fics] #Entity extraction with NLTK NE chunker
#print(tagged_fics[0]) #debug

# Create pandas dataframe to store data
df = pandas.DataFrame(columns=['Fic number', 'Sentence number', 'Word', 'POS', 'IOB'])

# Loop to explore the tagged chunks in tagged_fics
num_sentence = 0
num_fic = 0

rows = []
start = time.time() 
for fic in tagged_fics:
	for sentence in fic:
		#auxfic, auxsen, auxwords, auxpos, auxiob = traverse(sentence, count, num_fic, num_sentence)
		auxrows = traverse(sentence, num_fic, num_sentence, '-')
		rows.extend(auxrows)
		
		num_sentence+=1
	
	num_fic+=1

end = time.time()

print(num_sentence, 'sentences in ',(end-start)/60,'minutes')

### Unzip the tuples into columns and save results to csv file 
columns = list(zip(*rows))

df['Fic number'] = columns[0]
df['Sentence number'] = columns[1]
df['Word'] = columns[2]
df['POS'] = columns[3]
df['IOB'] = columns[4]

df.to_csv('toy_NER_tags.csv', index=False)


#result.draw() #requires Tkinter library


