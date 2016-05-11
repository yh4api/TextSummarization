# -*- coding:utf-8 -*-
# process : 分句(標點符號)-> 分詞(jieba) -> segmentation(vseg) -> sum_ch.py (還要n-gram嗎?)
# usage : result = summaryToDBCH(text) 
# version '160506 return result in json [{sentence, sentence_pos, sentence_ranking}]
import sys, os, re
import subprocess
import jieba
from collections import defaultdict, namedtuple
import operator
import random
import json

SEGMENT_PATH = "."


def load_CHstop_words(stop_word_file):
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

def calculate_CHphrases_scores_TF(sentenceList, stopwordList, NE = 0, ABBR = 0, CIT = 0):#NE->name entity; ABBR->abbrevation; CIT->citation
	
	sentenceKeywordList = defaultdict(list)
	phraseFreq = defaultdict(float)
	for s in sentenceList:
#		x = s.rpartition("(")[0]

#		x = re.sub('[^a-zA-Z0-9_\t!?,;:\.\\+\\-\\$@#\'\"/ \(\)]', "", x)
	
		#m = re.findall(r'\([A-Z]+\)', s)
		#abbrCount = len(m)
		abbrCount = 0
		citationCount = len(re.findall(r'\[\d+\]', s))
		wordList = s.split()
		#print s
		for kgram in range(0,3):
			for i in range(0, len(wordList)-kgram):#unigram, bigram, trigram

				candidatePhrase = " ".join(wordList[i:i+kgram+1])
				if candidatePhrase not in sentenceKeywordList[s]:
					sentenceKeywordList[s].append(candidatePhrase)
					#print candidatePhrase
				phraseFreq[candidatePhrase] += 1.0
				phraseFreq[candidatePhrase] += 0.05*kgram

			
		sentenceKeywordList[s].append(abbrCount)
		sentenceKeywordList[s].append(citationCount)
	for stopword in stopwordList:
		phraseFreq[stopword] = 0
	return sentenceKeywordList, phraseFreq

def generate_CHsentences_rating(sentenceKeywordList, phraseScore, NE = 0, ABBR = 0, CIT = 0):
	sentenceRating = defaultdict(float)
	phrasesTotal = sum(phraseScore.values())
	for (s, k) in sentenceKeywordList.iteritems():
		for p in k[:-2]:
			sentenceRating[s] += (phraseScore[p]*1.0 / phrasesTotal)
		for (p, q) in zip(k[-2:], [int(ABBR), int(CIT)]):
			sentenceRating[s] += (p * q * 1.0 / 100)
	#for p, k in phraseScore.iteritems():
	#	print p, k
	#for s, k in sentenceRating.iteritems():
	#	print s, k	
	return sentenceRating				


def calculateCHSentenceRating(text, origText, inputType, NE = 0, ABBR = 0, CIT = 0):
	
	#sentenceList = text.splitlines()
	#text is segmented sentence array, origText is the orig sentence array
	sentenceList = text
	stoppath = "ChineseStoplist.txt"
	stopwordList = load_CHstop_words(stoppath)
	#stopwordpattern = build_stop_word_regex(stoppath)
		
	(sentenceKeywordList, phraseScore) = calculate_CHphrases_scores_TF(sentenceList, stopwordList)
	sentenceRating = generate_CHsentences_rating(sentenceKeywordList, phraseScore)
	
	rate = lambda s : sentenceRating[s]
	newSentences = [{"sentence":origText[o].encode("utf-8"), "position":o, "ranking":rate(s)} for o, s in enumerate(sentenceList)]
	#newSentences = [{"sentence":s, "position":o, "ranking":rate(s)} for o, s in enumerate(sentenceList)] this fails if the text contains both English and Chinese, whose delimiter is not a space.
		
	return json.JSONEncoder().encode(newSentences)
	

def noGetSortedSentencesCH(text, threshold=1):#threshold value range is from 1~100
	sentenceOrder = {}
	sentenceList = text.split("\n")
	
	#Change threshold from sentence numbers to sentence percentage '150508
	"""
	if threshold < 1:
		threshold = 1
	if threshold >= len(sentenceList):
		threshold = len(sentenceList)-1	
	"""
	percentage = threshold
	sentenceAmount = ((len(sentenceList)-1)*threshold/100) + 1
	threshold = sentenceAmount
	if sentenceAmount < 1:
		threshold = 1
	if sentenceAmount >= len(sentenceList):
		threshold = len(sentenceList)-1	
	
	for s in sentenceList[:threshold]:
		tmp = s.split("!@#")
		sentenceOrder[tmp[0]]=int(tmp[1])

	newSentenceList = []
	for (k,v) in sorted(sentenceOrder.iteritems(), key=lambda(k,v):(v,k)):
		newSentenceList.append(k)

	return "\n\n".join(newSentenceList)

