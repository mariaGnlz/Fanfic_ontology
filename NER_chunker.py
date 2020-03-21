#!/bin/bash/python3

import string
import nltk
#from nltk.corpus import conll2000
from nltk.stem.snowball import SnowballStemmer

def feature_function(sentence, i, history):
	"""
	sentence: a POS-tagged sentence
	i: index of the current token
	history: previous IOB tags
	"""
	
	stemmer = SnowballStemmer('spanish')

	#Padding
	sentence = [('<START2>','<START2>'),('<START1>','<START1>')] + list(sentence) + [('<END1>','<END1>'),('<END2>','<END2>')]

	history = ['<START2>','<START1>'] + list(history)

	i += 2 #shift the index to accomodate padding

	word, pos = sentence[i]
	prevword, prevpos = sentence[i-1]
	prevprevword, prevprevpos = sentence[i-2]
	nextword, nextpos = sentence[i+1]
	nextnextword, nextnextpos = sentence[i+2]
	previob = history[i-1]
	
	contains_dash = '-' in word
	contains_dot = '.' in word
	allascii = all([True for c in word if c in string.ascii_lowercase])
	allcaps = word == word.capitalize()
	capitalized = word[0] in string.ascii_uppercase
	prevallcaps = prevword == prevword.capitalize()
	prevcapitalized = prevword[0] in string.ascii_uppercase
	nextallcaps = nextword == nextword.capitalize()
	nextcapitalized = nextword[0] in string.ascii_uppercase

	return {
		'word': word,
		'lemma': stemmer.stem(word),
		'pos': pos,
		'all-ascii': allascii,
		
		'prev-word': prevword,
		'prev-lemma': stemmer.stem(prevword),
		'prev-pos': prevpos,
		'prev-all-caps': prevallcaps,
		'prev-capitalized': prevcapitalized,

		'prevprev-word': prevprevword,
		'prevprev-pos': prevprevpos,

		'prev-iob': previob,

		'next-word': nextword,
		'next-lemma': stemmer.stem(nextword),
		'next-pos': nextpos,
		'next-all-caps': nextallcaps,
		'next-capitalized': nextcapitalized,

		'nextnext-word': nextnextword,
		'nextnext-pos': nextnextpos,

		'contains-dash': contains_dash,
		'contains-dot': contains_dot,
		'all-caps': allcaps,
		'capitalized': capitalized,	
	}


	
class NERTagger(nltk.TaggerI):
	def __init__(self, train_sents):
		train_set = []

		for tagged_sent in train_sents:
			untagged_sent = nltk.tag.untag(tagged_sent)
			history = []

			for i, (word,tag) in enumerate(tagged_sent):
				featureset = feature_function(untagged_sent, i, history)
				train_set.append( (featureset, tag) ) #sentence[1] is the tag of the token

				history.append(tag)

		self.classifier = nltk.MaxentClassifier.train(train_set,
                                  algorithm='megam', trace=0)

	def tag(self,sentence):
		history = []
		for i, word in enumerate(sentence):
			featureset = feature_function(sentence, i, history)
			tag = self.classifier.classify(featureset)
			history.append(tag)
		
		return zip(sentence, history)


class NERChunker(nltk.ChunkParserI):
	def __init__(self, train_sents):
		tagged_sents = [[((w,t,),c) for (w,t,c) in nltk.chunk.tree2conlltags(sent)]
                               for sent in train_sents]

		self.tagger=NERTagger(tagged_sents)

	def parse(self, sentence):
		tagged_sents = self.tagger.tag(sentence)
		conlltags = [(w,t,c) for ((w,t),c) in tagged_sents]

		return nltk.chunk.conlltags2tree(conlltags)

