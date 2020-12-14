#!/bin/bash/python3

from stanza.server import CoreNLPClient
from fanfic_util import Fanfic

def split_chapter(chapter):
	len_chapter = len(chapter)

	divisions = int(len_chapter/100000)

	div_chapters = []	
	while len(chapter) > 99900:
		div_chapters.append(chapter[:99900])
		chapter = chapter[99900:]

	if len(chapter) != 0: div_chapters.append(chapter)


	if len(div_chapters) != divisions: raise Exception("[corenlp_wrapper] An error ocurred while slicing chapters")

	return div_chapters

def compress_chapters(fic_chapters):
	compressed_chapters = []

	processed_chapters = 0
	while processed_chapters < len(fic_chapters):
		chapter_text = ''
		while len(chapter_text) < 99900:
			chapter_text += fic_chapters[processed_chapters]
			processed_chapters += 1

		compressed_chapters.append(chapter_text)

	return processed_chapters

class CoreClient(): #This client works with lists of string, or individual string. Returns a list of annotations with the data from CoreNLP

	def parse(self, fic_chapters):
		if type(fic_chapters) == list:
			#First we check that all chapters are strings, and none of them are longer than 100000 caracters
			for i, chapter in enumerate(fic_chapters):
				if not type(chapter) is str: raise TypeError("[corenlp_wrapper] The input for the client must be a string")
				elif len(chapter) > 100000: 
					div_chapters = split_chapter(chapter)
					fic_chapters[i:i] = div_chapters

		elif type(fic_chapters) == str:
			if len(fic_chapters) > 100000:
				div_chapters = split_chapter(fic_chapters)
				fic_chapters = div_chapters

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
		if type(fics) == list:
			#Check that members of list are class Fanfic
			for i, fic in enumerate(fics):
				if type(fic) is not Fanfic: raise TypeError("[corenlp_wrapper2] The input for the client must be list of Fanfic, or a single Fanfic")
				else: #check that all chapters in fanfic are no longer than 100000 characters
					fic_chapters = fic.chapters

					for chapter in fic_chapters:
						if len(chapter) > 100000:
							div_chapters = split_chapter(chapter)
							fic_chapters[i:i] = div_chapters

					fic.set_chapters(fic_chapters)
	
		elif type(fics) == Fanfic:
			fic_chapters = fics.chapters

			for chapter in fic_chapters:
				if len(chapter) > 100000:
					div_chapters = split_chapter(chapter)
					fic_chapters[i:i] = div_chapters

			fics.set_chapters(fic_chapters)

		else: raise TypeError("[corenlp_wrapper2] The input for the client must be list of Fanfic, or a single Fanfic")

		

		

		annotations = []
		
		with CoreNLPClient(
			annotators = ['tokenize', 'sentiment', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse','coref'],
		        timeout=120000,
			be_quiet = True,
		        memory='4G') as client:
				print("Annotating data . . .")

				for fic in fics:
					annotations = []
					for chapter in fic.chapters: annotations.append(client.annotate(chapter))
	
					fic.set_annotations(annotations)
				

				print("...done")
		
		return fics
