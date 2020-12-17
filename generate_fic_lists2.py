#!/usr/bin/bash/python3

from fanfic_util import FanficGetter
from fanfic_util import FanficHTMLHandler

import string, sys, re

### VARIABLES ###
FIC_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/html_fic_paths.txt'
ROMANCE_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/romance_fic_paths3.txt'
FRIENDSHIP_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/friendship_fic_paths3.txt'
ENEMY_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/enemy_fic_paths3.txt'
#EXPLICIT_LISTING_PATH = '/home/maria/Documents/Fanfic_ontology/explicit_fic_paths.txt'
#OUT = '/home/maria/Documents/Fanfic_ontology/TFG_logs/generate_fic_lists_discardlog3.txt'

ENEMY_TAGS = ['Graphic Depictions Of Violence', 'Rape/Non-Con', 'Torture', 'Mind Rape', 'Dead Dove: Do Not Eat']
MATURE_RATINGS = ['Mature', 'Explicit']
FANDOM_TAGS = ['Good Omens - Neil Gaiman & Terry Pratchett', ' Good Omens (TV)']

### MAIN ###

#Initialize handlers, get fanfic paths
fgetter = FanficGetter()
handler = FanficHTMLHandler()

html_fics = fgetter.get_fic_paths_in_list()
#print(fgetter.get_fic_listing_path()) #debug
#print(html_fics[:10]) #debug


romance_fics = []
friendship_fics = []
enemy_fics = []
explicit_fics = []

romance = False
friendship = False

gomens_fanfics = []
for path in html_fics:
	fandoms = handler.get_fandoms(path)

	if all(fandom in FANDOM_TAGS for fandom in fandoms): gomens_fanfics.append(path)

for path in gomens_fanfics:
	chapters = handler.get_chapters(path)
	ships = handler.get_relationships(path)
	tags = handler.get_tags(path)
	#rating = handler.get_rating(path)

	#if chapters[0] == 1 : print(chapters, rating) #debug

	#This hand of the IF-ELSE handles romance, frienship, and fics featuring rape. Because they're very popular, and can feature in long fics, we're restricting it to fics than only have one chapter to ensure that we get the essential characteristics
	if chapters == [1,1]:
		
		if len(ships) == 1:
			ship = ships[0]

			if re.match('(\s*\w* \w*/\w* \w*)|(\s*\w*/\w*)', ship): #If the fic has a sexual or romantic relationship tag
				if 'Rape/Non-Con' in tags: enemy_fics.append(path)
				#elif rating in MATURE_RATINGS: explicit_fics.append(path)
				else: romance_fics.append(path)

			elif re.match('(\s*\w* \w* & \w* \w*)|(\s*\w* & \w*)', ship) or re.match('(\s*\w* \w* and \w* \w*)|(\s*\w* and \w*)', ship, re.IGNORECASE): #If the fic has a friendship relationship tag
				friendship_fics.append(path)
		

	elif int(chapters[0]) < 6: #This hand of the IF-ELSE handles enemy relationships. It's much less popular, so we admit longer fics
		if len(ships) < 2: #We do not want friendship or romance here, we admit one at max
			tags = handler.get_tags(path)

			if any(tag in ENEMY_TAGS for tag in tags): enemy_fics.append(path)
			
			
				


print("Total romance fics: ", len(romance_fics))
print("Total friendship fics: ", len(friendship_fics))
print("Total enemy fics: ", len(enemy_fics))
#print("Total explicit fics: ", len(explicit_fics))

#Save path lists

for path in romance_fics:
	f = open(ROMANCE_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()


for path in friendship_fics:
	f = open(FRIENDSHIP_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()

for path in enemy_fics:
	f = open(ENEMY_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()
"""
for path in explicit_fics:
	f = open(EXPLICIT_LISTING_PATH, 'a')
	f.write(path+'\n')
	f.close()
"""
