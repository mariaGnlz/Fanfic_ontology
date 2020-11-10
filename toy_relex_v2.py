#!/bin/bash/python3

import nltk, re, pprint, sys, time, pickle, pandas, numpy
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from sklearn.cluster import KMeans
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from stanza.server import CoreNLPClient

from collections import Counter
from NER_tagger_v3 import NERTagger
from fanfic_util import FanficCleaner

import matplotlib.pyplot as plt

### VARIABLES ###
POS_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_tags.csv'
POS_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/POS_typical_tags.csv'
NER_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/NER_tags.csv'
NER_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/NER_typical_tags.csv'

VERB_TAGS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
COLORMAP  = {0: 'red', 1: 'blue'}
### FUNCTIONS ###

def get_longest_lists(coref_chains): #returns the two longest chains in the coreference graph
	longest = []
	longest.append(max(list(coref_chains), key=len))

	coref_chains.remove(longest[0])

	longest.append(max(list(coref_chains), key=len))

	return longest
	

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

fCleaner = FanficCleaner()
NERtagger = NERTagger()

fic_list = fCleaner.clean_fanfics_in_range(8,9)
fic_text, fic_num = list(zip(*fic_list))
#print(fic_text[0]) #debug
#print(fic_num) #debug


fic_sents = [word_tokenize(sent) for sent in sent_tokenize(fic_text[0])]
"""
nlp = Pipeline(lang='en', processors='tokenize', tokenize_pretokenized=True)

doc = nlp(fic_sents)

for i, sent in enumerate(doc.sentences):
	print(f'==== Sentence {i+1} tokens ====')
	print(*[f'id:: {token.id}\ttext: {token.text}' for token in sent.tokens], sep='\n')

	if i == 11: break
"""
#print(len(fic_sents)/2) #debug

half_index = int(len(fic_sents)/2)

first_half = ''
for sent in fic_sents[:half_index]:
	for word in sent: first_half += str(word)+' '

second_half = ''
for sent in fic_sents[half_index:]:
	for word in sent: second_half += str(word)+' '

#text = [first_half, second_half]
text = [first_half] #debug

#print(len(first_half), len(second_half))#debug

print("\n###### Starting client and calling CoreNLP server ######\n")
start= time.time()

sentences = []
nerMentions = []
corefMentions = []
coref_chains = []
with CoreNLPClient(
	annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse','coref'],
        timeout=120000,
	be_quiet = True,
        memory='4G') as client:	
		
		print("Annotating data . . .")
		ann = client.annotate(first_half)

		print("...done")

		sentences = ann.sentence
		nerMentions = ann.mentions #NERMention[]
		corefMentions = ann.mentionsForCoref #Mention[]
		chain = ann.corefChain #CorefChain[], made up of CorefMention[]

		for i in range(0, len(chain)): #debug
			coref_chains.append(chain[i].mention)


#print(len(coref_chains)) #debug

end = time.time()
print("Client closed. "+ str((end-start)/60) +" mins elapsed")

start = time.time()
print("Processing annotation data...")


coref_chains = get_longest_lists(coref_chains) #debug

characterMentions = []
i = 0
for chain in coref_chains:
	print(" =========== CHAIN #"+ str(i) +" ===========")
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

print(len(characterMentions)) #debug
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

start = time.time()
print("Initializing  and fitting KMeans model...")
model = KMeans(init='k-means++', n_clusters=2, n_init=5)
model.fit(data)
predict = model.predict(data)

data['category'] = model.labels_

#for i in range(0,1): print(data.iloc[i,:]) #debug
end = time.time()
print("...done. "+ str((end-start)/60) +" mins elapsed.")

#Print who belongs to which cluster
#print(data.shape)	

#selection = data.loc[['category','clusterID','nerID']]
#print(selection)

print(data[['category','clusterID','nerID']].values)

"""
#Generate scatterplot
colors = list(map(lambda x: '#3b4cc0' if x == 1 else '#b40426', predict))

data = vec1.inverse_transform(data)
colors = data.apply(lambda row: COLORMAP[row.category], axis=1)

ax = data.plot(kind='scatter', x='name', y='gender', alpha=0.2, s=300, c=colors)

"""			
"""
print(sentences[55].token[5]) #debug #example of accessing data in sentences

pronominal = []
for sen in sentences:
	for token in sen.token:
		if token.corefClustedID == 553 and token.ner = "O": pronominal.append(token) #get pronominal mentions of character with id 553

"""

