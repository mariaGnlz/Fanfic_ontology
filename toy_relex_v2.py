#!/bin/bash/python3

import nltk, re, pprint, sys, time, pickle, pandas
from nltk.tokenize import word_tokenize, sent_tokenize
from stanza import Pipeline
from stanza.server import CoreNLPClient
from nltk.tag import pos_tag
from collections import Counter
from NER_tagger_v3 import NERTagger
from fanfic_util import FanficCleaner

### VARIABLES ###
POS_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/POS_tags.csv'
POS_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/POS_typical_tags.csv'
NER_TAGGED_FICS_PATH = '/home/maria/Documents/Fanfic_ontology/NER_tags.csv'
NER_TYPICAL_PATH = '/home/maria/Documents/Fanfic_ontology/NER_typical_tags.csv'

VERB_TAGS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
### FUNCTIONS ###


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

print(len(first_half), len(second_half))

sentences = []
nerMentions = []
corefMentions = []
coref_chains = []
with CoreNLPClient(
	annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse','coref'],
        timeout=120000,
	be_quiet = True,
        memory='4G') as client:	
		ann = client.annotate(first_half)

		sentences = ann.sentence
		nerMentions = ann.mentions #NERMention[]
		corefMentions = ann.mentionsForCoref #Mention[]
		chain = ann.corefChain #CorefChain[], made up of CorefMention[]

		for i in range(0, len(chain)): #debug, cambiar luego a len(chain)
			coref_chains.append(chain[i].mention)


#print(len(coref_chains)) #debug

i = 0
for chain in coref_chains:
	print(" =========== CHAIN #"+ str(i) +" ===========")
	for mention in chain:
		senIndex = str(mention.sentenceIndex)
		tokBIndex = str(mention.beginIndex)
		tokEIndex = str(mention.endIndex)
		clusterID = str(corefMentions[mention.mentionID].corefClusterID)
		entityID = str(nerMentions[sentences[mention.sentenceIndex].token[mention.beginIndex].entityMentionIndex].canonicalEntityMentionIndex)
		entityName = nerMentions[sentences[mention.sentenceIndex].token[mention.beginIndex].entityMentionIndex].entityMentionText

		print("Sentence "+ senIndex +"	|	tokens "+ tokBIndex +"-"+ tokEIndex +"	|	"+ mention.mentionType +"	|	cluster  "+ clusterID +"	|	entity "+ entityID +" "+ entityName +"	|	text: "+  sentences[mention.sentenceIndex].token[mention.beginIndex].originalText)	

	i+=1
				
"""
print(sentences[55].token[5]) #debug #example of accessing data in sentences

pronominal = []
for sen in sentences:
	for token in sen.token:
		if token.corefClustedID == 553 and token.ner = "O": pronominal.append(token) #get pronominal mentions of character with id 553

"""

