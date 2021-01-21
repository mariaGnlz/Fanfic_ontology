#!/usr/bin/bash/python3

from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize, sent_tokenize
from fanfic_util import *
from NER_tagger import NERTagger
from corenlp_util import CoreNLPDataProcessor, CoreWrapper

import sys, time, random, pandas

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
FIC_NAME_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_fics/html/'

MAX_FIC_CHARACTERS = 50000

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

def calculate_sentiment_percent(fic_sentiment):
	total = fic_sentiment['Num sentences']
	fic_sentiment.pop('Num sentences')

	sentiment_percents = []
	for _, count in fic_sentiment.items():
		sentiment_percents.append(count*100/total)

	return sentiment_percents
		

### MAIN ###
getter = FanficGetter()
handler = FanficHTMLHandler()

if len(sys.argv) == 1:
	print('Fetching fanfic...')

	fic_not_found = True
	while fic_not_found:
		fic_id = random.randint(0,20190)
		fic_path = FIC_NAME_PATH+'gomensfanfic_'+str(fic_id)+'.html'
		#print(fic_id, fic_path) #debug

		fic = getter.get_fanfics_in_range(fic_id, fic_id+1)
		fic = fic[0]

		if len(fic.get_string_chapters()) < MAX_FIC_CHARACTERS: fic_not_found = False

	print('Fic #'+str(fic.index)+' fetched.')

	print('Tagging characters with NERTagger...')
	start = time.time()
	nertagger_characters = tag_with_NERTagger(fic)
	#for char in nertagger_characters: print(char) #debug
	end = time.time()  
	print('...done in '+str((end-start)/60)+' minutes.')

	annotated_fic = call_corenlp(fic)
	#print(len(annotated_fic)) #debug
	annotated_fic = annotated_fic[0]

	print('Processing CoreNPL data...')
	coreProcessor = CoreNLPDataProcessor(annotated_fic)
	coreProcessor.extract_fic_characters()
	core_characters = coreProcessor.fic.characters
	#print(type(core_characters)) #debug

	fic_sentiment = coreProcessor.extract_fic_sentiment()
	#print(fic_sentiment) #debug

	print('...data processed.')
	fic_title = handler.get_title(fic_path)

	print('-- DATA FOR FANFIC #'+str(fic.index)+' --\n')
	print('·Title: '+fic_title)
	print('·NERTagger characters:	{:<8} {:<30} {:<10}'.format('Canon ID','Name','Mentions'))
	for character in nertagger_characters:
		try: print('			{:<8} {:<30} {:<10}'.format(character['Canon ID'], character['Name'],character['Mentions']))
		except TypeError: print(character) #debug

	print('\n')

	print('·CoreNLP characters:	{:<8} {:<20} {:<10} {:<10} {:<10} {:<10} {:<20}'.format('Canon ID','Name','MALE','FEMALE','NEUTRAL','UNKNOWN','Other names'))
	for character in core_characters:
		try: print('			{:<8} {:<20} {:<10} {:<10} {:<10} {:<10} {:<20}'.format(character['Canon ID'], character['Name'],character['Male mentions'],character['Female mentions'],character['Neutral mentions'],character['Unknown mentions'],character['Other names']))
		except TypeError: print(character) #debug

	print('\n')

	#percentages = calculate_sentiment_percentages(fic_sentiment)	
	print('·Sentiment:	{:<10} {:<15} {:<15} {:<15} {:<15} {:<15} {:<15}'.format('Sentences','Very positive','Positive','Neutral','Negative','Very negative','Weighted avg'))
	print('		{:<10} {:<15} {:<15} {:<15} {:<15} {:<15} {:<15}'.format(fic_sentiment['Num sentences'],fic_sentiment['Very positive'],fic_sentiment['Positive'],fic_sentiment['Neutral'],fic_sentiment['Negative'],fic_sentiment['Very negative'], fic_sentiment['Weighted average']))
	print('\n\n')
	

elif len(sys.argv) == 2:
	try: 
		fic_id = int(sys.argv[1])
		fic_path = FIC_NAME_PATH+'gomensfanfic_'+sys.argv[1]+'.html'
		print(fic_id, fic_path) #debug

		if fic_id < 0 or fic_id > 20190: raise ValueError

	except ValueError:
		print('Fic index must be a natural number between 0 and 20190')
		sys.exit()

	print('Fetching fanfic #'+str(fic_id)+'...')
	fic = getter.get_fanfic_in_path(fic_path)
	

	print('Tagging characters with NERTagger...')
	start = time.time()
	nertagger_characters = tag_with_NERTagger(fic)
	#for char in nertagger_characters: print(char) #debug
	end = time.time()  
	print('...done in '+str((end-start)/60)+' minutes.')

	annotated_fic = call_corenlp(fic)
	#print(len(annotated_fic)) #debug
	annotated_fic = annotated_fic[0]

	print('Processing CoreNPL data...')
	coreProcessor = CoreNLPDataProcessor(annotated_fic)
	coreProcessor.extract_fic_characters()
	core_characters = coreProcessor.fic.characters
	#print(type(core_characters)) #debug

	fic_sentiment = coreProcessor.extract_fic_sentiment()
	#print(fic_sentiment) #debug

	print('...data processed.')
	fic_title = handler.get_title(fic_path)
	fic_character_tags = handler.get_characters(fic_path)
	character_tags = ''
	for tag in fic_character_tags: character_tags += tag+' '

	print('-- DATA FOR FANFIC #'+str(fic_id)+' --\n')
	print('·Title: '+fic_title)
	print('·Character tags: '+character_tags)
	print('·NERTagger characters:	{:<8} {:<30} {:<10}'.format('Canon ID','Name','Mentions'))
	for character in nertagger_characters:
		try: print('			{:<8} {:<30} {:<10}'.format(character['Canon ID'], character['Name'],character['Mentions']))
		except TypeError: print(character) #debug

	print('\n')

	print('·CoreNLP characters:	{:<8} {:<20} {:<10} {:<10} {:<10} {:<10} {:<20}'.format('Canon ID','Name','MALE','FEMALE','NEUTRAL','UNKNOWN','Other names'))
	for character in core_characters:
		try: print('			{:<8} {:<20} {:<10} {:<10} {:<10} {:<10} {:<20}'.format(character['Canon ID'], character['Name'],character['Male mentions'],character['Female mentions'],character['Neutral mentions'],character['Unknown mentions'],character['Other names']))
		except TypeError: print(character) #debug

	print('\n')

	#percentages = calculate_sentiment_percentages(fic_sentiment)	
	print('·Sentiment:	{:<10} {:<15} {:<15} {:<15} {:<15} {:<15} {:<15}'.format('Sentences','Very positive','Positive','Neutral','Negative','Very negative', 'Weighted avg'))
	print('		{:<10} {:<15} {:<15} {:<15} {:<15} {:<15} {:<15}'.format(fic_sentiment['Num sentences'],fic_sentiment['Very positive'],fic_sentiment['Positive'],fic_sentiment['Neutral'],fic_sentiment['Negative'],fic_sentiment['Very negative'], fic_sentiment['Weighted average']))
	print('\n\n')

else: print('Incorrect usage of program.py. Correct use: program.py, program.py <fic_index>')
