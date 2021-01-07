#!/usr/bin/bash/python3

import time, pandas
#from corenlp_wrapper import CoreClient2
from stanza.server import Document
from stanza.server import CoreNLPClient
from stanza.server.client import TimeoutException
from urllib.error import HTTPError

from fanfic_util import *

### VARIABLES ###
CANON_DB = '/home/maria/Documents/Fanfic_ontology/canon_characters.csv'
ERRORLOG = '/home/maria/Documents/Fanfic_ontology/TFG_logs/corenlp_util_errorlog.txt'

FEMALE_TAGS = ['She/Her Pronouns for ', 'Female ', 'Female!', 'Female-Presenting ']
MALE_TAGS = ['He/Him Pronouns for ', 'Male ', 'Male!', 'Male-Presenting ']
NEUTRAL_TAGS = ['They/Them Pronouns for ', 'Gender-Neutral Pronouns for', 'Gender-Neutral ', 'Agender ', 'Genderfluid ', 'Androgynous ', 'Gender Non-Conforming ']

MAX_CHAPTER_LENGTH = 30000

### FUNCTIONS ###
def normalize_sentiment(sentences):
	sentiment_count = {'Num sentences':0, 'Very positive':0, 'Positive':0, 'Neutral':0, 'Negative':0, 'Very negative':0}
	sentiment_count['Num sentences'] = len(sentences)
	
	for sentence in sentences:
		sentiment = sentence.sentiment
		#print(sentiment) #debug
		sentiment_count[sentiment] += 1

		'''
		if sentiment == 'Very positive': sentiment_count += 2
		elif sentiment == 'Positive': sentiment_count += 1
		elif sentiment == 'Negative': sentiment_count -= 1
		elif sentiment == 'Very negative': sentiment_count -= 2
		'''

	return sentiment_count

def make_gender_tags(tags, character_name):
	for tag in tags:
		tag = tag+character_name

	return tags

def decide_gender(characters, canon_db):
	handler = FanficHTMLHandler()

	for character in characters:
		fic_link = '/home/maria/Documents/Fanfic_ontology/TFG_fics/html/gomensfanfic_'+str(character['ficID'])+'.html'
		fic_tags = handler.get_tags(fic_link)
		character_name = character['Name'].capitalize()

		f_gender = make_gender_tags(FEMALE_TAGS, character_name)
		m_gender = make_gender_tags(MALE_TAGS, character_name)
		n_gender = make_gender_tags(NEUTRAL_TAGS, character_name)

		male = female = neutral = False

		if any(tag in fic_tags for tag in f_gender): female = True
		elif any(tag in fic_tags for tag in m_gender): male = True
		elif any(tag in fic_tags for tag in n_gender): neutral = True

		if female and male: character['Gender'] = 'NEUTRAL'
		elif female: character['Gender'] = 'FEMALE'
		elif male: character['Gender'] = 'MALE'
		elif neutral: character['Gender'] = 'NEUTRAL'
		else: #if there are no gender tags applicable to the character, we'll defer to CoreNLP's opinion on this character's gender

			if character['Gender'] == 'UNKNOWN' or character['Gender']== '':
				#print(character['Name'], character['Gender']) #debug

				#if CoreNLP doesn't know this character's gender, and it is canon, we assume the canon gender. If it isn't canon it'll be left unknown
				if character['canonID'] > -1:
					canon_gender = canon_db.iloc[character['canonID']]['Gender']
					character['Gender'] = canon_gender

	return characters

def merge_sentences(fic_index, fic_dataset, character_sentences):
	sen_ids = []
	merged_sentences = []

	for sentence in character_sentences:
		sent = {}
		if sentence['senID'] in sen_ids: #If a dict for this sentence already exists
			sent = list(filter(lambda s: s['senID'] == sentence['senID'], merged_sentences))
			#print(len(sent)) #debug
			sent = sent[0]

			if sentence['nerIDs'] > -1 and sentence['nerIDs'] not in sent['nerIDs']: sent['nerIDs'].append(sentence['nerIDs'])
			if sentence['Clusters'] > -1 and sentence['Clusters'] not in sent['Clusters']: sent['Clusters'].append(sentence['Clusters'])

		else: #Create new sentence dict
			sen_ids.append(sentence['senID'])

			sent['ficID'] = fic_index
			sent['ficDataset'] = fic_dataset
			sent['senID'] = sentence['senID']
			sent['Sentiment'] = sentence['Sentiment']
			sent['Verbs'] = sentence['Verbs']

			if sentence['nerIDs'] > -1: sent['nerIDs'] =  [sentence['nerIDs']]
			else: sent['nerIDs'] = []

			if sentence['Clusters'] > -1: sent['Clusters'] = [sentence['Clusters']]
			else: sent['Clusters'] = []

			merged_sentences.append(sent)

	return merged_sentences

