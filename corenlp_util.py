#!/usr/bin/bash/python3

import time, pandas, nltk, re, random
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
NEUTRAL_TAGS = ['They/Them Pronouns for ', 'Gender-Neutral Pronouns for ', 'Gender-Neutral ', 'Agender ', 'Genderfluid ', 'Androgynous ', 'Gender Non-Conforming ']

PRONOUNS = ['he','him','his','she','her','hers','I','me','mine','you','your','yours','we','our','ours','they','them','theirs','it','its']


MAX_CHAPTER_LENGTH = 30000

### FUNCTIONS ###
def normalize_sentiment(sentences):
	sentiment_info = {'Num sentences':0, 'Very positive':0, 'Positive':0, 'Neutral':0, 'Negative':0, 'Very negative':0}
	sentiment_info['Num sentences'] = len(sentences)
	
	sentiment_count = 0
	for sentence in sentences:
		sentiment = sentence.sentiment
		#print(sentiment) #debug
		sentiment_info[sentiment] += 1

		
		if sentiment == 'Very positive': sentiment_count += 2
		elif sentiment == 'Positive': sentiment_count += 1
		elif sentiment == 'Negative': sentiment_count -= 1
		elif sentiment == 'Very negative': sentiment_count -= 2
		

	sentiment_info['Weighted average'] = sentiment_count/len(sentences)

	return sentiment_info

def make_gender_tags(tags, character_name):
	for tag in tags:
		tag = tag+character_name
		#print(tag) #debug

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
		if any(tag in fic_tags for tag in m_gender): male = True
		if any(tag in fic_tags for tag in n_gender): neutral = True

		if female and male: character['Gender'] = 'NEUTRAL'
		elif female: character['Gender'] = 'FEMALE'
		elif male: character['Gender'] = 'MALE'
		elif neutral: character['Gender'] = 'NEUTRAL'
		else: #if there are no gender tags applicable to the character, we'll defer to CoreNLP's opinion on this character's gender

			if character['Gender'] == 'UNKNOWN' or character['Gender']== '':#if CoreNLP doesn't know this character's gender, and it is canon, we assume the canon gender. If it isn't canon it'll be left unknown
				#print(character['Name'], character['Gender']) #debug

				if character['canonID'] > -1:
					canon_gender = canon_db.iloc[character['canonID']]['Gender']
					character['Gender'] = canon_gender

				elif character['Gender'] == '' or character['Gender'] == 'X': character['Gender'] = 'UNKNOWN' 

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

def get_name_count(ner_chars):
	names = {}
	other_names = []

	for char in ner_chars:
		try: 
			if char['Name'].lower() not in PRONOUNS:
				names[char['Name']] += 1
		except KeyError: names[char['Name']] = 1

	return names

def get_edit_distance(name1, name2):
	if ' ' in name1:
		name_and_surname1 = [n.strip().lower() for n in name1.split(' ')]

		distance = []
		if ' ' in name2:
			name_and_surname2 = [n.strip().lower() for n in name2.split(' ')]

			for n1 in name_and_surname1:
				for n2 in name_and_surname2: distance.append(nltk.edit_distance(n1, n2))

		else:
			for n in name_and_surname1: distance.append(nltk.edit_distance(n, name2.lower()))

		return min(distance)

	elif ' ' in name2:
		name_and_surname2 = [n.strip().lower() for n in name2.split(' ')]

		distance = []
		for n in name_and_surname2: distance.append(nltk.edit_distance(name1.lower(), n))

		return min(distance)

	else: return nltk.edit_distance(name1.lower(), name2.lower())

def get_max_edit_distance(name):
	if ' ' in name:
		subnames = [n.strip() for n in name.split(' ')]

		lengths = [len(name) for name in subnames]

		min_length = min(lengths)

	else: min_length = len(name)

	if min_length > 4: return 3
	elif min_length == 4: return 2
	else: return 1
 
