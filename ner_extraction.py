#!/bin/bash/python3

import sys, time, pickle, pandas, numpy
from sklearn.cluster import KMeans
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from corenlp_wrapper import CoreClient
from stanza.server import Document

from NER_tagger_v3 import NERTagger
from fanfic_util import FanficGetter, Fanfic

### VARIABLES ###
TO_CSV = '/home/maria/Documents/Fanfic_ontology/fic_characters.csv'
CANON_DB = '/home/maria/Documents/Fanfic_ontology/canon_characters.csv'
ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths2.txt'

VERB_TAGS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
FEMALE_TAGS = ['She/Her Pronouns for ', 'Female ', 'Female!', 'Female-Presenting ']
MALE_TAGS = ['He/Him Pronouns for ', 'Male ', 'Male!', 'Male-Presenting ']
NEUTRAL_TAGS = ['They/Them Pronouns for ', 'Gender-Neutral Pronouns for', 'Gender-Neutral ', 'Agender ', 'Genderfluid ', 'Androgynous ', 'Gender Non-Conforming ']

### FUNCTIONS ###

def merge_character_mentions(character_entities, character_mentions):
	# create characters from their NER IDs
	ner_ids = [char['nerID'] for char in character_entities]
	ner_ids = set(ner_ids) #remove duplicates

	characters = []
	for ner in ner_ids:
		character = {}
		character['Fic ID'] = fic.index
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
				if char['Name'] == c['Name'] and char['Gender'] == c['Gender']:
					char['Mentions'] = char['Mentions']+c['Mentions']
					char['nerID'].append(c['nerID'][0])

					aux.remove(c)
					characters.remove(c)

	#end FOR char

	return characters

def link_characters_to_canon(characters):
	canon_db = pandas.read_csv(CANON_DB)

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

			elif character['Name'].lower() in other_names:
				character['canonID'] = index
				break

	#if a character is not canon its canonID will not be changed from -1

	return characters

	

def get_longest_lists(coref_chains): #returns the two longest chains in the coreference graph
	longest = []
	longest.append(max(list(coref_chains), key=len))

	coref_chains.remove(longest[0])

	longest.append(max(list(coref_chains), key=len))

	return longest

def print_coref_mention(mention, sent):
	token = sent.token[mention.headIndex]
	coref_cluster = token.corefClusterID
	#print(mention.mentionID, coref_cluster, mention.mentionType, token.originalText, mention.gender, mention.animacy, mention.number)

def print_ner_mention(mention):	
	print(mention.entityMentionIndex, mention.canonicalEntityMentionIndex, mention.ner, mention.gender, mention.entityMentionText)

def extract_ners_from_fic(fic):
	# Declarations for later
	#sentences = []
	chains = []

	character_mentions = []
	character_entities = []
	mention_sentences = []

	# Starting client to CoreNLP
	anns = client.parse(fic.chapters)


	fic_sentences = []
	#print("Processing annotation data...")
	#start = time.time()
	
	for ann in anns:
		sentences= ann.sentence
		all_ner_mentions = ann.mentions #NERMention[]
		all_coref_mentions = ann.mentionsForCoref #Mention[]
		chains = ann.corefChain #CorefChain[], made up of CorefMention[]
		

		coref_chains = []
		for i in range(0, len(chains)): #debug
			coref_chains.append(chains[i].mention)
		coref_chains = get_longest_lists(coref_chains)


		## Extract characters from NER and coreference mentions ##
		if len(all_ner_mentions) > 0:
			for ner in all_ner_mentions:
				if ner.ner == 'PERSON':
					character = {}

					#token = tokens[ner.tokenStartInSentenceInclusive]
					#coref_in_token = token.

					character['senID'] = ner.sentenceIndex
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
				if mention.mentionType == 'NOMINAL':
					print_coref_mention(mention, sentences[mention.sentNum])

				elif mention.mentionType in ['PROPER','PRONOMINAL']:
					character = {}

					token = sentences[mention.sentNum].token[mention.headIndex]
					ner_in_token = all_ner_mentions[token.entityMentionIndex]

					character['senID'] = mention.sentNum
					character['nerID'] = ner_in_token.canonicalEntityMentionIndex
					character['clusterID'] = mention.corefClusterID
					character['Name'] = mention.headString
					character['Gender'] = mention.gender
					character['MentionT'] = mention.mentionType

					character_mentions.append(character)


			#end FOR mention
		#end IF len

		## Extract sentences which mention protagonists ##
		for chain in coref_chains:
			for mention in chain:
				sen = sentences[mention.sentenceIndex]

				string_sen = ''
				for token in sen.token: string_sen += ' '+token.originalText
				#print(string_sen)

		

	#end FOR anns
	"""
	print('\n\n=========== Character mentions =============')
	for char in character_mention: print(char['senID'], char['nerID'], char['clusterID'], char['MentionT'], char['Name'], char['Gender'])

	print('\n\n=========== Character entities =============')

	for char in character_entities: print(char['senID'], char['nerID'], char['nerMentionIndex'], char['MentionT'], char['Name'], char['Gender'])
	"""

	return character_entities, character_mentions