def merge_character_mentions(fic_index, character_entities, character_mentions, tagger_characters):
	# create characters from their NER IDs
	ner_ids = [char['nerID'] for char in character_entities]
	ner_ids = set(ner_ids) #remove duplicates

	characters = []
	for ner in ner_ids:
		character = {}
		character['ficID'] = fic_index
		character['nerID'] = [ner]
		character['Name'] = 'Jane Doe' #filler
		character['Gender'] = 'X' #filler
		character['Mentions'] = 0
		character['clusterID'] = [-1] #filler
		character['canonID'] = -1 #to be used later
		characters.append(character)

	# fill in character information using its clusters and mentions
	for char in characters:
		for mention in character_mentions:
			if mention['nerID'] == char['nerID'][0]:
				no_cluster = False
				char['Mentions'] = char['Mentions']+1

				if mention['MentionT'] == 'PROPER':
					char['Name'] = mention['Name']
					char['Gender'] = mention['Gender']

					cluster = char['clusterID']
					if  mention['clusterID'] not in cluster: char['clusterID'].append(mention['clusterID'])

	for char in characters:
		if len(char['clusterID']) == 1:
			ner_char = list(filter(lambda entity: entity['nerID'] == char['nerID'][0], character_entities))

			char['Name'] = ner_char[0]['Name']
			char['Gender'] = ner_char[0]['Gender']
			char['Mentions'] = len(ner_char)  		

	for char in characters: char['clusterID'].remove(-1) #remove filler
	
	# merge repeated character entries into single entry
	aux = characters.copy()
	for char in characters:
		aux.remove(char)
		for c in aux:
			cluster = c['clusterID']
			if len(cluster) == 1 and cluster[0] in char['clusterID']:
				if char['Name'].lower() == c['Name'].lower() and char['Gender'] == c['Gender']:
					char['Mentions'] = char['Mentions']+c['Mentions']
					char['nerID'].append(c['nerID'][0])

					aux.remove(c)
					characters.remove(c)

	# merge in the NERTagger characters
	for tagger_char, mentions in tagger_characters.items():
		for char in characters:
			if tagger_char.lower() == char['Name'].lower(): #add characters mentions if the character is already named
				if mentions > char['Mentions']:
					char['Mentions'] += mentions-char['Mentions']
				break


	return characters

def link_characters_to_canon(characters, canon_db):

	for character in characters:
		for index, canon_character in canon_db.iterrows():
			if type(canon_character['Other names']) == str:
				other_names = [name.lower() for name in canon_character['Other names'].split(',')]
				#print(other_names) #debug

			else: other_names = ['']

			if canon_character['Name'].lower() == character['Name'].lower():
				#print(canon_character['Name'].lower(), character['Name'].lower()) #debug
				character['canonID'] = index
				break

			elif character['Name'].lower() in [name.lower() for name in canon_character['Name'].split(' ')]:
				character['canonID'] = index
				break

			else:
				if character['Name'].lower() in other_names:
					character['canonID'] = index
					break
				else:
					for name in other_names:
						if ' ' in name:
							name = name.split(' ')
							if character['Name'].lower() in name:
								character['canonID'] = index
								break

	#if a character is not canon its canonID will not be changed from -1

	return characters

def canonize_characters(characters, canon_db):
	characters = link_characters_to_canon(characters, canon_db)
	characters = decide_gender(characters, canon_db)

	canon_ids = len(canon_db['Name'])
	#print(canon_ids) #debug

	canonized_characters = []
	for i in range(canon_ids):
		canon_name = canon_db.iloc[i]['Name']
		#print(canon_name) #debug
		characters_in_canon = list(filter(lambda char: char['canonID'] == i, characters))

		if len(characters_in_canon) > 0:
			canonized_character = {'Name':canon_name, 'Other names':[], 'Gender':[], 'Mentions':0, 'Canon ID':i}
			for char in characters_in_canon:
				if char['Name'].lower() == 'Fell': print(char)
				if char['Name'].lower() != canon_name.lower():
					canonized_character['Other names'].append(char['Name'])

				if char['Gender'] not in canonized_character['Gender']:
					canonized_character['Gender'].append(char['Gender'])

				canonized_character['Mentions'] += char['Mentions']

			canonized_characters.append(canonized_character)

	characters_not_in_canon = list(filter(lambda char: char['canonID'] == -1, characters))
	noncanon_characters = []
	for char in characters_not_in_canon:
		noncanon_characters.append({'Name':char['Name'], 'Other names':[], 'Gender':char['Gender'], 'Mentions':char['Mentions'], 'Canon ID':-1})

	return canonized_characters+noncanon_characters

