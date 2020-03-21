#!/bin/bash/python3

import nltk
from nltk.corpus import conll2000


class UnigramChunker(nltk.ChunkParserI):
	def __init__(self, train_sents):
		train_data = [[(t,c) for w,t,c in nltk.chunk.tree2conlltags(sent)] for sent in train_sents]
		self.tagger = nltk.UnigramTagger(train_data)

	def parse(self, sentence):
		pos_tags = [pos for (word,pos) in sentence]
		tagged_pos_tags = self.tagger.tag(pos_tags)
		chunktags = [chunktag for (pos, chunktag) in tagged_pos_tags]
		conlltags = [(word, pos, chunktag) for ((word,pos),chunktag) in zip(sentence, chunktags)]
	
		return nltk.chunk.conlltags2tree(conlltags)
#end UnigramChunker


class BigramChunker(nltk.ChunkParserI):
	def __init__(self, train_sents):
		train_data = [[(t,c) for w,t,c in nltk.chunk.tree2conlltags(sent)] for sent in train_sents]
		self.tagger = nltk.BigramTagger(train_data)

	def parse(self, sentence):
		pos_tags = [pos for (word,pos) in sentence]
		tagged_pos_tags = self.tagger.tag(pos_tags)
		chunktags = [chunktag for (pos, chunktag) in tagged_pos_tags]
		conlltags = [(word, pos, chunktag) for ((word, pos),chunktag) in zip(sentence, chunktags)]

		return nltk.chunk.conlltags2tree(conlltags)

#end BigramChunker

def npchunk_features(sentence, i, history):
	word, pos = sentence[i]
	return {'pos':pos}

class ConsecutiveNPChunkTagger(nltk.TaggerI):
	def __init__(self, train_sents):
		train_set = []

		for tagged_sent in train_sents:
			untagged_sent = nltk.tag.untag(tagged_sent)
			history = []

			for i, (word, tag) in enumerate(tagged_sent):
				featureset = npchunk_features(untagged_sent, i, history)
				train_set.append( (featureset, tag) )

				history.append(tag)

		self.classifier = nltk.MaxentClassifier.train(train_set, algorithm='megam', trace=0)

	def tag(self,sentence):
		history = []
		for i, word in enumerate(sentence):
			featureset = npchunk_features(sentence, i, history)
			tag = self.classifier.classify(featureset)
			history.append(tag)
		
		return zip(sentence, history)

#end ConsecutiveNPChunkTagger


class ConsecutiveNPChunker(nltk.ChunkParserI):
	def __init__(self, train_sents):
		tagged_sents = [[((w,t),c) for (w,t,c) in nltk.chunk.tree2conlltags(sent)] for sent in train_sents]

		self.tagger=ConsecutiveNPChunkTagger(tagged_sents)

	def parse(self, sentence):
		tagged_sents = self.tagger.tag(sentence)
		conlltags = [(w,t,c) for ((w,t),c) in tagged_sents]

		return nltk.chunk.conlltags2tree(conlltags)

#end ConsecutiveNPChunker

