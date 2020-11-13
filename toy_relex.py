#!/bin/bash/python3

import nltk, re, pprint
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from NER_tagger_v3 import NERTagger
from fanfic_util import FanficGetter, Fanfic
#from nltk.tree import Tree

### VARIABLES ###

VERB_TAGS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
### FUNCTIONS ###

fGetter = FanficGetter()
NERtagger = NERTagger()

fic_list = fGetter.get_fanfics_in_range(8,9)
#print(fic_list[0].get_chapter(0)) #debug

fic_chapters = fic_list[0].chapters
#print(type(fic_chapters[0])) #debug

fic_text = ''
for chapter in fic_chapters: fic_text+=chapter


fic_sents = sent_tokenize(fic_text)

pos_fic = [pos_tag(word_tokenize(sent)) for sent in fic_sents]
#print(pos_fic) #debug

char_list, ner_fic = NERTagger.parse(pos_fic)

#print(char_list[40][1]) #debug
#char_name1 = char_list[40][1]
char_name1 = "Crowley"
char_name2 = "Aziraphale"

for sent in ner_fic:
	leaves = sent.leaves()
	words = [word for word, _ in leaves]
	#plain = ' '.join(words)
	#plain = plain.strip()

	#if char_name1 in words and char_name2 in words: print(words)
	#verbs = [word for word, tag in leaves if tag in VERB_TAGS]

	for word, pos in leaves:
		"""
		if pos == 'NN' and word == char_name1: 
			print(sent)
			break
		
		"""
		if pos in VERB_TAGS and word == "love":
			print(sent)
			#Match tree structure to S->VB->Direct object, and extrat S (subject) and direct object
			break

	


