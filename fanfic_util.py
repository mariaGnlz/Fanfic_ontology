#!/usr/bin/bash/python3

from bs4 import BeautifulSoup

import string, html2text, sys


### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
#TXT_LISTING_PATH = '/'
#SAVE_TXT_PATH = '/home/maria/Documents/pruebasNLTK/trial_e_fics/'
TXT_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/trial_e_txt_paths.txt'

### FUNCTIONS ###
#def clean_text(text, chapter_titles):
def clean_text(text, num_chapters):
	headers_and_footers = ['See the end of the chapter for more notes', 'See the end of the chapter for notes', 'Summary', 'Chapter Summary', 'Chapter Notes', 'Notes', 'Chapter End Notes']
	#headers_and_footers.extend(chapter_titles)

	chapters = []
	for i in range(0,num_chapters):
		header1_index = text.find('## ')

		if header1_index < 0: print("menos de 0", text[:100]) #esto no deberia pasar
		else:
			header2_index = text[header1_index+3:].find('## ')
			chapters.append(text[header1_index:header2_index])

			#print(header1_index, header2_index) #debug

			text = text[header2_index:]
			#print(text[:100]) #debug
			#print("\n N E X T  C H A P T E R") #debug

	chapter_text = ''
	clean_chapters = []
	for chapter in chapters:
		for line in chapter.splitlines():
			if line not in headers_and_footers and '> ' != line[:2]: chapter_text += line+'\n'

		clean_chapters.append(chapter_text)
		chapter_text = ''
	


	"""
	fic_text = ''
	for line in text.splitlines():
		if line == '## Afterword': break
		if line not in headers_and_footers and '> ' != line[:2] and '## ' != line[:3]: fic_text += line+'\n'

	"""
	#print(fic_text[:10000]) #debug

	return clean_chapters

def remove_metadata(text):
	chapter_header_index1 = text.find('See the end of the chapter for more notes')
	chapter_header_index2 = text.find('See the end of the chapter for notes')
	chapter_header_index3 = text[3:].find('## ')

	#print(text[:10000])
	
	fic_text = ''
	if chapter_header_index1 < 0 and chapter_header_index2 < 0:
		fic_text = text[chapter_header_index3:]
		
	elif chapter_header_index1 > 0:
		if chapter_header_index1 < chapter_header_index2: fic_text = text[chapter_header_index1:]
		else: fic_text = text[chapter_header_index2:]
	elif chapter_header_index2>0:
		if chapter_header_index2 < chapter_header_index3: fic_text = text[chapter_header_index2:]
		else: fic_text = text[chapter_header_index3:]

	#print(fic_text[:10000]) #debug
	#print(chapter_header_index1, chapter_header_index2, chapter_header_index3) #debug
	
	
	""" #debug
	f = open('no_metadata.txt', 'w')
	f.write(fic_text)
	f.close()
	"""

	return fic_text

def get_chapterised_fic(path): #Transforms the HTML file in a list of chapters (a list of str)
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
	fic_text = remove_metadata(text)
	chapterised_fic = clean_text(fic_text, num_chapters)

	"""
	print(len(chapterised_fic)) #debug
	for chapter in chapterised_fic: #debug
		print(chapter[:100])
		print(". . .")
		print(chapter[-100:])

	#debug
	f = open('text.txt', 'w')
	f.write(fic_text)
	f.close()
	"""

	return chapterised_fic

def get_fanfics(start, end): #gets the paths to the fics, opens them
                   #and stores them in chapterised form in a list of Fanfic objects
	paths_file = open(FIC_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()
	fic_paths = fic_paths[start:end]

	fic_list = []
	for path in fic_paths:
		num_fic=int((path.split('_')[3]).split('.')[0])
		chapterised_fic = get_chapterised_fic(path)
		fic_list.append(Fanfic(num_fic, chapterised_fic, None))

	return fic_list

### CLASSES ###

class Fanfic():
	def __init__(self, index, chapters, annotations):
		self.index = index
		self.chapters = chapters
		self.annotations = annotations

	def get_chapter(self, index):
		return self.chapters[index]

	def set_annotations(self, ann):
		self.annotations = ann


class FanficGetter():
	def get_fanfics_in_range(self, start_index, end_index):
		fic_list = get_fanfics(start_index, end_index)


		return fic_list

	def get_fic_paths_in_range(self, start_index, end_index):
		paths_file = open(FIC_LISTING_PATH, 'r')
		fic_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()
		fic_paths = fic_paths[start_index:end_index]

		return fic_paths

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

	def get_fic_listing_path(self): return FIC_LISTING_PATH

	def get_save_txt_path(self): return SAVE_TXT_PATH



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