### MAIN ###

# Initializing getters and taggers...
fGetter = FanficGetter()
NERtagger = NERTagger()
client = CoreClient()

fGetter.set_fic_listing_path(ROMANCE_LISTING_PATH)

if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])

	print('Fetching fic texts...')
	start = time.time()

	fic_list = fGetter.get_fanfics_in_range(start_index, end_index)
	#fic_texts = [fic.chapters for fic in fic_list]
	#print(len(fic_texts[0]), type(fic_texts[0][0])) #debug

	end = time.time()
	print("...fics fetched. Elapsed time: ",(end-start)/60," mins")

	all_characters = []
	for fic in fic_list:
		character_entities, character_mentions = extract_ners_from_fic(fic)
	
		# Merge all character mentions into unique characters
		unique_characters = merge_character_mentions(character_entities, character_mentions)

		# Link characters to their canon version, if it has one
		canonized_characters = link_characters_to_canon(unique_characters)

		#convert lists to str so pandas can digest them
		"""
		for char in canonized_characters:
			char['clusterID'] = str(char['clusterID']).strip('[]')
			char['nerID'] = str(char['nerID']).strip('[]')
		"""

		#print(canonized_characters[:10])
		#print('\n',len(unique_characters)) #debug
		#for char in unique_characters: print(char['nerID'], char['clusterID'], char['Name'], char['Gender'], char['Mentions']) #debug

		all_characters.extend(canonized_characters)

	# Create dataframe from dicts and save to csv
	df = pandas.DataFrame.from_dict(all_characters)

	df.to_csv(TO_CSV, mode='a', index=False, header=True)

elif len(sys.argv) == 1:
	print('Fetching fic texts...')
	start = time.time()

	fic_list = fGetter.get_fanfics_in_range(0, 5)
	#fic_texts = [fic.chapters for fic in fic_list]
	#print(len(fic_texts[0]), type(fic_texts[0][0])) #debug

	end = time.time()
	print("...fics fetched. Elapsed time: ",(end-start)/60," mins")

	print('\n###### Starting CoreNLP server and processing fanfics. . .######\n')
	start= time.time()

	all_characters = []
	for fic in fic_list:
		print('Processing fic #', fic.index)
		character_entities, character_mentions = extract_ners_from_fic(fic)
	
		# Merge all character mentions into unique characters
		unique_characters = merge_character_mentions(character_entities, character_mentions)

		# Link characters to their canon version, if it has one
		canonized_characters = link_characters_to_canon(unique_characters)
		#print(canonized_characters[:10])

		all_characters.extend(canonized_characters)
		
	end = time.time()
	print("Client closed. "+ str((end-start)/60) +" mins elapsed")
	
	# Create dataframe from dicts and save to csv
	df = pandas.DataFrame.from_dict(all_characters)

	df.to_csv(TO_CSV, mode='a', index=False, header=True)




