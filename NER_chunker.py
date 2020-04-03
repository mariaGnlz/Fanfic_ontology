#!/bin/bash/python3

import string, re
import nltk
#from nltk.corpus import conll2000
from nltk.stem.snowball import SnowballStemmer
from nltk.tag import ClassifierBasedTagger
from collections import Iterable

def word_shape(word):
	shape = 'other'

	if re.match('[0-9]+(\.[0-9]*)?|[0-9]*\.[0-9]+$', word): shape = 'number'
	elif re.match('\W+$', word): shape = 'punct'
	elif re.match('[A-Z][a-z]+$', word): shape = 'capitalized'
	elif re.match('[A-Z]+$', word): shape = 'allcaps'
	elif re.match('[a-z]+$', word): shape = 'alllower'
	elif re.match('[A-Z][a-z]+[A-Z][a-z]+[A-Za-a]*$', word): shape = 'camelcase'
	elif re.match('[A-Za-z]+$', word): shape = 'mixedcase'
	elif re.match('__-+__$', word): shape = 'wildcard'
	elif re.match('[A-Za-z0-9]+\.$', word): shape = 'dot-end'
	elif re.match('[A-Za-z0-9]+\.[A-Za-z0-9\.]+\.$', word): shape = 'abbreviation'
	elif re.match('[A-Za-z0-9]+\-[A-Za-z0-9\-]+.*$', word): shape = 'hyphenated'

	return shape
	
def feature_function(sentence, i, history):
	"""
	sentence: a POS-tagged sentence
	i: index of the current token
	history: previous IOB tags
	"""
	
	stemmer = SnowballStemmer('spanish') #must be changed to 'english' on final ver

	#Padding
	sentence = [('<START2>','<START2>'),('<START1>','<START1>')] + list(sentence) + [('<END1>','<END1>'),('<END2>','<END2>')]

	history = ['<START2>','<START1>'] + list(history)

	i += 2 #shift the index to accomodate padding

	word, pos = sentence[i]
	prevword, prevpos = sentence[i-1]
	previob = history[i-1]
	prevprevword, prevprevpos = sentence[i-2]
	prevpreviob = history[i-2]
	nextword, nextpos = sentence[i+1]
	nextnextword, nextnextpos = sentence[i+2]
	
	"""
	contains_dash = '-' in word
	contains_dot = '.' in word
	allascii = all([True for c in word if c in string.ascii_lowercase])
	allcaps = word == word.capitalize()
	capitalized = word[0] in string.ascii_uppercase
	prevallcaps = prevword == prevword.capitalize()
	prevcapitalized = prevword[0] in string.ascii_uppercase
	nextallcaps = nextword == nextword.capitalize()
	nextcapitalized = nextword[0] in string.ascii_uppercase
	"""

	return {
		'word': word,
		'lemma': stemmer.stem(word),
		'shape': word_shape(word),
		'pos': pos,
		
		'prev-word': prevword,
		'prev-lemma': stemmer.stem(prevword),
		'prev-shape': word_shape(prevword),
		'prev-pos': prevpos,

		'prevprev-word': prevprevword,
		'prevprev-lemma': stemmer.stem(prevprevword),
		'prevprev-shape': word_shape(prevprevword),
		'prevprev-pos': prevprevpos,

		'prev-iob': previob,
		'prevprev-iob': prevpreviob,

		'next-word': nextword,
		'next-lemma': stemmer.stem(nextword),
		'next-shape': word_shape(nextword),
		'next-pos': nextpos,

		'nextnext-word': nextnextword,
		'nextnext-lemma': stemmer.stem(nextnextword),
		'nextnext-shape': word_shape(nextnextword),
		'nextnext-pos': nextnextpos,
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


class NERChunkerv3(nltk.ChunkParserI):
	def __init__(self, train_sents):
		tagged_sents = [((w,t),c) for (w,t,c) in train_sents]#transform sentences to a shape that can be understood to the tagger
		self.tagger=NERTagger(tagged_sents)

	def parse(self, sentence):
		tagged_sents = self.tagger.tag(sentence)
		conlltags = [(w,t,c) for ((w,t),c) in tagged_sents]

		return nltk.chunk.conlltags2tree(conlltags)


class NERChunkerv2(nltk.ChunkParserI):
	def __init__(self, train_sents, **kwargs):
		assert isinstance(train_sents, Iterable)
		tagged_sents = [[((w,t),c) for (w,t,c) in
                                 nltk.chunk.tree2conlltags(sent)]
                                 for sent in train_sents] #transform sentences to a shape that can be understood to the tagger

		self.feature_detector = feature_function
		self.tagger = ClassifierBasedTagger(train=tagged_sents, feature_detector=feature_function, **kwargs)

	def parse(self, sentence):
		tagged_sents = self.tagger.tag(sentence)
		conlltags = [(w,t,c) for ((w,t),c) in tagged_sents]

		return nltk.chunk.conlltags2tree(conlltags)


class NERChunkerv1(nltk.ChunkParserI):
	def __init__(self, train_sents):
		tagged_sents = [[((w,t,),c) for (w,t,c) in                        nltk.chunk.tree2conlltags(sent)]
                               for sent in train_sents]#transform sentences to a shape that can be understood to the tagger


		self.tagger=NERTagger(tagged_sents)

	def parse(self, sentence):
		tagged_sents = self.tagger.tag(sentence)
		conlltags = [(w,t,c) for ((w,t),c) in tagged_sents]

		return nltk.chunk.conlltags2tree(conlltags)

