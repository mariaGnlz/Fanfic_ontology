#!/bin/bash/python3

# A POS tagger that processes and tags a set of texts stored in HTML files and dumps its output into a CSV

import nltk, re, pprint, time, pandas, html2text
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from bs4 import BeautifulSoup

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'

### FUNCTIONS ###

def tag_fics(fic_list): #divide raw text into words and tag them	
	fic_sentences = [sent_tokenize(fic) for fic in fic_list]	
	processed_fics = [[pos_tag(word_tokenize(sent)) for sent in fic] for fic in fic_sentences]

	return processed_fics

def parse_HTML(page):
	#soup = BeautifulSoup(page, 'html.parser')
	#chapter_header = '<!--chapter content-->'
	chapter_header = '<div class="userstuff">'
	chapter_footer = '<!--/chapter content-->'
	#chapter_nodes = (soup.find_all('div', class_='userstuff'))[1:] #the first node is metadata

	to_text = html2text.HTML2Text()
	fic_text=''
	while chapter_header in page and chapter_footer in page:
		header_index = page.find(chapter_header)
		footer_index = page.find(chapter_footer) + len(chapter_footer)
		text = page[header_index:footer_index]
		fic_text = fic_text+ to_text.handle(text)
	"""
	for chapter in chapter_nodes:
		fic_text = fic_text+to_text.handle(chapter.content)
	
	
	"""
	return fic_text

def get_tagged_fanfics(): #gets the paths to the fics, opens them
                   #and stores their text in a list
	paths_file = open(FIC_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()
	fic_paths = fic_paths[:10] #debug

	to_text = html2text.HTML2Text()
	to_text.ignore_images = True
	to_text.ignore_links = True
	
	fic_list = []
	for path in fic_paths:
		page = (open(path, 'r')).read()
		text = to_text.handle(page)
		fic_list.append(text)

	#print(fic_list[0]) #debug
	
	
	return tag_fics(fic_list)
	#return fic_text

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

### M A I N ###
		
### Open and get text from HTML files
start = time.time() 
tagged_fics = get_tagged_fanfics() #returns list of tagged fanfics

#print('Len: ', len(tagged_fics), '\n',tagged_fics) #debug
#print(tagged_fics[0])
#print(type(tagged_fics), type(tagged_fics[0]), type(tagged_fics[0][0]), type(tagged_fics[0][0][0])) #debug

# Create pandas dataframe to store data
df = pandas.DataFrame(columns=['Fic number', 'Sentence number', 'Word', 'POS', 'IOB'])
#I'm not doing IOB tags on this program, but I'll do in the future so I'm already adding a column for it

# Loop to explore the tagged chunks in tagged_fics
num_sentence = 0
num_fic = 0

rows = []
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

df.to_csv('POS_tags.csv', index=False)


