#!/usr/bin/bash/python3

from bs4 import BeautifulSoup
from stanza.server import Document

import string, html2text, sys


### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
#TXT_LISTING_PATH = '/'
#SsAVE_TXT_PATH = '/home/maria/Documents/pruebasNLTK/trial_e_fics/'
TXT_LISTING_PATH = '/home/maria/Documents/pruebasNLTK/trial_e_txt_paths.txt'

### FUNCTIONS ###
#def clean_text(text, chapter_titles):
def clean_text(text, num_chapters, num_fic):
	headers_and_footers = ['See the end of the chapter for more notes', 'See the end of the chapter for notes', 'Summary', 'Chapter Summary', 'Chapter Notes', 'Notes', 'Chapter End Notes']
	#headers_and_footers.extend(chapter_titles)
	if num_chapters == 0: num_chapters += 1

	errorstr = '?\n'
	chapters = []
	for i in range(0,num_chapters):
		header1_index = text.find('## ')

		if header1_index < 0: #esto no deberia pasar
			print("Error on fanfic ", num_fic,": menos de 0")
			errorstr = "menos de 0\n"
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
	
	if len(clean_chapters) != num_chapters: #something went wrong
		print("Chapters of fic number ", num_fic, " were improperly processed") #debug
		f = open('clean_text_problems.txt', 'a')
		ficid = "Num fic: "+str(num_fic)+"\n"
		ficchapters = str(num_chapters)+"\n" 
		f.write(ficid)
		f.write(ficchapters)
		f.write(text[:10000])
		f.write("=====================================================")
		f.close()

	"""
	fic_text = ''
	for line in text.splitlines():
		if line == '## Afterword': break
		if line not in headers_and_footers and '> ' != line[:2] and '## ' != line[:3]: fic_text += line+'\n'

	"""
	#print(fic_text[:10000]) #debug

	return clean_chapters

def remove_metadata(text):
	index1 = text.find('See the end of the chapter for more notes')
	index2 = text.find('See the end of the chapter for notes')
	index3 = text[3:].find('## ')
	chapter_header_indexes = [index1, index2, index3]

	#print(text[:1000]) #debug

	while -1 in chapter_header_indexes: chapter_header_indexes.remove(-1) #Remove unvalid indexes
	
	fic_text = ''
	
	if len(chapter_header_indexes) == 1: fic_text = text[chapter_header_indexes[0]:]
	else:
		index = min(chapter_header_indexes)
		fic_text = text[index:]
	

	#print(fic_text[:1000]) #debug
	#print(chapter_header_index1, chapter_header_index2, chapter_header_index3) #debug
	
	
	""" #debug
	f = open('no_metadata.txt', 'w')
	f.write(fic_text)
	f.close()
	"""

	return fic_text

def get_chapterised_fic(path, num_fic): #Transforms the HTML file in a list of chapters (a list of str)
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
	chapterised_fic = clean_text(fic_text, num_chapters, num_fic)

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

def get_fanfics(start, end, slicing): #gets the paths to the fics, opens them
                   #and stores them in chapterised form in a list of Fanfic objects
	paths_file = open(FIC_LISTING_PATH, 'r')
	fic_paths = [line[:-1] for line in paths_file.readlines()]
	paths_file.close()

	if slicing: fic_paths = fic_paths[start:end] #slices the list, if not all of it is required

	fic_list = []
	for path in fic_paths:
		num_fic=int((path.split('_')[3]).split('.')[0])
		chapterised_fic = get_chapterised_fic(path, num_fic)
		fic_list.append(Fanfic(num_fic, chapterised_fic, None, None, None))

	return fic_list

### CLASSES ###

class Fanfic():
	def __init__(self, index, chapters, annotations, characters, sentences):
		self.index = index
		self.chapters = chapters
		self.annotations = annotations
		self.characters = characters
		self.sentences = sentences

	def set_chapters(self, new_chapters):
		self.chapters = new_chapters

	def get_chapter(self, index):
		return self.chapters[index]

	def get_string_chapters(self):
		chaps = ''
		for chapter in self.chapters: chaps += chapter+'\n'


		return chaps

	def set_annotations(self, ann):
		self.annotations = ann