def extract_data_from_annotations(annotation):
	sentences= annotation.sentence
	all_ner_mentions = annotation.mentions #NERMention[]
	all_coref_mentions = annotation.mentionsForCoref #Mention[]
	chains = annotation.corefChain #CorefChain[], made up of CorefMention[]
	
	# lists to store the return values in
	character_entities = []
	character_mentions = []
	character_sentences = []

	## Extract characters from NER and coreference mentions ##
	if len(all_ner_mentions) > 0:
		for ner in all_ner_mentions:
			if ner.ner == 'PERSON':
				sentence = {}
				sen = sentences[ner.sentenceIndex]
						
				string_sen = ''
				for token in sen.token: 
					string_sen += ' '+token.originalText

				sentence['senID'] = sen.sentenceIndex
				sentence['Sentiment'] = sen.sentiment
				#sentence['Verbs'] = get_lemmatized_verbs(string_sen)
				sentence['Verbs'] = string_sen
				sentence['nerIDs'] =  ner.canonicalEntityMentionIndex
				sentence['Clusters'] = -1 #filler
				character_sentences.append(sentence)

				character = {}
				#token = tokens[ner.tokenStartInSentenceInclusive]
				#coref_in_token = token.

				character['senID'] = sen.sentenceIndex
				character['nerID'] = ner.canonicalEntityMentionIndex
				character['nerMentionIndex'] = ner.entityMentionIndex
				character['Name'] = ner.entityMentionText
				character['Gender'] = ner.gender
				character['MentionT'] = 'PERSON'
				character_entities.append(character)

		#end FOR ner
	#end IF len
	if len(all_coref_mentions) > 0:
		for mention in all_coref_mentions:
			if mention.mentionType in ['PROPER','PRONOMINAL']:
				sentence = {}
				sen = sentences[mention.sentNum]
						
				string_sen = ''
				for token in sen.token: 
					string_sen += ' '+token.originalText

				sentence['senID'] = sen.sentenceIndex
				sentence['Sentiment'] = sen.sentiment
				#sentence['Verbs'] = get_lemmatized_verbs(string_sen)
				sentence['Verbs'] = string_sen
				sentence['nerIDs'] = -1 #filler
				sentence['Clusters'] = mention.corefClusterID

				character_sentences.append(sentence)
					
				if mention.sentNum != sen.sentenceIndex: print('false')

				character = {}

				token = sen.token[mention.headIndex]
				ner_in_token = all_ner_mentions[token.entityMentionIndex]
				character['senID'] = sen.sentenceIndex
				character['nerID'] = ner_in_token.canonicalEntityMentionIndex
				character['clusterID'] = mention.corefClusterID
				character['Name'] = mention.headString
				character['Gender'] = mention.gender
				character['MentionT'] = mention.mentionType
				character_mentions.append(character)


		#end FOR mention
	#end IF len		

	return character_entities, character_mentions, character_sentences

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
class CoreNLPDataProcessor():
	def __init__ (self, fic): #fic must be annotated with CoreNLP data
		try: 
			if fic.annotations is None: raise ValueError
			else: self.fic = fic

		except ValueError: print('This fanfic does not contain CoreNLP annotations')

	def extract_fic_characters(self, nerTagger_characters):
		#Get canon_db
		canon_db = pandas.read_csv(CANON_DB)

		# Declarations
		character_entities = []
		character_mentions = []
		character_sentences = []
		canonized_characters = [] #final result is stored here


		for annotation in self.fic.annotations:
			entities, mentions, sentences = extract_data_from_annotations(annotation)

			character_entities = character_entities + entities
			character_mentions = character_mentions + mentions
			character_sentences = character_sentences + sentences

		# Merge all character mentions into unique characters
		unique_characters = merge_character_mentions(self.fic.index, character_entities, character_mentions, nerTagger_characters)

		# Link characters to their canon version, if it has one
		canonized_characters = canonize_characters(unique_characters, canon_db)
		#print(canonized_characters[:10]) #debug

		# Decide genders for all characters
		#canonized_characters = decide_gender(canonized_characters, canon_db)

		self.fic.set_characters(canonized_characters)

	def extract_fic_sentiment(self):
		fic_sentences = []

		for annotation in self.fic.annotations: fic_sentences.extend(annotation.sentence)

		fic_sentiment = normalize_sentiment(fic_sentences)

		return fic_sentiment

class CoreWrapper(): #This client is like CoreClient2 from corenlp_wrapper

	def parse(self, fics):
		fics = process_fics(fics)
		if type(fics) == Fanfic: fics = [fics]

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


		
			
