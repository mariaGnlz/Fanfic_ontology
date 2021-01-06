#!/usr/bin/bash/python3

from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize, sent_tokenize
from fanfic_util import *
from NER_tagger_v3 import NERTagger
from corenlp_util import CoreNLPDataProcessor, CoreWrapper

import sys, time, random

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
FIC_NAME_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_fics/html/'

### FUNCTIONS ###

def tag_with_NERTagger(fic):
	nerTagger = NERTagger()
	tagged_fic = []

	#tokenize fanfic
	for chapter in fic.chapters:
		tokens = [word_tokenize(sent) for sent in sent_tokenize(chapter)]
		tagged_chapter = [pos_tag(word) for word in tokens]

		tagged_fic.extend(tagged_chapter)

	#tag NERs with NERTagger
	ner_characters = nerTagger.parse(tagged_fic)

	return ner_characters

def call_corenlp(fic):
	client = CoreWrapper()

	print('\n## Starting CoreNLP server and processing fanfic. . .\n')
	start= time.time()


	annotated_fics, error = client.parse(fic)
	if error:
		print('Error: not all fanfics could be processed by the server')
		recovered_fics = []
		for fic in annotated_fics:
			if fic.annotations is not None: recovered_fics.append(fic)

		print('Program is continuing with ',len(recovered_fics),' of the original ',len(fics), 'fics')
		annotated_fics = recovered_fics

	

	end = time.time()
	print("Client closed. "+ str((end-start)/60) +" mins elapsed")

	return annotated_fics
		

### MAIN ###
getter = FanficGetter()
handler = FanficHTMLHandler()

if len(sys.argv) == 1:
	fic_id = random.randint(0,20190)
	fic_path = FIC_NAME_PATH+'gomensfanfic_'+str(fic_id)+'.html'
	print(fic_id, fic_path) #debug

	print('Fetching fanfic.')
	fic = getter.get_fanfics_in_range(fic_id, fic_id+1)
	fic = fic[0]

	print('Tagging characters with NERTagger...')
	start = time.time()
	ner_characters = tag_with_NERTagger(fic)
	print(ner_characters) #debug
	end = time.time()

	print('...done in '+str((end-start)/60)+' minutes.')

	annotated_fic = call_corenlp(fic)
	print(len(annotated_fic)) #debug
	annotated_fic = annotated_fic[0]

	print('Processing CoreNPL data...')
	coreProcessor = CoreNLPDataProcessor(annotated_fic)
	coreProcessor.extract_fic_characters()
	characters = coreProcessor.fic.get_characters()
	print(characters) #debug

	fic_sentiment = coreProcessor.extract_fic_sentiment()
	print(fic_sentimetn) #debug

	print('...data processed.')
	fic_title = handler.get_title(fic_path)

	print('-- DATA FOR FANFIC #'+str(fic_id))
	print('·Title: '+fic_title)
	print('·Characters: ')
	for character in annotated_fic.characters: print('	'+character['Name']+' ('+character['Gender']+')')

	print('·Sentiment:',fic_sentiment)
	

elif len(sys.argv) == 2:
	try: 
		fic_id = int(sys.argv[1])
		fic_path = FIC_NAME_PATH+'gomensfanfic_'+sys.argv[1]+'.html'
		print(fic_id, fic_path) #debug

		if fic_id < 0 or fic_id > 20190: raise ValueError

	except ValueError:
		print('Parameter must be a natural number between 0 and 20190')


	print('Fetching fanfic.')
	fic = getter.get_fanfics_in_range(fic_id, fic_id+1)
	fic = fic[0]

	print('Tagging characters with NERTagger...')
	start = time.time()
	ner_characters = tag_with_NERTagger(fic)
	print(ner_characters) #debug
	end = time.time()  
	print('...done in '+str((end-start)/60)+' minutes.')

	annotated_fic = call_corenlp(fic)
	#print(len(annotated_fic)) #debug
	annotated_fic = annotated_fic[0]

	print('Processing CoreNPL data...')
	coreProcessor = CoreNLPDataProcessor(annotated_fic)
	coreProcessor.extract_fic_characters(ner_characters)
	characters = coreProcessor.fic.characters
	print(characters) #debug

	fic_sentiment = coreProcessor.extract_fic_sentiment()
	print(fic_sentiment) #debug

	print('...data processed.')
	fic_title = handler.get_title(fic_path)

	print('-- DATA FOR FANFIC #'+str(fic_id))
	print('·Title: '+fic_title)
	print('·Characters: ')
	for character in annotated_fic.characters: print('	'+character['Name']+' ('+character['Gender']+')')

	print('·Sentiment:',fic_sentiment)
	
