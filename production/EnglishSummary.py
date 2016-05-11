#TF weighted model Summarization for English text; no special feature or text structure are taken into consideration.
#usage : result = summaryToDBCH(text) 

import sys, re, os
import subprocess
import random
from nltk.corpus import wordnet as wn 
import nltk.data

from nltk.corpus import stopwords #stopword to detect languages
from nltk.tokenize import wordpunct_tokenize #function to split our words

from collections import defaultdict, namedtuple
from math import sqrt
import json




tokenizers = nltk.data.load("tokenizers/punkt/english.pickle")

alphaU = "A B C D E F G H I J K L M  N O P Q R S T U V W X Y Z".split()

exp_email = r'@[\w\d]+\.[\w\d]+'
comp_email = re.compile(exp_email)

exp_url = r'(http|https|ftp)://'
comp_url = re.compile(exp_url)

#exp_header = r' *(\w+ et al\..* \d+|\d+ .* \w+ et al\.)'
exp_header = r' *(et al\. ?:.* \d+|\d+ .* [\w ]+ et al\. ?:)'
comp_header = re.compile(exp_header, re.I)
SEGMENT_PATH="."

def load_stop_words(stop_word_file):
	"""
	Utility function to load stop words from a file and return as a list of words
	@param stop_word_file Path and file name of a file containing stop words.
	@return list A list of stop words.
	"""
	stop_words = []
	for line in open(stop_word_file):
		if line.strip()[0:1] != "#":
			for word in line.split():  # in case more than one per line
				stop_words.append(word)
	return stop_words

def calculate_phrases_scores_TF(sentenceList, stopwordList, NE = 1, ABBR = 1, CIT = 1):#NE->name entity; ABBR->abbrevation; CIT->citation
	stopwordList += [',','.','!',';',':','\'','"']	
	sentenceKeywordList = defaultdict(list)
	phraseFreq = defaultdict(float)
	for realS in sentenceList:
		#x = s.rpartition("(")[0]
		#print s
		
		x = re.sub('[^a-zA-Z0-9_\t!?,;:\.\\+\\-\\$@#\'\"/ \(\)]', "", realS)
		x = re.sub('([,\.!;:\'\"]) ',r' \1 ', x)
		s = x.replace("  ", " ")
		m = re.findall(r'\([A-Z]+\)', s)
		abbrCount = len(m)
		citationCount = len(re.findall(r'\[\d+\]', s))
		wordList = s.split()
		for kgram in range(0,3):
			for i in range(0, len(wordList)-kgram):#unigram, bigram, trigram
				if wordList[i].lower() in stopwordList:
					continue	
				candidatePhrase = " ".join(wordList[i:i+kgram+1])
				if candidatePhrase not in sentenceKeywordList[realS]:
					sentenceKeywordList[realS].append(candidatePhrase)
					#print candidatePhrase
				phraseFreq[candidatePhrase] += 1.0
				phraseFreq[candidatePhrase] += 0.05*kgram

			
		sentenceKeywordList[realS].append(abbrCount)
		sentenceKeywordList[realS].append(citationCount)
	for stopword in stopwordList:
		phraseFreq[stopword] = 0
	return sentenceKeywordList, phraseFreq

def generate_sentences_rating(sentenceKeywordList, phraseScore, NE = 1, ABBR = 1, CIT = 1):
	sentenceRating = defaultdict(float)
	phrasesTotal = sum(phraseScore.values())
	for (s, k) in sentenceKeywordList.iteritems():
		for p in k[:-2]:
			sentenceRating[s] += (phraseScore[p]*1.0 / phrasesTotal)
		for (p, q) in zip(k[-2:], [int(ABBR), int(CIT)]):
			sentenceRating[s] += (p * q * 1.0 / 100)
	#for s, k in sentenceRating.iteritems():
	#	print s, k	
	return sentenceRating				

def calculateSentenceRating(text, inputType, NE=1, ABBR=1, CIT=1):
	
	#text is a sentence array
	sentenceList = text
	stoppath = "SmartStoplist.txt"
	stopwordList = load_stop_words(stoppath)
	#stopwordpattern = build_stop_word_regex(stoppath)
		
	(sentenceKeywordList, phraseScore) = calculate_phrases_scores_TF(sentenceList, stopwordList)
	sentenceRating = generate_sentences_rating(sentenceKeywordList, phraseScore, NE, ABBR, CIT)
	rate = lambda s : sentenceRating[s]
	
	newSentences = [{"sentence":s, "position":o, "ranking":rate(s)} for o, s in enumerate(sentenceList)]
		
	return json.JSONEncoder().encode(newSentences)



def normalSummary(text):
	pid = str(os.getpid())+"_"+str(random.randint(1,10000))
	filename = "/tmp/"+pid+".tmp"
	text = text.replace("\r\n", " ")
	text = text.replace("\n", " ")
	sentences = tokenizers.tokenize(text)
	fout = open(filename, "w")
	#with open("/tmp/"+pid+".tmp", "w") as fout:
	for s in sentences:
		fout.write(s)
		fout.write("\n")
	fout.write("="*10)
	fout.close()
	#cwd = os.getcwd()
	
	cmd2 = "cat "+filename+" | sh "+os.path.join(SEGMENT_PATH, "segment")
	ps = subprocess.Popen(cmd2,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
	try:
		boundary = eval(ps.communicate()[0])
		#print boundary
	except:
		return calculateSentenceRating(sentences, "other")
	bStart = 0
	newText = []
	for b in boundary:
		newText.append(" ".join(sentences[bStart:int(b)]))
		#newText += "\n"
		bStart = b
	os.remove(filename)
	return calculateSentenceRating(newText, "other")

def summaryEntryToDB(text):

	return normalSummary(text)


if __name__ == "__main__":
	summaryEntryToDB("")
