#!/bin/bash/python3

from stanza.server import CoreNLPClient

class CoreClient():

	def __init__(self):
		print("\n###### Starting client and calling CoreNLP server ######\n")

	def parse(self, fic_chapters):
		for chapter in fic_chapters:
			if not type(chapter) is str: raise TypeError("[corenlp_client] The input for the client must be a string")
			elif len(chapter) > 100000: raise Exception("[corenlp_client] String input must have less than 100000 caracters")

		annotations = []
		with CoreNLPClient(
			annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse','coref'],
		        timeout=120000,
			be_quiet = True,
		        memory='4G') as client:
				print("Annotating data . . .")

				for chapter in fic_chapters: annotations.append(client.annotate(chapter))
				fic.set_annotations(annotations)

				print("...done")

		return annotations