def toSplitSentences(text):
	#print text
	sentences = re.split(u'([。；！？])', text)
	return sentences

def tokenize(sentence):
	seg_list = jieba.cut(sentence)
	return " ".join(seg_list)

def segmentUI(filename, pid):
	#print filename
	#cwd = os.getcwd()
	#os.chdir("bayesseg/baselines/textseg-1.211/")
	cmd2 = "cat "+filename+" | sh SegSh "+pid
	ps = subprocess.Popen(cmd2,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
	outtmp = ps.communicate()
	
	try:
		(segFile, textFile) = outtmp[0].split()
	except:
		#print "text size is too big!"
		os.remove("/tmp/Seg."+pid+".seg")
		os.remove("/tmp/Seg."+pid+".txt")
		return [], []
	#modify seg-comb to get boundary and segGroup 0701
	seg = open(segFile, "r").read()
	boundary = map(lambda x:int(x), seg.split()[1:])
	
	segGroup = []
	newGroup = ""
	b = boundary.pop(0)
	with open(textFile, "r") as ftext:
		b = boundary.pop(0)
		lineid = 0
		for line in ftext:
			lineid += 1
			newGroup+=line
			#print lineid, b, lineid >= b
			if lineid >= b :
				segGroup.append(newGroup)
				#print newGroup
				newGroup = ""
				if len(boundary) > 0:
					b = boundary.pop(0)
		ftext.close()
	
	boundary = map(lambda x:int(x), seg.split()[2:])
	#print boundary

	"""
	boundary = []
	boundaryId = 0
	segGroup = []
	newGroup = ""
	for o in out[1:]:
		if o.startswith("="*10):
			segGroup.append(newGroup)
			newGroup = ""
			boundary.append(boundaryId)
			continue
		newGroup += o
		boundaryId += 1
	"""		
	
	#os.chdir(cwd)
	os.remove(segFile)
	os.remove(textFile)
	return segGroup, boundary

def segmentBayesseg(filename):
	#print filename
	#cwd = os.getcwd()
	#os.chdir(SEGMENT_PATH)	
	cmd2 = "cat "+filename+ " | sh "+os.path.join(SEGMENT_PATH, "segment")
	ps = subprocess.Popen(cmd2,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

	boundary = eval(ps.communicate()[0])
	#print boundary
	bStart = 0
	segGroup = []
	sentences = open(filename, "r").read().splitlines()
	if sentences[-1] =="="*10: #this check is for Chinese only
		sentences[-1] = ""
	for b in boundary:
		segGroup.append(" ".join(sentences[bStart:int(b)]))
		#newText += "\n"
		bStart = int(b)
	#for sid, s in enumerate(segGroup):
	#	print sid, s
	#os.chdir(cwd)
	#return segGroup 
	return segGroup, boundary


def getTokenizedText(text):
	sentences = toSplitSentences(text)
	newTkSentences = []
	newSentences = []

	for sIndex in range(0, len(sentences), 2):
		tokenizedS = tokenize("".join(sentences[sIndex:sIndex+2]))
		newTkSentences.append(tokenizedS)
		newSentences.append("".join(sentences[sIndex:sIndex+2]))

	return newTkSentences, newSentences

def summaryToDBCH(text):
	pid = str(os.getpid())+"_"+str(random.randint(1,10000))
	text = text.decode("unicode-escape")
	text = text.replace("\r\n", " ")
	text = text.replace("\n", " ")
	try:
		(tokenizedSentences, splitSentences) = getTokenizedText(text)
	except:
		with open("./log/"+pid+".err", "w") as f:
			f.write(text.encode("utf-8"))
		reload(jieba)
		return "null"
	#filename = "tmp.txt"
	filename = os.path.join("/tmp", pid+".tmp")
	with open(filename, "w") as ftmp:
		for sentence in tokenizedSentences:
			
			ftmp.write(sentence.encode("utf-8")) # this is important, make Segmentation work for Chinese!
			# \n works on Linux but not on windows. Seems \r\n works for both(?)
			ftmp.write("\n")
		ftmp.write("="*10)
	ftmp.close()
	#(segGroup, boundary) = segmentBayesseg(filename) #Bayesseg code does not work in Chinese since it map words to its built-in dictionary 0617
	(segGroup, boundary) = segmentUI(filename, pid)
	if segGroup == [] and boundary == []:
		
		os.remove(filename)
		return calculateCHSentenceRating(tokenizedSentences, splitSentences, None)
	#create corresponding segments composed by untokenized sentences
	bStart = 0
	origSegGroup = []
	for b in boundary:
		origSegGroup.append(" ".join(splitSentences[bStart:int(b)]))
		#newText += "\n"
		bStart = int(b)

	os.remove(filename)
	return calculateCHSentenceRating(segGroup, origSegGroup, None)

if __name__=="__main__":
	summaryToDBCH("")
