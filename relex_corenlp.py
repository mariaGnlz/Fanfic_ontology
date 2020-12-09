#!/bin/bash/python3

import sys, time, pickle, pandas, numpy
from sklearn.cluster import KMeans
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from corenlp_wrapper import CoreClient
from stanza.server import Document

from NER_tagger_v3 import NERTagger
from fanfic_util import FanficGetter, Fanfic

import matplotlib.pyplot as plt

### VARIABLES ###
TO_CSV = '/home/maria/Documents/Fanfic_ontology/tagged_sents.csv'
ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths2.txt'

ANNOTATORS_PATH = '/home/maria/Documents/Fanfic_ontology/TFG_annotators/'
ANNOTATOR_NAME = 'annotator_0.pickle'

VERB_TAGS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']

### FUNCTIONS ###

def get_longest_lists(coref_chains): #returns the two longest chains in the coreference graph
	longest = []
	longest.append(max(list(coref_chains), key=len))

	coref_chains.remove(longest[0])

	longest.append(max(list(coref_chains), key=len))

	return longest

def print_coref_mention(mention, sentences):
	sent = sentences[mention.sentenceIndex]
	token = sent.token[mention.headIndex]
	coref_cluster = token.corefClusterID
	print(mention.mentionID, coref_cluster, mention.mentionType, token.originalText, mention.gender, mention.animacy, mention.number)

def print_ner_mention(mention):	
	print(mention.entityMentionIndex, mention.canonicalEntityMentionIndex, mention.ner, mention.gender, mention.entityMentionText)

### CLASSES ###

class FicSentence():
	def __init__(self, fic_index, sen_index, sentence, sentiment, character_mentions):
		self.fic_index = fic_index
		self.sen_index = sen_index
		self.sentence = sentence
		self.character_mentions = character_mentions
		self.sentiment = sentiment

	def getDictRepresentation(self):	
		return {
			'id': self.ID,
			'sentence': self.sentence,
			'sentiment': self.sentiment,
			'character_mentions': self.character_mentions,
			}


class CharacterMention():
	def __init__(self, ID, word, canonicalName, gender, animacy, number, corefClusterID, nerEntityID, corefMentions, nerMentions):
		self.ID = ID
		self.word = word
		self.canonicalName = canonicalName
		self.gender = gender
		self.animacy = animacy
		self.number = number

		self.corefClusterID = corefClusterID
		self.nerEntityID = nerEntityID
		self.corefMentions = corefMentions
		self.nerMentions = nerMentions


	def getDictRepresentation(self):
		return {
			'name': self.canonicalName,
			'gender': self.gender,
			'animacy': self.animacy,
			'number': self.number,

			'clusterID': self.corefClusterID,
			'nerID': self.nerEntityID,
			}

	def getID(self): return self.ID
	

### MAIN ###

# Initializing getters and taggers...
fGetter = FanficGetter()
NERtagger = NERTagger()
client = CoreClient()

fGetter.set_fic_listing_path(ROMANCE_LISTING_PATH)

print('Fetching fic texts...')
start = time.time()

fic_list = fGetter.get_fanfics_in_range(0,1)
#fic_texts = [fic.chapters for fic in fic_list]
#print(len(fic_texts[0]), type(fic_texts[0][0])) #debug

end = time.time()
print("...fics fetched. Elapsed time: ",(end-start)/60," mins")


print('\n###### Starting client and calling CoreNLP server ######\n')
start= time.time()

sentences = []
nerMentions = []
corefMentions = []
chains = []
for fic in fic_list:
	anns = client.parse(fic.chapters)


	end = time.time()
	print("Client closed. "+ str((end-start)/60) +" mins elapsed")
	
	fic_sentences = []
	print("Processing annotation data...")
	start = time.time()
	
	for ann in anns:
		sentences= ann.sentence
		nerMentions = ann.mentions #NERMention[]
		corefMentions = ann.mentionsForCoref #Mention[]
		chains = ann.corefChain #CorefChain[], made up of CorefMention[]
		

		coref_chains = []
		for i in range(0, len(chains)): #debug
			coref_chains.append(chains[i].mention)

		#print(len(coref_chains)) #debug


		coref_chains = get_longest_lists(coref_chains) #debug
		print('Collecting information from annotators. . .')
		start= time.time()
		
		character_dicts = []
		for chain in coref_chains:
			#print(" =========== CHAIN #"+ str(i) +" ===========") #for visualization purposes
			for mention in chain:
				senIndex = mention.sentenceIndex
				headTokenIndex = mention.headIndex

				try: sent = sentences[senIndex]
				except IndexError:
					print(len(sentences), senIndex)
					break

				coref_cluster = sent.token[headTokenIndex].corefClusterID
				ner_id = sent.token[headTokenIndex].entityMentionIndex
				canon_ner = nerMentions[ner_id].canonicalEntityMentionIndex

				character = {}
				#find the character with the same NER ID
				indexes = [i for i, item in enumerate(character_dicts) if item['nerID'] == canon_ner]
				if len(indexes) == 0:
					character['nerID'] = canon_ner
					character['clusterID'] = [coref_cluster]
					character['Name'] = nerMentions[canon_ner].entityMentionText
					character['Gender'] = mention.gender

					character_dicts.append(character)

				else:
					#print(len(indexes)) #debug

					if mention.mentionType == 'PRONOMINAL':
						cluster_ids = character_dicts[indexes[0]]['clusterID']
						if coref_cluster not in cluster_ids: 
							cluster_ids.append(coref_cluster)
							#print(cluster_ids) #debug
							character_dicts[indexes[0]]['clusterID'] = cluster_ids

					elif mention.mentionType == 'NOMINAL': print_coref_mention(mention,sentences)


				#character_dicts.append(character)
				#if len(character) > 0: print(character)


				#character = list(filter(lambda char: char['clusterID'] == index, characterDicts)) #find the character with the same coref cluster ID

			#end FOR mention loop
		#end FOR chain loop

		#mentions_dicts = [char.getDictRepresentation() for char in character_mentions]

		sen = ''
		for sentence in sentences:
			character_mentions = []

			if sentence.hasCorefMentionsAnnotation:
				for token in sentence.token:
					sen += token.originalText+' '

					if token.ner == 'PERSON':
						characters = list(filter(lambda person: person['nerID'] == token.entityMentionIndex, character_dicts))

						if len(characters) == 0: print(len(characters), token.entityMentionIndex, token.originalText)
						else:
							character_mentions.append(characters[0])

					elif len(token.corefMentionIndex) > 0:
						indexes = token.corefMentionIndex

						coref_ids = [corefMentions[i].corefClusterID for i in indexes]
						for index in coref_ids:
							characters = list(filter(lambda person: person['clusterID'] == index, character_dicts))
							if len(characters) > 0: character_mentions.append(characters[0])

						#end FOR index
					#end IF-ELSE end
				#end for TOKEN
			#end IF-ELSE

			sent = FicSentence(fic.index, sentence.sentenceIndex, sen, sentence.sentiment, character_mentions)
			fic_sentences.append(sent)
			

		#end FOR sentence

		for character in character_mentions:
			print(character['Name'], character['Gender'], character['clusterID'], character['nerID'])


	#end FOR ann loop

	#sen_dicts = [sen.getDictRepresentation() for sen in fic_sentences]

	

	end = time.time()
	print("...done. "+ str((end-start)/60) +" mins elapsed.")


