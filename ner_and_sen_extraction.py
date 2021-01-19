#!/bin/bash/python3

import sys, time, pandas, numpy
#from sklearn.feature_extraction import DictVectorizer
#from sklearn.feature_extraction.text import TfidfTransformer
from corenlp_wrapper import CoreClient
from stanza.server import Document
from nltk.tag import pos_tag
from nltk.tokenize import sent_tokenize, word_tokenize

from NER_tagger import NERTagger
from fanfic_util import FanficGetter, FanficHTMLHandler, Fanfic

### VARIABLES ###
TO_CSV = '/home/maria/Documents/Fanfic_ontology/fic_characters.csv'
CANON_DB = '/home/maria/Documents/Fanfic_ontology/canon_characters.csv'
ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths2.txt'

FEMALE_TAGS = ['She/Her Pronouns for ', 'Female ', 'Female!', 'Female-Presenting ']
MALE_TAGS = ['He/Him Pronouns for ', 'Male ', 'Male!', 'Male-Presenting ']
NEUTRAL_TAGS = ['They/Them Pronouns for ', 'Gender-Neutral Pronouns for', 'Gender-Neutral ', 'Agender ', 'Genderfluid ', 'Androgynous ', 'Gender Non-Conforming ']

### FUNCTIONS ###

def print_coref_mention(mention, sent):
	token = sent.token[mention.headIndex]
	coref_cluster = token.corefClusterID
	#print(mention.mentionID, coref_cluster, mention.mentionType, token.originalText, mention.gender, mention.animacy, mention.number)

def print_ner_mention(mention):	
	print(mention.entityMentionIndex, mention.canonicalEntityMentionIndex, mention.ner, mention.gender, mention.entityMentionText)

def merge_character_mentions(character_entities, character_mentions, tagger_characters):
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

			elif character['Name'].lower() in other_names:
				character['canonID'] = index
				break

	#if a character is not canon its canonID will not be changed from -1

	return characters

def make_gender_tags(tags, character_name):
	for tag in tags:
		tag = tag+character_name

	return tags

def decide_gender(characters, canon_db):
	handler = FanficHTMLHandler()

	for character in characters:
		if character['Gender'] == 'UNKNOWN':
			fic_link = '/home/maria/Documents/Fanfic_ontology/TFG_fics/html/gomensfanfic_'+str(character['Fic ID'])+'.html'
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
			else: #if there are no gender tags applicable to the character we assume the canon gender
				if character['canonID'] > -1: #if the character is not canon the gender will remain unknown
					canon_gender = canon_db.iloc[character['canonID']]['Gender']
					character['Gender'] = canon_gender

	return characters
			
 
def get_longest_lists(coref_chains): #returns the two longest chains in the coreference graph
	longest = []
	longest.append(max(list(coref_chains), key=len))

	coref_chains.remove(longest[0])

	longest.append(max(list(coref_chains), key=len))

	return longest

def merge_sentences(fic_sentences):

	sen_ids = []
	merged_sentences = []
	for sentence in fic_sentences:
		sent = {}
		if sentence['SenID'] in sen_ids: #If a dict for this sentence already exists
			sent = list(filter(lambda s: s['SenID'] == sentence['SenID'], merged_sentences))
			#print(len(sent)) #debug
			sent = sent[0]

			if sentence['nerIDs'] > -1 and sentence['nerIDs'] not in sent['nerIDs']: sent['nerIDs'].append(sentence['nerIDs'])
			if sentence['Clusters'] > -1 and sentence['Clusters'] not in sent['Clusters']: sent['Clusters'].append(sentence['Clusters'])

		else: #Create new sentence dict
			sen_ids.append(sentence['SenID'])

			sent['SenID'] = sentence['SenID']
			sent['Sentiment'] = sentence['Sentiment']
			sent['Verbs'] = sentence['Verbs']

			if sentence['nerIDs'] > -1: sent['nerIDs'] =  [sentence['nerIDs']]
			else: sent['nerIDs'] = []

			if sentence['Clusters'] > -1: sent['Clusters'] = [sentence['Clusters']]
			else: sent['Clusters'] = []

			merged_sentences.append(sent)

	return merged_sentences	

