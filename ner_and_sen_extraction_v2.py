#!/bin/bash/python3

import sys, time, pandas, numpy
#from sklearn.feature_extraction import DictVectorizer
#from sklearn.feature_extraction.text import TfidfTransformer
from corenlp_wrapper import CoreClient2
from stanza.server import Document
from nltk.tag import pos_tag
from nltk.tokenize import sent_tokenize, word_tokenize

from NER_tagger_v3 import NERTagger
from fanfic_util import FanficGetter, FanficHTMLHandler, Fanfic

### VARIABLES ###
CHARACTERS_TO_CSV = '/home/maria/Documents/Fanfic_ontology/fic_characters.csv'
SENTENCES_TO_CSV = '/home/maria/Documents/Fanfic_ontology/fic_sentences.csv'
CANON_DB = '/home/maria/Documents/Fanfic_ontology/canon_characters.csv'

ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_shortened.txt'
FRIENDSHIP_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_shortened.txt'
ENEMY_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths3.txt'

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

def extract_data_from_annotations(annotation):
	sentences= annotation.sentence
	all_ner_mentions = annotation.mentions #NERMention[]
	all_coref_mentions = annotation.mentionsForCoref #Mention[]
	chains = annotation.corefChain #CorefChain[], made up of CorefMention[]
	

	coref_chains = []
	for i in range(0, len(chains)): #debug
		coref_chains.append(chains[i].mention)
	coref_chains = get_longest_lists(coref_chains)

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
			if mention.mentionType == 'NOMINAL':
				print_coref_mention(mention, sentences[mention.sentNum])

			elif mention.mentionType in ['PROPER','PRONOMINAL']:
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

def character_and_sentence_extraction(fics):
	# Declarations
	client = CoreClient2()
	NERtagger = NERTagger()
	#chains = []

	print('\n###### Starting CoreNLP server and processing fanfics. . .######\n')
	start= time.time()

	annotated_fics = client.parse(fics)

	end = time.time()
	print("Client closed. "+ str((end-start)/60) +" mins elapsed")

	print("Processing annotation data...")
	start = time.time()



	num_fics = len(annotated_fics)-1
	for i, fic in enumerate(annotated_fics):
		# Declarations
		character_entities = []
		character_mentions = []
		character_sentences = []

		# First we process the character entities with NERTagger
		print('Processing fic '+ str(i)+' of '+str(num_fics)+' (Fic #'+str(fic.index)+')')

		# Preprocess and tag characters with NERTagger
		processed_fic = preprocess_fic(fic)
		tagger_characters = NERtagger.parse(processed_fic)
		#print(tagger_characters) #debug

		canonized_characters = []
		for annotation in fic.annotations:
			entities, mentions, sentences = extract_data_from_annotations(annotation)

			character_entities.extend(entities)
			character_mentions.extend(mentions)
			character_sentences.extend(sentences)

		# Merge all character mentions into unique characters
		unique_characters = merge_character_mentions(fic.index, character_entities, character_mentions, tagger_characters)

		# Link characters to their canon version, if it has one
		canonized_characters = link_characters_to_canon(unique_characters, canon_db)
		#print(canonized_characters[:10])
		#print(canonized_characters) #debug

		# Decide genders for all characters
		canonized_characters = decide_gender(canonized_characters, canon_db)

		# Merge all sentences into unique sentences with the characters they mention
		merged_sentences = merge_sentences(fic.index,fic.dataset,character_sentences)

		fic.characters = canonized_characters
		fic.sentences = merged_sentences


	end = time.time()
	print(". . .annotation data processed. "+ str((end-start)/60) +" mins elapsed")


	return fics

def preprocess_fic(fic):
	tagged_fic = []

	for chapter in fic.chapters:
		tokenized_chapter = [word_tokenize(sent) for sent in sent_tokenize(chapter)]
		tagged_chapter = [pos_tag(word) for word in tokenized_chapter]

		tagged_fic.extend(tagged_chapter)

	return tagged_fic

def get_fanfics(start, end):
	fGetter = FanficGetter()

	fGetter.set_fic_listing_path(ROMANCE_LISTING_PATH)
	r_fics = fGetter.get_fanfics_in_range(start, end) #get ROMANCE fanfics

	fGetter.set_fic_listing_path(FRIENDSHIP_LISTING_PATH)
	f_fics = fGetter.get_fanfics_in_range(start, end) #get FRIENDSHIP fanfics

	fGetter.set_fic_listing_path(ENEMY_LISTING_PATH)
	e_fics = fGetter.get_fanfics_in_range(start, end) #get ENEMY fanfics

	return r_fics + f_fics + e_fics

def count_fics_already_processed():
	processed_sentences = pandas.DataFrame.read_csv(SENTENCES_TO_CSV)

	return set(processed_sentences['ficID'])

### MAIN ###
# Loading canon DB...
canon_db = pandas.read_csv(CANON_DB)

if len(sys.argv) == 3:
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])

	print('Fetching fic texts...')
	start = time.time()

	fic_list = get_fanfics(start_index, end_index)
	#fic_texts = [fic.chapters for fic in fic_list] #debug
	#print(len(fic_texts[0]), type(fic_texts[0][0])) #debug

	end = time.time()
	print("...fics fetched. Elapsed time: ",(end-start)/60," mins")

	processed_fics = character_and_sentence_extraction(fic_list)
	
	all_characters = []
	all_sentences = []
	for fic in processed_fics: 
		all_characters.extend(fic.characters)
		all_sentences.extend(fic.sentences)

	print('Saving data to csv file...')
	start = time.time()

	# Create dataframe from dicts and save to csv
	c_df = pandas.DataFrame.from_dict(all_characters)
	s_df = pandas.DataFrame.from_dicst(all_sentences)

	c_df.to_csv(CHARACTERS_TO_CSV, mode='a', index=False, header=True)
	s_df.to_csv(SENTENCES_TO_CSV, mode = 'a', index=False, header=True)

	end = time.time()
	print("...saved. Elapsed time: ",(end-start)/60," mins")

elif len(sys.argv) == 1:
	fGetter = FanficGetter()
	fGetter.set_fic_listing_path(ROMANCE_LISTING_PATH)

	print('Fetching fic texts...')
	start = time.time()

	fic_list = fGetter.get_fanfics_in_range(0, 5)
	#fic_texts = [fic.chapters for fic in fic_list]
	#print(len(fic_texts[0]), type(fic_texts[0][0])) #debug

	end = time.time()
	print("...fics fetched. Elapsed time: ",(end-start)/60," mins")

	processed_fics = character_and_sentence_extraction(fic_list)
	
	all_characters = []
	all_sentences = []
	for fic in processed_fics: 
		all_characters.extend(fic.characters)
		all_sentences.extend(fic.sentences)
	
	#print(len(all_characters), len(all_sentences)) #debug
	#print(type(all_characters), type(all_sentences)) #debug

	#print(all_characters[:5]) #debug
	#print(all_sentences[:5]) #debug

	# Create dataframe from dicts and save to csv
	c_df = pandas.DataFrame.from_dict(all_characters)
	s_df = pandas.DataFrame.from_dict(all_sentences)

	#c_df.to_csv(CHARACTERS_TO_CSV, mode='a', index=False, header=True)
	#s_df.to_csv(SENTENCES_TO_CSV, mode = 'a', index=False, header=True)