def merge_character_mentions(fic_index, character_entities, coref_mentions):
	# create characters from their NER IDs
	ner_ids = [char['nerID'] for char in character_entities]
	ner_ids = set(ner_ids) #remove duplicates

	characters = []
	## Rule 1 of character merging: Mentions with the same nerID refer to the same character
	for ner in ner_ids:
		ner_chars = list(filter(lambda entity: entity['nerID'] == ner, character_entities)) #characters with this ner ID
		#Select gender according to CoreNLP NER extractor
		gender = []
		for char in ner_chars: gender.append(char['Gender'])
		gender = list(set(gender)) #remove duplicates
		if '' in gender: gender.remove('')

		if len(gender) == 0: gender = 'X'
		elif len(gender) == 1: gender = gender[0]
		else:
			#print(gender) #debug
			gender = 'X'

		#Clean and select character's name
		names = [char['Name'].replace('\n',' ').strip() for char in ner_chars]
		names = [re.sub(r'[^A-Za-z0-9 	]+', '', name).strip() for name in names if name.lower() not in PRONOUNS] #strip non-alphanumeric characters, except for spaces
		names = list(set(names)) #remove duplicates
		#print(names) #debug

		for name in names:
			new_character = {'ficID':fic_index,'nerID':[ner],'Name':name,'Other names':[],'Gender':gender,'clusterID':[-1],'canonID':-1,'Mentions':0}
			#print(new_character) #debug
			characters.append(new_character)

	
	for char in characters:
		for mention in coref_mentions:
			if mention['nerID'] == char['nerID'][0]:

				if mention['MentionT'] == 'PROPER':
					#if mention['nerID'] == 0: print(mention) #debug
					## Rule 2 of character merging: Mentions which overlap with a NERMention refer to its same character
					distance = get_edit_distance(char['Name'], mention['Name'])
					max_edit_distance = min(get_max_edit_distance(char['Name']),get_max_edit_distance(mention['Name']))

					if distance < max_edit_distance:
						if char['Gender'] == 'X': #gender is added
							char['Gender'] = mention['Gender']

						elif char['Gender'] != mention['Gender']: 
							#print('diff gender: ',mention) #debug
							diff_gender_chars = list(filter(lambda entity: nltk.edit_distance(char['Name'],entity['Name']) < max_edit_distance and entity['Gender'] == mention['Gender'], characters))
							if len(diff_gender_chars) > 0:
								#print('len diff gender:',len(diff_gender_chars))#debug
								char = diff_gender_chars[0]

							else:	#Add new entry for the character with different gender
								diff_gender_char = char.copy()
								diff_gender_char['Gender'] = mention['Gender']
								diff_gender_char['Mentions'] = 0
								characters.append(diff_gender_char)

								char = diff_gender_char

						char['Mentions'] +=1

						if distance > 0: #different names are added
							other_names = [name.lower() for name in char['Other names']]
							if mention['Name'].lower() not in other_names:
								char['Other names'].append(mention['Name'])


						cluster = char['clusterID'] #cluster is added
						if  mention['clusterID'] not in cluster: char['clusterID'].append(mention['clusterID'])
	
	
	for char in characters:
		if -1 in char['clusterID']: char['clusterID'].remove(-1) #remove filler

	"""
	aux = characters.copy()
	for char in characters:
		aux.remove(char)

		for c in aux:
			name = c['Name']
			gender = c['Gender']

			distance = get_edit_distance(char['Name'],name)
			max_edit_distance = min(get_max_edit_distance(char['Name']),get_max_edit_distance(name))

			if gender == char['Gender']:
				if distance == 0:
					char['Mentions'] += c['Mentions']
					aux.remove(c)
					characters.remove(c)

				elif distance < max_edit_distance:
					char['Mentions'] += c['Mentions']
					other_names = [n.lower() for n in char['Other names']]

					if name.lower() not in other_names: char['Other names'].append(name)
					aux.remove(c)
					characters.remove(c)

	
	"""
	## Rule 3 of character merging: All the mentions of a coreference cluster refer to the same character, but only if the gender is consistent and the names have an edit distance lesser than MAX_EDIT_DISTANCE
	aux = characters.copy()
	for char in characters:
		aux.remove(char)

		for c in aux:
			cluster = c['clusterID']
			
			if any(cluster) in char['clusterID']:
				if char['Gender'] == c['Gender']:
					distance = get_edit_distance(char['Name'],c['Name'])
					max_edit_distance = min(get_max_edit_distance(char['Name']),get_max_edit_distance(c['Name']))

					if distance == 0:
						char['Mentions'] = char['Mentions']+c['Mentions']

						aux.remove(c)
						characters.remove(c)

					elif distance < max_edit_distance:
						char['Mentions'] = char['Mentions']+c['Mentions']
						char['nerID'].append(c['nerID'][0])

						other_names = [n.lower() for n in char['Other names']]
						if c['Name'] not in other_names: char['Other names'].append(c['Name'])

						aux.remove(c)
						characters.remove(c)
		

	
	#print(characters) #debug
	return characters