def extract_ners_with_corenlp(fic):
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
					sentence = {}
					sen = sentences[ner.sentenceIndex]
						
					string_sen = ''
					for token in sen.token: 
						string_sen += ' '+token.originalText

					sentence['SenID'] = sen.sentenceIndex
					sentence['Sentiment'] = sen.sentiment
					#sentence['Verbs'] = get_lemmatized_verbs(string_sen)
					sentence['Verbs'] = string_sen
					sentence['nerIDs'] =  ner.canonicalEntityMentionIndex
					sentence['Clusters'] = -1 #filler

					fic_sentences.append(sentence)

					character = {}

					#token = tokens[ner.tokenStartInSentenceInclusive]
					#coref_in_token = token.

					character['SenID'] = sen.sentenceIndex
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
					sentence = {}
					sen = sentences[mention.sentNum]
						
					string_sen = ''
					for token in sen.token: 
						string_sen += ' '+token.originalText

					sentence['SenID'] = sen.sentenceIndex
					sentence['Sentiment'] = sen.sentiment
					#sentence['Verbs'] = get_lemmatized_verbs(string_sen)
					sentence['Verbs'] = string_sen
					sentence['nerIDs'] = -1 #filler
					sentence['Clusters'] = mention.corefClusterID

					fic_sentences.append(sentence)
					
					if mention.sentNum != sen.sentenceIndex: print('false')

					character = {}

					token = sen.token[mention.headIndex]
					ner_in_token = all_ner_mentions[token.entityMentionIndex]

					character['SenID'] = sen.sentenceIndex
					character['nerID'] = ner_in_token.canonicalEntityMentionIndex
					character['clusterID'] = mention.corefClusterID
					character['Name'] = mention.headString
					character['Gender'] = mention.gender
					character['MentionT'] = mention.mentionType

					character_mentions.append(character)


			#end FOR mention
		#end IF len		
	#end FOR anns
	"""
	print('\n\n=========== Character mentions =============')
	for char in character_mention: print(char['SenID'], char['nerID'], char['clusterID'], char['MentionT'], char['Name'], char['Gender'])

	print('\n\n=========== Character entities =============')

	for char in character_entities: print(char['SenID'], char['nerID'], char['nerMentionIndex'], char['MentionT'], char['Name'], char['Gender'])
	"""

	return character_entities, character_mentions, fic_sentences

def preprocess_fic(fic):
	tokenized_fic = [word_tokenize(sen) for sen in sent_tokenize(fic.chapters[0])]
	tagged_fic = [pos_tag(word) for word in tokenized_fic]

	return tagged_fic


### MAIN ###

# Initializing getters and taggers...
fGetter = FanficGetter()
NERtagger = NERTagger()
client = CoreClient()

fGetter.set_fic_listing_path(ROMANCE_LISTING_PATH)

# Loading canon DB...
canon_db = pandas.read_csv(CANON_DB)

if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])

	print('Fetching fic texts...')
	start = time.time()

	fic_list = fGetter.get_fanfics_in_range(start_index, end_index)
	#fic_texts = [fic.chapters for fic in fic_list] #debug
	#print(len(fic_texts[0]), type(fic_texts[0][0])) #debug

	end = time.time()
	print("...fics fetched. Elapsed time: ",(end-start)/60," mins")

	print('\n###### Starting CoreNLP server and processing fanfics. . .######\n')
	start= time.time()

	all_characters = []
	for fic in fic_list:
		print('Processing fic #', fic.index)
		# Preprocess and tag characters with NERTagger
		processed_fic = preprocess_fic(fic)
		tagger_characters = NERtagger.parse(processed_fic)
		#print(tagger_characters) #debug

		# Extract characters with CoreNLP
		character_entities, character_mentions = extract_ners_with_corenlp(fic)
	
		# Merge all character mentions into unique characters
		unique_characters = merge_character_mentions(character_entities, character_mentions, tagger_characters)

		# Link characters to their canon version, if it has one
		canonized_characters = link_characters_to_canon(unique_characters, canon_db)
		#print(canonized_characters[:10])
		#print(canonized_characters) #debug

		# Decide genders for all characters
		canonized_characters = decide_gender(canonized_characters, canon_db)

		all_characters.extend(canonized_characters)
		
	end = time.time()
	print("Client closed. "+ str((end-start)/60) +" mins elapsed")

	# Create dataframe from dicts and save to csv
	df = pandas.DataFrame.from_dict(all_characters)

	#df.to_csv(TO_CSV, mode='a', index=False, header=True)

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
		# Preprocess and tag characters with NERTagger
		tagged_fic = preprocess_fic(fic)
		tagger_characters = NERtagger.parse(tagged_fic)
		#print(tagger_characters) #debug

		# Extract characters with CoreNLP
		character_entities, character_mentions, fic_sentences = extract_ners_with_corenlp(fic)
	
		# Merge all character mentions into unique characters
		unique_characters = merge_character_mentions(character_entities, character_mentions, tagger_characters)

		# Link characters to their canon version, if it has one
		canonized_characters = link_characters_to_canon(unique_characters, canon_db)
		#print(canonized_characters[:10]) #debug

		# Merge all sentences into unique sentences with the characters they mention
		merged_sentences = merge_sentences(fic_sentences)
		print(merged_sentences) #debug

		all_characters.extend(canonized_characters)
		
	end = time.time()
	print("Client closed. "+ str((end-start)/60) +" mins elapsed")
	
	# Create dataframe from dicts and save to csv
	df = pandas.DataFrame.from_dict(all_characters)

	#df.to_csv(TO_CSV, mode='a', index=False, header=True)