class FanficGetter():
	def get_fanfics_in_range(self, start_index, end_index):
		fic_list = get_fanfics(start_index, end_index, True)


		return fic_list

	def get_fanfics_in_list(self):
		fic_list = get_fanfics(0, 0, False)

		return fic_list

	def get_fic_paths_in_range(self, start_index, end_index):
		paths_file = open(FIC_LISTING_PATH, 'r')
		fic_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()
		fic_paths = fic_paths[start_index:end_index]

		return fic_paths

	def get_fic_paths_in_list(self):
		paths_file = open(FIC_LISTING_PATH, 'r')
		fic_paths = [line[:-1] for line in paths_file.readlines()]
		paths_file.close()

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

		index = 0
		ships = ''
		for dt in dt_inf:
			#print(dt) #debug
			if 'Relationship:' not in dt.text: index += 1
			else: 
				ships = dd_inf[index].text
				break

		#print(ships) #debug
		ships = ships.split(',')
		if len(ships) == 1 and ships[0] == '': ships = []
		else:
			for i in range(len(ships)):
				if ' (Good Omens)' in ships[i]: ships[i] = ships[i][:-len(' (Good Omens)')]

		return ships

	def get_tags(self, fic_path):
		filehandle = open(fic_path, 'r').read()
		soup = BeautifulSoup(filehandle, 'html.parser')

		dt_inf = soup.find_all('dt')
		dd_inf = soup.find_all('dd')

		tags = ''
		index = 0
		for dt in dt_inf:
			if 'Archive Warning:' not in dt.text: index +=1
			else:
				tags = dd_inf[index].text

		tags += ', '
		index = 0
		for dt in dt_inf:
			if 'Additional Tags:' not in dt.text: index += 1
			else:
				tags += dd_inf[index].text

		#print(tags) #debug
		tags = tags.split(',')
		if len(tags) == 1 and tags[0] == '': tags = [] #I don't think this ever happens, but just in case
		else:
			tags = [tag.strip() for tag in tags]
			for i in range(len(tags)):
				if ' (Good Omens)' in tags[i]: tags[i] = tags[i][:-len(' (Good Omens)')]

		return tags
		

	def get_characters(self, fic_path):
		filehandle = open(fic_path, 'r').read()
		soup = BeautifulSoup(filehandle, 'html.parser')
		dt_inf = soup.find_all('dt')
		dd_inf = soup.find_all('dd')
		#print(len(dt_inf), len(dd_inf)) #debug
		
		index = 0
		chars = ''
		for dt in dt_inf:
			#print(dt) #debug
			if 'Character:' not in dt.text: index += 1
			else :
				chars = dd_inf[index].text
				break

		#print(chars) #debug
		chars = chars.split(',')
		if len(chars) == 1 and chars[0] == '': chars = []
		else:
			for i in range(len(chars)):
				if ' (Good Omens)' in chars[i]: chars[i] = chars[i][:-len(' (Good Omens)')]

		return chars

	def get_fandoms(self, fic_path):
		filehandle = open(fic_path, 'r').read()
		soup = BeautifulSoup(filehandle, 'html.parser')
		dt_inf = soup.find_all('dt')
		dd_inf = soup.find_all('dd')
		#print(len(dt_inf), len(dd_inf)) #debug
		
		index = 0
		fandoms = ''
		for dt in dt_inf:
			#print(dt) #debug
			if 'Fandom:' not in dt.text: index += 1
			else :
				fandoms = dd_inf[index].text
				break

		#print(chars) #debug
		fandoms = fandoms.split(',')
		if len(fandoms) == 1 and fandoms[0] == '': fandoms = [] #does this ever happen?
		else: fandoms = [fandom.strip() for fandom in fandoms]

		return fandoms

	def get_title(self, fic_path):
		filehandle = open(fic_path, 'r').read()
		soup = BeautifulSoup(filehandle, 'html.parser')
		h1 = soup.find('h1')
		#print(len(h1)) #debug

		return h1.text
		



