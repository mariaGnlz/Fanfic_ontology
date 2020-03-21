#!/bin/bash/python3


#Toy version of an entity recognition process

import nltk, re, pprint
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

### VARIABLES ###
TXT_FIC_LISTING_PATH = '/home/maria/Documents/TFG/txt_fic_paths.txt'

### FUNCTIONS ###

def ie_preprocess(document): #divide raw text into words and tag them	
	sentences = nltk.sent_tokenize(document) #sentence segmentation
	sentences = [nltk.word_tokenize(sent) for sent in sentences] #tokenization
	sentences = [nltk.pos_tag(sent) for sent in sentences] #POS tagging
	
	return sentences

def get_processed_fanfics(): #gets the paths to the fics, opens them
                   #and concatenates their textin a string
	fic_paths = []
	fic_paths_file = open(TXT_FIC_LISTING_PATH, 'r')

	for path in fic_paths_file.readlines():
		fic_paths.append(path[:-1])

	fic_paths_file.close()
	
	fic_text=''
	for path in fic_paths:
		txt_file = open(path, 'r')
		fic_text=fic_text+txt_file.read()
		txt_file.close()

	preprocessed_fics = ie_preprocess(fic_text)

	return preprocessed_fics

		
### Open and get text from txt file
proc_fic_text = get_processed_fanfics()
f=open('/home/maria/Documents/TFG/TFG_fics/txt/BlessedCursed_Retirement_train.txt', 'r')
fic_text=f.read()
f.close()

proc_fic_text=ie_preprocess(fic_text)
print(len(proc_fic_text))

### NER chunking ###
result=nltk.ne_chunk(proc_fic_text) #Entity extraction


#print(result.pos()) #debug

### Store individual entities in lists ###
people=[] #Store entities tagged 'PERSON' here
locations=[] #Store entities tagged 'LOCATION' here
organizations=[] #Store entities tagged 'ORGANIZATION' Here
dates=[] #Store entities tagged 'DATE' Here
gpes=[] #Store entities tagged 'GPE' Here
facilities=[] #Store entities tagged 'FACILITY' Here

for chunk in result.pos(): #result.pos() returns the leaves of the tree with their tags
	
	if chunk[1] == 'PERSON' and chunk[0][0] not in people:
		#print(chunk[0],chunk[1]) #debug
		people.append(chunk[0][0])

	elif chunk[1] == 'LOCATION' and chunk[0][0] not in locations:
		locations.append(chunk[0][0])

	elif chunk[1] == 'ORGANIZATION' and chunk[0][0] not in organizations:
		organizations.append(chunk[0][0])

	elif chunk[1] == 'DATE' and chunk[0][0] not in dates:
		dates.append(chunk[0][0])

	elif chunk[1] == 'GPE' and chunk[0][0] not in gpes:
		gpes.append(chunk[0][0])

	elif chunk[1] == 'FACILITY'and chunk[0][0] not in facilities:
		facilities.append(chunk[0][0])
	"""
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
	"""

entities=people+locations+organizations+dates+gpes+facilities
print('PEOPLE: \n', people)
print('LOCATIONS: \n', locations)
print('ORGANIZATIONS: \n', organizations)
print('DATES: \n', dates)
print('GPES: \n', gpes)
print('FACILITIES: \n', facilities)


aux=open('./output.txt','w')
for element in entities:
	aux.write(str(element)+'\n')

aux.close()

#print(result)
#result.draw() #requires Tkinter library


