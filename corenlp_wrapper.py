#!/bin/bash/python3

from stanza.server import CoreNLPClient
from stanza.server.client import TimeoutException
from fanfic_util import Fanfic
from urllib.error import HTTPError

import time

### VARIABLES ###
MAX_CHAPTER_LENGTH = 20000


### FUNCTIONS ###
def split_chapter(chapter):
	len_chapter = len(chapter)

	if len_chapter % MAX_CHAPTER_LENGTH == 0: divisions = int(len_chapter/MAX_CHAPTER_LENGTH)
	else: divisions = int(len_chapter/MAX_CHAPTER_LENGTH)+1

	div_chapters = []
	while len(chapter) > MAX_CHAPTER_LENGTH:
		div_chapters.append(chapter[:MAX_CHAPTER_LENGTH])
		chapter = chapter[MAX_CHAPTER_LENGTH:]

	if len(chapter) != 0: div_chapters.append(chapter)


	if len(div_chapters) != divisions: raise Exception("[corenlp_wrapper] An error ocurred while slicing chapters")

	return div_chapters

def compress_chapters(fic_chapters):
	compressed_chapters = []

	processed_chapters = 0
	while processed_chapters < len(fic_chapters):
		chapter_text = ''
		while len(chapter_text) < MAX_CHAPTER_LENGTH:
			chapter_text += fic_chapters[processed_chapters]
			processed_chapters += 1

		compressed_chapters.append(chapter_text)

	return processed_chapters

def process_fics(fics):
	if type(fics) == list:
		#Check that members of list are class Fanfic
		for i, fic in enumerate(fics):
			if type(fic) is not Fanfic: raise TypeError("[corenlp_wrapper2] The input for the client must be list of Fanfic, or a single Fanfic")
			else: #check that all chapters in fanfic are no longer than 100000 characters
				fic_chapters = fic.chapters

				for chapter in fic_chapters:
					#print(type(chapter), len(chapter))
					if len(chapter) > MAX_CHAPTER_LENGTH:
						print('BIG BOY CHAPTER')
						extra_chapters = split_chapter(chapter)
						fic_chapters.remove(chapter)

						position = i
						for extra_chap in extra_chapters:
							#print(len(extra_chap)) #debug
							fic_chapters.insert(position, extra_chap)
							position += 1

				#end FOR chapter

				fic.set_chapters(fic_chapters)
		
			#end ELSE
		#end FOR fic
	#end if TYPE(FICS) == LIST
	elif type(fics) == Fanfic:
		fic_chapters = fics.chapters

		for i,chapter in enumerate(fic_chapters):
			if len(chapter) > MAX_CHAPTER_LENGTH:
				extra_chapters = split_chapter(chapter)
				fic_chapters.remove(chapter)

				position = i
				for extra_chap in extra_chapters:
					fic_chapters.insert(position, extra_chap)
					position += 1

		fics.set_chapters(fic_chapters)


	return fics


### CLASSES ###
class CoreClient(): #This client works with lists of string, or individual string. Returns a list of annotations with the data from CoreNLP

	def parse(self, fic_chapters):
		if type(fic_chapters) == list:
			#First we check that all chapters are strings, and none of them are longer than 100000 caracters
			for i, chapter in enumerate(fic_chapters):
				if not type(chapter) is str: raise TypeError("[corenlp_wrapper] The input for the client must be a string")
				elif len(chapter) > MAX_CHAPTER_LENGTH: 
					extra_chapters = split_chapter(chapter)
					fic_chapters.remove(chapter)

					position = i
					for extra_chap in extra_chapters:
						fic_chapters.insert(position, extra_chap)
						position += 1

		elif type(fic_chapters) == str:
			if len(fic_chapters) > MAX_CHAPTER_LENGTH:
				extra_chapters = split_chapter(fic_chapters)
				fic_chapters = extra_chapters

			else: fic_chapters = [fic_chapters]

		else: raise TypeError("[corenlp_wrapper] The input for the client must be a list of string or a single string")

		

		

		annotations = []
		
		with CoreNLPClient(
			annotators = ['tokenize', 'sentiment', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse','coref'],
		        timeout=120000,
			be_quiet = True,
		        memory='4G') as client:
				print("Annotating data . . .")

				for chapter in fic_chapters: annotations.append(client.annotate(chapter))
				

				print("...done")
		
		return annotations

class CoreClient2(): #This client works with lists of Fanfic objects. Returns the same list, but each Fanfic object now has a list of annotations with the data from CoreNLP

	def parse(self, fics):
		fics = process_fics(fics)

		annotations = []
		
		try:
			with CoreNLPClient(
				annotators = ['tokenize', 'sentiment', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse','coref'],
				timeout=120000,
				be_quiet = True,
				memory='4G') as client:
					print("Annotating data . . .")

					for i, fic in enumerate(fics):
						print('fic #', i, 'has ',len(fic.chapters))
						annotations = []
						for i, chapter in enumerate(fic.chapters):
							print('chapter ',i,': ',len(chapter))
							ann = client.annotate(chapter)
							time.sleep(4)

							annotations.append(ann)
		
						fic.set_annotations(annotations)

		
			print("...done")

		except TimeoutException as e:
			print('CoreNLP TimeoutException')
			return fics, True

		
		return fics, False
