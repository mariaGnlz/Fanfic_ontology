#!/bin/bash/python3

from stanza.server import CoreNLPClient

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

class CoreClient():

	def parse(self, fic_chapters):
		#First we check that all chapters are strings, and none of them are longer than 100000 caracters
		for i, chapter in enumerate(fic_chapters):
			if not type(chapter) is str: raise TypeError("[corenlp_wrapper] The input for the client must be a string")
			elif len(chapter) > 100000: 
				div_chapters = split_chapter(chapter)
				fic_chapters[i:i] = div_chapters

		

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
