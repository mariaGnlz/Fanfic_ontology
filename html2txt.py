#!/bin/bash/python3

from bs4 import BeautifulSoup

### VARIABLES ###
HTML_FIC_LISTING_PATH='/home/maria/Documents/TFG/html_fic_paths.txt'

### FUNCTIONS ###
def cleanHTMLTags(unclean_html):	#remove HTML tags from text
	clean_text=[]	
	for line in unclean_html.split('\n'):
		#print(line) #debug
		clean_text.append(line)

	return clean_text

def createFicName(original_name, fic_number, max_number): #creates a new filename for the .txt from the original one
	new_name=original_name.replace(' ', '_')
	new_name=new_name.replace('html','txt')
	prefix=new_name[:-4]
	suffix=new_name[-4:]
	
	#print(prefix, suffix) #debug
	
	if fic_number<max_number: #75% of the fanfics will be used in traning, the other 15% for testing
		new_name=prefix+'_train'+suffix
	else:
		new_name=prefix+'_test'+suffix

	#print(new_name) #debug
	
	return new_name
	


### MAIN ###

### Find HTML document(s) and parse it ###
fic_paths=open(HTML_FIC_LISTING_PATH, 'r')
#print(fic_paths.readline()[:-1]) #debug

paths=[]
for path in fic_paths.readlines():	#store each fic listed in fic_paths.txt in a list
	#print(path) #debug
	paths.append(path)

fic_paths.close()

percentage_training_dataset=len(paths)*0.75 #75% of the fanfics will be used in traning, the other 15% for testing
#print(percentage_training_dataset) #debug

fic_number=1
for path in paths:	#open each fic with f.open(), remove HTML tags, save in .txt file
	fic=open(path[:-1])
	#print(fic.name) #debug

	parsed_fic=BeautifulSoup(fic, features='lxml')
	fic_chapters=parsed_fic.body.find('div', attrs={'class':'userstuff'}) #select the actual chapter(s) text from the HTML
	#print(fic_chapters.text) #debug

	clean_fic=cleanHTMLTags(fic_chapters.text)

	
	txt_filename=createFicName(fic.name, fic_number, percentage_training_dataset)
	fic_number=fic_number+1
	
	txt_file=open(txt_filename, 'w') #write fanfic text in a txt file
	for line in clean_fic:
		txt_file.write(line)

	txt_file.close()
	
	fic.close()


