#!/bin/bash/python3

import nltk, pprint
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from NER_chunker import NERChunker

trial = NERChunker.parse(pos_tag(word_tokenize('Una comunidad hospitalaria en medio del desierto, en donde el sol calienta, la luna es preciosa, y luces misteriosas sobrevuelan nuestras cabezas mientras todos fingimos estar durmiendo. Bienvenidos a Night Vale')))

print('WTNV NER:\n', trial)

trial = nltk.ne_chunk(pos_tag(word_tokenize('Una comunidad hospitalaria en medio del desierto, en donde el sol calienta, la luna es preciosa, y luces misteriosas sobrevuelan nuestras cabezas mientras todos fingimos estar durmiendo. Bienvenidos a Night Vale')))

print('WTNV NE:\n', trial)

trial = NERChunker.parse(pos_tag(word_tokenize('En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua, rocín flaco y galgo corredor.')))

print ('Quijote NER:\n',trial)

trial = nltk.ne_chunk(pos_tag(word_tokenize('En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua, rocín flaco y galgo corredor.')))

print ('Quijote NE:\n',trial)
