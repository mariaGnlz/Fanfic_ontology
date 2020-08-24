#!/bin/bash/python3

# A POS tagger that processes and tags a set of texts stored in HTML files and dumps its output into a CSV

import nltk, re, pprint, sys, time, pandas, html2text
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from bs4 import BeautifulSoup

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
POS_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_tags.csv'
TYPICAL_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/typical_txt_paths.txt'
TYPICAL_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_typical_tags.csv'

### FUNCTIONS ###

def tag_fics(fic_list): #divide raw text into words and tag them	
	fic_sentences = [sent_tokenize(fic) for fic in fic_list]	
	processed_fics = [[pos_tag(word_tokenize(sent)) for sent in fic] for fic in fic_sentences]

	return processed_fics

def clean_text(text, chapter_titles):
	headers_and_footers = ['See the end of the chapter for more notes', 'See the end of the chapter for notes', 'Summary', 'Chapter Summary', 'Chapter Notes', 'Notes', 'Chapter End Notes']
	headers_and_footers.extend(chapter_titles)

	fic_text = ''
	for line in text.splitlines():
		if line == '## Afterword': break
		if line not in headers_and_footers and '> ' != line[:2]: fic_text += line+'\n'

	return fic_text

def remove_metadata(text, first_title):
	chapter_header_index1 = text.find('See the end of the chapter for more notes')
	chapter_header_index2 = text.find('See the end of the chapter for notes')
	chapter_header_index3 = text.find(first_title)
	
	fic_text = ''
	if chapter_header_index1 < 0 and chapter_header_index2 < 0:
		fic_text = text[chapter_header_index3:]
		
	elif chapter_header_index1 > 0:
		if chapter_header_index1 < chapter_header_index2: fic_text = text[chapter_header_index1:]
		else: fic_text = text[chapter_header_index2:]
	else: fic_text = text[chapter_header_index2:]
	
	
	""" #debug
	f = open('no_metadata.txt', 'w')
	f.write(fic_text)
	f.close()
	"""

	return fic_text

def get_plain_text(path):
	page = open(path, 'r').read()
	soup = BeautifulSoup(open(path, 'r'), 'html.parser')
	
	#Get number of chapters with BeautifulSoup
	chapter_titles = ['## '+header.text for header in soup.find_all('h2', class_='heading')]
	num_chapters = len(chapter_titles)

	if num_chapters == 0: #this fic only has one chapter
		title = soup.find('h1').text
		chapter_titles = ['## '+title]

	#print(chapter_titles) #debug


	#Take HTML tags out with HTML2text
	to_text = html2text.HTML2Text()
	to_text.ignore_images = True
	to_text.ignore_links = True

	text = to_text.handle(page)

	""" #debug
	f = open('htmlfic.txt', 'w')
	f.write(text)
	f.close()
	"""

	#Take author notes and metadata out
	fic_text = remove_metadata(text, chapter_titles[0])
	fic_text = clean_text(fic_text, chapter_titles)

	""" #debug
	f = open('text.txt', 'w')
	f.write(fic_text)
	f.close()
	"""

	return fic_text

def get_tagged_fanfics(start, end, typical): #gets the paths to the fics, opens them
                   #and stores their text in a list
	if typical == 0:
		paths_file = open(FIC_LISTING_PATH, 'r')
	else: 
		paths_file = open(TYPICAL_LISTING_PATH, 'r')

	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()
	fic_paths = fic_paths[start:end]

	untagged_fics = []
	fic_nums = []
	for path in fic_paths:
		num_fic=int((path.split('_')[3]).split('.')[0])
		if typical == 0: text = get_plain_text(path)
		else: text = open(path, 'r').read()

		untagged_fics.append(text)
		fic_nums.append(num_fic)

	#print(untagged_fics[0]) #debug
	tagged_fics = tag_fics(untagged_fics)

	return zip(tagged_fics, fic_nums)
	#return fic_text

def traverse(t, num_fic, num_sentence, iob_str):
	rows = []
	for node in t:
		if type(node) is nltk.Tree:
			#print(node.label()) #debug

			#iob_str = node.label()
			auxrows = traverse(node, num_fic, num_sentence, iob_str)
			rows.extend(auxrows)
			
	
		else: 
			#print('Word: ',node) #debug
			rows.append((num_fic, num_sentence, node[0], node[1], iob_str))

			iob_str = ''

	return rows

def save_to_csv(fic_list, typical):
	# Create pandas dataframe to store data
	df = pandas.DataFrame(columns=['Fic number', 'Sentence number', 'Word', 'POS', 'IOB'])
	#I'm not doing IOB tags on this program, but I'll do it in the future so I'm already adding a column for it

	# Loop to explore the tagged chunks in tagged_fics
	total_sentences = 0

	rows = []
	start = time.time() 
	for fic, num_fic in fic_list:
		num_sentence = 0
		for sentence in fic:
			#auxfic, auxsen, auxwords, auxpos, auxiob = traverse(sentence, count, num_fic, num_sentence)
			auxrows = traverse(sentence, num_fic, num_sentence, '')
			rows.extend(auxrows)
		
			num_sentence+=1
		total_sentences+=num_sentence
	
	end = time.time()

	if total_sentences > 0: 
		print(total_sentences, 'sentences in ',(end-start)/60,'minutes')
		### Unzip the tuples into columns and save results to csv file 
		columns = list(zip(*rows))

		df['Fic number'] = columns[0]
		df['Sentence number'] = columns[1]
		df['Word'] = columns[2]
		df['POS'] = columns[3]
		df['IOB'] = columns[4]

		#df.to_csv(POS_TAGGED_FICS_PATH, mode='a', index=False, encoding='ISO-8859-1')
		if typical == 0:
			df.to_csv(POS_TAGGED_FICS_PATH, mode='w', index=False)
		else:
			df.to_csv(TYPICAL_TAGGED_FICS_PATH, mode='w', index=False)
	
	else:
		print('Ocurrió algún problema procesando el fic ',num_fic)
		f = open('fic_problems.txt','a')
		f.write('Problem ocurred on fic '+str(num_fic)+'\n')
		f.close()

def get_last_tagged_fics():
	csv_file = pandas.read_csv(POS_TAGGED_FICS_PATH)
	last_tagged = csv_file['Fic number'][len(csv_file['Fic number'])-1]
	num_fics = len(set(csv_file['Fic number']))

	return last_tagged, num_fics

### M A I N ###
if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])
	#print(type(start_index), end_index) #debug

	### Open and get text from HTML files
	fic_list = get_tagged_fanfics(start_index, end_index, 0) #returns list of tagged fanfics
	save_to_csv(fic_list, 0)

elif len(sys.argv) == 2:
	if sys.argv[1] == 'd': 
		last_tagged, num_fics = get_last_tagged_fics()
		print('Number of tagged fics: ',num_fics,'\nID of last tagged fic: ',last_tagged)
	elif sys.argv[1] == 't':
		fic_list = get_tagged_fanfics(0,2, 1)
		save_to_csv(fic_list, 1)

elif len(sys.argv) == 1:
	### Open and get text from HTML files
	fic_list = get_tagged_fanfics(0,10, 0) #debug #more than 500 at once seems to be too much
	save_to_csv(fic_list, 0)

else:
	print('Error. Correct usage: \nPOS_tagger.py \nNPOS_tagger.py [start_index] [end_index] \nPOS_tagger d')




