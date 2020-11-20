#!/bin/bash/python3

import sys, time, pickle, pandas, numpy
from sklearn.cluster import KMeans
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from corenlp_wrapper import CoreClient

from NER_tagger_v3 import NERTagger
from fanfic_util import FanficGetter, Fanfic

import matplotlib.pyplot as plt

### VARIABLES ###

VERB_TAGS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
COLORMAP  = {0: 'red', 1: 'blue'}

### FUNCTIONS ###

def get_longest_lists(coref_chains): #returns the two longest chains in the coreference graph
	longest = []
	longest.append(max(list(coref_chains), key=len))

	coref_chains.remove(longest[0])

	longest.append(max(list(coref_chains), key=len))

	return longest

def print_coref_mention(mention):
	print(mention.mentionID, mention.corefClusterID, mention.mentionType, mention.gender, mention.animacy, mention.number)

def print_ner_mention(mention):	
	print(mention.entityMentionIndex, mention.canonicalEntityMentionIndex, mention.ner, mention.gender, mention.entityMentionText)

### CLASSES ###

class FicCharacteristics():
	def __init__(self, ID, characterA, characterB,  sentiment, tf_id, rel_tag):
		self.ID = ID
		self.characterA = characterA
		self.characterB = characterB
		self.sentiment = sentiment
		self.tf_id = tf_id
		self.rel_tag = rel_tag

	def getDictRepresentation(self):	
		return {
			'id': self.ID,
			'characterA': self.characterA,
			'characterB': self.characterB,
			'sentiment': self.sentiment,
			'tf_id': self.tf_id,
			'rel_tag': self.rel_tag,
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

fGetter = FanficGetter()
NERtagger = NERTagger()
client = CoreClient()

print('Fetching fic texts...')
start = time.time()

fic_list = fGetter.get_fanfics_in_range(8,9)
fic_texts = [fic.chapters for fic in fic_list]
#print(len(fic_texts[0]), type(fic_texts[0][0])) #debug

end = time.time()
print("...fics fetched. Elapsed time: ",(end-start)/60," mins")


print('\n###### Starting client and calling CoreNLP server ######\n')
start= time.time()

sentences = []
nerMentions = []
corefMentions = []
coref_chains = []
chains = []
for fic in fic_texts:
	anns = client.parse(fic)

	for ann in anns:
		sentences= ann.sentence
		nerMentions = ann.mentions #NERMention[]
		corefMentions = ann.mentionsForCoref #Mention[]
		chains = ann.corefChain #CorefChain[], made up of CorefMention[]

		for i in range(0, len(chains)): #debug
			coref_chains.append(chains[i].mention)

		#print(len(coref_chains)) #debug

		end = time.time()
		print("Client closed. "+ str((end-start)/60) +" mins elapsed")

		start = time.time()
		print("Processing annotation data...")


		coref_chains = get_longest_lists(coref_chains) #debug

		characterMentions = []
		i = 0
		for chain in coref_chains:
			#print(" =========== CHAIN #"+ str(i) +" ===========") #for visualization purposes
			for mention in chain:
				senIndex = mention.sentenceIndex
				tokBIndex = mention.beginIndex
				tokEIndex = mention.endIndex
				clusterID = corefMentions[mention.mentionID].corefClusterID
				entityID = nerMentions[sentences[mention.sentenceIndex].token[mention.beginIndex].entityMentionIndex].canonicalEntityMentionIndex
				entityName = str(nerMentions[sentences[mention.sentenceIndex].token[mention.beginIndex].entityMentionIndex].entityMentionText)
				mentionText = sentences[mention.sentenceIndex].token[mention.beginIndex].originalText
	
				character = CharacterMention(i, mentionText, entityName, corefMentions[mention.mentionID].gender, corefMentions[mention.mentionID].animacy, corefMentions[mention.mentionID].number, clusterID, entityID, [], [])
				characterMentions.append(character)

			#if i < 10: print(character.getDictRepresentation()) #debug

				i+=1


			#print("Sentence "+ senIndex +"	|	tokens "+ tokBIndex +"-"+ tokEIndex +"	|	"+ mention.mentionType +"	|	cluster  "+ clusterID +"	|	entity "+ entityID +" "+ entityName +"	|	text: "+  mentionText) #for visualization purposes

		print("CanonicalEntityMentionIndex for nerMentions[0]: ",nerMentions[0].canonicalEntityMentionIndex) #debug
		print("number or character mentions: ", len(characterMentions)) #debug
		characterDicts = [char.getDictRepresentation() for char in characterMentions]

		end = time.time()
		print("Annotations processed. "+ str((end-start)/60) +" mins elapsed")

		print("\n###### Starting clustering process ######\n")

		start = time.time()
		print("Get dictionary and Tfid vectorization...")
		vec1 = DictVectorizer()
		vec2 = TfidfTransformer() #this one is for normalization

		vec_data = vec1.fit_transform(characterDicts) #toarray?
		#print("before tfid", vec_data.shape) #debug
		#vec_data = vec2.fit_transform(vec_data)
		#print("after tfid", vec_data.shape) #debug
		#print(vec1.get_feature_names()) #debug

		data = pandas.DataFrame(vec_data.toarray(), columns = vec1.get_feature_names())


		end = time.time()
		print("...done. "+ str((end-start)/60) +" mins elapsed.")



		#for i in range(0,1): print(data.iloc[i,:]) #debug
		end = time.time()
		print("...done. "+ str((end-start)/60) +" mins elapsed.")

		print("Navigate sentences with more than one PERSON entity\n")
		for sentence in sentences:
			sen = ''
			ner_indexes = []
			ners = 0
			coref_indexes = []

			for token in sentence.token:
				sen += token.originalText+' '

				if token.ner == 'PERSON': ners += 1

			if ners > 1:
				for token in sentence.token:
					if token.ner == 'PERSON':
						print(token.originalText, token.ner, token.gender)
						print(nerMentions[token.entityMentionIndex].canonicalEntityMentionIndex, nerMentions[token.entityMentionIndex].ner, nerMentions[token.entityMentionIndex].gender, nerMentions[token.entityMentionIndex].entityMentionText)

						if len(token.corefMentionIndex) > 0:
							for index in token.corefMentionIndex: print(corefMentions[index].corefClusterID)

					elif len(token.corefMentionIndex) > 0:
						for index in token.corefMentionIndex:
							if corefMentions[index].mentionType == 'PRONOMINAL':
								character = list(filter(lambda char: char['clusterID'] == corefMentions[index].corefClusterID, characterDicts)) #find the character with the same cluster ID

								if len(character) < 1:
									print(token.originalText, corefMentions[index].corefClusterID, corefMentions[index].mentionType, corefMentions[index].gender, corefMentions[index].number, corefMentions[index].animacy)

								else:
									character = character[0]
									if character['name'] != '': print(character['name'], corefMentions[index].corefClusterID, corefMentions[index].mentionType, corefMentions[index].gender, corefMentions[index].number, corefMentions[index].animacy)

									else: print(token.originalText, corefMentions[index].corefClusterID, corefMentions[index].mentionType, corefMentions[index].gender, corefMentions[index].number, corefMentions[index].animacy)

							else: print(token.originalText, corefMentions[index].corefClusterID, corefMentions[index].mentionType, corefMentions[index].gender, corefMentions[index].number, corefMentions[index].animacy)

					else: print(token.originalText)

				print("\n\n")


