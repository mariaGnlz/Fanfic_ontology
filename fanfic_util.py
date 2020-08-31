#!/usr/bin/bash/python3

from bs4 import BeautifulSoup

import string, html2text, sys


### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
#TXT_LISTING_PATH = '/'
#SAVE_TXT_PATH = '/home/maria/Documents/pruebasNLTK/trial_e_fics/'
TXT_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/trial_e_txt_paths.txt'

### FUNCTIONS ###
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

def clean_fanfics(start, end): #gets the paths to the fics, opens them
                   #and stores their text in a list
	paths_file = open(FIC_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()
	fic_paths = fic_paths[start:end]

	untagged_fics = []
	#fic_nums = []
	for path in fic_paths:
		#num_fic=int((path.split('_')[3]).split('.')[0])
		text = get_plain_text(path)
		untagged_fics.append(text)
		#fic_nums.append(num_fic)

	#print(untagged_fics[0]) #debug
	#tagged_fics = tag_fics(untagged_fics)

	return zip(untagged_fics, fic_paths)
	#return untagged_fics

class FanficCleaner():
	def clean_fanfics_in_range(self, start_index, end_index):
		fic_list = clean_fanfics(start_index, end_index)
		#fic_texts = [fic for fic, _ in fic_list]
		#for fic, _ in fic_list:

		return fic_list

	def clean_fanfic_list(self, html_fic_list, save):
		clean_fics = []
		for _, path in html_fic_list:
			fic_text = get_plain_text(path)
			clean_fics.append((fic_text, path))
		
		if save:
			save_txt_fics(clean_fics)
	
		return clean_fics

	def save_txt_fanfics(fic_list):
		for fic, path in fic_list:
			path_tokens = path.split('/')
			fic_name = path_tokens[7:][0]
			#print(fic_name)
			new_path = SAVE_TXT_PATH + fic_name[:-4] +'txt'

			#print(new_path) #debug
		
			f = open(new_path, 'w')
			f.write(fic)
			f.close()

			f = open(TXT_LISTING_PATH, 'a')
			f.write(new_path+'\n')
			f.close()

	def set_fic_listing_path(self, new_fic_listing):
		global FIC_LISTING_PATH
		FIC_LISTING_PATH = new_fic_listing

	def set_save_txt_path(self, new_fic_save_path):
		global SAVE_TXT_PATH
		SAVE_TXT_PATH = new_fic_save_path

	def set_txt_listing_path(self, new_txt_listing_path):
		global TXT_LISTING_PATH
		TXT_LISTING_PATH = new_txt_listing_path
	def get_fic_listing_path(self): return FIC_LISTING_PATH

	def get_save_txt_path(self): return SAVE_TXT_PATH
	
	def get_txt_listing_path(self): return TXT_LISTING_PATH

class FanficGetter():
	def get_fanfic_paths_in_range(self, start, end):
		paths_file = open(FIC_LISTING_PATH, 'r')
		fic_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()
		
		return fic_paths

	def get_txt_fanfics_in_range(self, start, end):
		paths_file = open(TXT_LISTING_PATH, 'r')
		fic_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()

		txt_fics = []
		
		for i in range(start, end):
			path = fic_paths[i]
			txt_fics.append(open(path, 'r').read())
		
		return txt_fics
	def get_all_txt_fanfics(self):
		paths_file = open(TXT_LISTING_PATH, 'r')
		fic_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()

		txt_fics = []
		
		for path in fic_paths:
			txt_fics.append(open(path, 'r').read())
		
		return txt_fics

	def get_html_fanfics_in_range(self, start, end):
		paths_file = open(FIC_LISTING_PATH, 'r')
		fic_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()

		html_fics = []
		
		for i in range(start, end):
			path = fic_paths[i]
			text = open(path, 'r').read()
			html_fics.append((text,path))
		
		return html_fics

	def set_txt_fic_listing_path(self, new_fic_txt_listing):
		global TXT_LISTING_PATH
		TXT_LISTING_PATH = new_fic_txt_listing

	def set_fic_listing_path(self, new_fic_listing):
		global FIC_LISTING_PATH
		FIC_LISTING_PATH = new_fic_listing
	
	def get_txt_fic_listing_path(self): return TXT_LISTING_PATH

	def get_fic_listing_path(self): return FIC_LISTING_PATH

class FanficHTMLHandler():
	def get_chapters(self, fic_path):
		filehandle = open(fic_path, 'r').read()
		soup = BeautifulSoup(filehandle, 'html.parser')
		meta_inf = soup.find_all('dd') #chapters are displayed as '# of current chapters / total # of chapters'

		meta_chapters = meta_inf[len(meta_inf)-1].text
		#print(chapters) #debug

		if 'Chapters:' not in meta_chapters: #this means that the fic only has one chapter
			return [1,1]

		else:
			lines = meta_chapters.split('\n')
			for line in lines:
				if 'Chapters:' in line:
					chapters = line[20:].split('/')
					#print(chapters)#debug
			
			return chapters

	def get_rating(self, fic_path):
		filehandle = open(fic_path, 'r').read()
		soup = BeautifulSoup(filehandle, 'html.parser')
		rating_link = soup.find(class_='tags').find('a')
		#print(rating_link.text)#debug

		return rating_link.text

	def get_relationships(self, fic_path):
		filehandle = open(fic_path, 'r').read()
		soup = BeautifulSoup(filehandle, 'html.parser')
		dt_inf = soup.find_all('dt')
		dd_inf = soup.find_all('dd')
		#print(len(dt_inf), len(dd_inf)) #debug

		counter = 0
		ships = ''
		for dt in dt_inf:
			#print(dt) #debug
			if 'Relationship:' not in dt.text: counter += 1
			else: 
				ships = dd_inf[counter].text
				break

		#print(ships) #debug
		ships = ships.split(',')
		ships = [ship[:-len(' (Good Omens)')] for ship in ships]

		return ships
		

	def get_characters(self, fic_path):
		filehandle = open(fic_path, 'r').read()
		soup = BeautifulSoup(filehandle, 'html.parser')
		dt_inf = soup.find_all('dt')
		dd_inf = soup.find_all('dd')
		#print(len(dt_inf), len(dd_inf)) #debug
		
		counter = 0
		chars = ''
		for dt in dt_inf:
			#print(dt) #debug
			if 'Character:' not in dt.text: counter += 1
			else :
				chars = dd_inf[counter].text
				break

		#print(chars) #debug
		chars = chars.split(',')
		chars = [char[:-len(' (Good Omens)')] for char in chars]

		return chars