def link_characters_to_canon(characters, canon_db):
	for character in characters:
		better_fit = (-1, 300) #first member of the tuple is ID, the other is edit distance, instantiated to an absolutely ridiculous high one so it can be replaced for the smallest one

		for index, canon_character in canon_db.iterrows():
			if type(canon_character['Other names']) == str:
				other_canon_names = [name.strip().lower() for name in canon_character['Other names'].split(',')]
				#print(other_canon_names) #debug


			else: other_canon_names = ['']

			distance = get_edit_distance(canon_character['Name'], character['Name'])
			max_edit_distance = min(get_max_edit_distance(canon_character['Name']),get_max_edit_distance(character['Name']))

			if  distance == 0:
				character['canonID'] = index
				break

			elif distance < max_edit_distance:
				#print(canon_character['Name'].lower(), character['Name'].lower()) #debug
				if distance < better_fit[1]: better_fit = (index, distance)

			elif character['Name'].lower() in other_canon_names:
					character['canonID'] = index
					break
			else:
				for name in character['Other names']:
					distances = [get_edit_distance(name, canon_name) for canon_name in other_canon_names]
					max_distances = [get_max_edit_distance(canon_name) for canon_name in other_canon_names]
					max_edit_distance = min(max_distances)
					if any(distances) == 0:
						character['canonID'] = index
						break

					elif any(distances) < max_edit_distance:
						if distance < better_fit[1]: better_fit = (index, distance)


		# end for canon_characters			
		if character['canonID'] < 0 and better_fit[0] >= 0:
			character['canonID'] = better_fit[0]

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
			canonized_character = {'Name':canon_name, 'Other names':'', 'Male mentions':0, 'Female mentions':0, 'Neutral mentions':0, 'Unknown mentions':0, 'Canon ID':i}
			
			canonized_character['Name'] = canon_name

			other_names = []
			for char in characters_in_canon:
				if char['Name'].lower() != canon_name.lower(): other_names.append(char['Name'])
				other_names.extend(char['Other names'])

				if char['Gender'] == 'MALE':
					canonized_character['Male mentions'] += char['Mentions']

				elif char['Gender'] == 'FEMALE':
					canonized_character['Female mentions'] += char['Mentions']

				elif char['Gender'] == 'NEUTRAL':
					canonized_character['Neutral mentions'] += char['Mentions']
				else:
					canonized_character['Unknown mentions'] += char['Mentions']

			other_names = list(set(other_names))
			canonized_character['Other names'] = ', '.join(other_names)

			canonized_characters.append(canonized_character)

	characters_not_in_canon = list(filter(lambda char: char['canonID'] == -1, characters))
	noncanon_characters = []
	for char in characters_not_in_canon:
		noncanon_char = {'Name':char['Name'], 'Other names':'', 'Male mentions':0, 'Female mentions':0, 'Neutral mentions':0, 'Unknown mentions':0,'Canon ID':'NO'}

		if char['Gender'] == 'MALE':
			noncanon_char['Male mentions'] += char['Mentions']

		elif char['Gender'] == 'FEMALE':
			noncanon_char['Female mentions'] += char['Mentions']

		else:
			noncanon_char['Unknown mentions'] += char['Mentions']
		
		noncanon_characters.append(noncanon_char)

	#print(type(canonized_characters)) #debug

	return canonized_characters+noncanon_characters

def extract_data_from_annotations(annotation):
	sentences= annotation.sentence
	all_ner_mentions = annotation.mentions #NERMention[]
	all_coref_mentions = annotation.mentionsForCoref #Mention[]
	chains = annotation.corefChain #CorefChain[], made up of CorefMention[]
	
	# lists to store the return values in
	character_entities = []
	coref_mentions = []
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
					
				#if mention.sentNum != sen.sentenceIndex: print('false')

				character = {}

				token = sen.token[mention.headIndex]
				ner_in_token = all_ner_mentions[token.entityMentionIndex]
				character['senID'] = sen.sentenceIndex
				character['nerID'] = ner_in_token.canonicalEntityMentionIndex
				character['clusterID'] = mention.corefClusterID
				character['Name'] = mention.headString
				character['Gender'] = mention.gender
				character['MentionT'] = mention.mentionType
				coref_mentions.append(character)


		#end FOR mention
	#end IF len		

	return character_entities, coref_mentions, character_sentences

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
						#print('BIG BOY CHAPTER') #debug
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

	def extract_fic_characters(self):
		#Get canon_db
		canon_db = pandas.read_csv(CANON_DB)

		# Declarations
		character_entities = []
		coref_mentions = []
		character_sentences = []
		canonized_characters = [] #final result is stored here


		for annotation in self.fic.annotations:
			entities, mentions, sentences = extract_data_from_annotations(annotation)

			character_entities = character_entities + entities
			coref_mentions = coref_mentions + mentions
			character_sentences = character_sentences + sentences

		# Merge all character mentions into unique characters
		unique_characters = merge_character_mentions(self.fic.index, character_entities, coref_mentions)

		# Link characters to their canon version, if it has one
		canonized_characters = canonize_characters(unique_characters, canon_db)
		#print(canonized_characters[:10]) #debug

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


		
			
