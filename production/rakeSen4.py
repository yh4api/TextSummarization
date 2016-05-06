#Based on the implementation of RAKE - Rapid Automatic Keyword Extraction algorithm - to do text-ranking and sentence selection
#postag is not used as ranking feature in this one in order to speed up 
#split the file into ranking and sorting functions #20150505

#version 2015.08.03

import re
import operator
from collections import defaultdict, namedtuple
import sys
from math import sqrt



string_type = (str, unicode, )
class ItemsCount(object):
	def __init__(self, value):
		self._value = value

	def __call__(self, sequence):
		if isinstance(self._value, string_type):
			if self._value.endswith("%"):
				total_count = len(sequence)
				percentage = int(self._value[:-1])
				count = max(1, total_count*percentage // 100)
				return sequence[:count]
			else:
				return sequence[:int(self._value)]
		elif isinstance(self._value, (int, float, )):
			return sequence[:int(self._value)]
		else:
			ValueError("Unsupported value of items count '%s'." % self._value)

debug = True
test = True

def is_number(s):
	try:
		float(s) if '.' in s else int(s)
		return True
	except ValueError:
		return False

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

def load_words(word_file):
	words = []
	for line in open(word_file):
		if line.strip()[0:1] != "#":
			words.append(line.strip())
	return words


def build_transition_regex(transitional_phrase_file_path):
	transitional_phrase_list = load_words(transitional_phrase_file_path)
	transitional_phrase_regex_list = []
	for word in transitional_phrase_list:
		transitional_phrase_regex_list.append(word)
	transition_phrases_pattern = re.compile(r'\b('+'|'.join(transitional_phrase_regex_list)+r')\b,?', re.IGNORECASE)
	return transition_phrases_pattern


def build_stop_word_regex(stop_word_file_path):
    stop_word_list = load_stop_words(stop_word_file_path)
    stop_word_regex_list = []
    for word in stop_word_list:
        word_regex = '\\b' + word + '\\b'
        stop_word_regex_list.append(word_regex)
    stop_word_pattern = re.compile('|'.join(stop_word_regex_list), re.IGNORECASE)
    return stop_word_pattern

def generate_candidate_keywords(sentence_list, stopword_pattern):
    phrase_list = []
    for s in sentence_list:
        tmp = re.sub(stopword_pattern, '|', s.strip())
        phrases = tmp.split("|")
        for phrase in phrases:
            phrase = phrase.strip().lower()
            if phrase != "":
                phrase_list.append(phrase)
    return phrase_list
"""
def inSplitCondition(word, pos):
	global stopwordList
	#if (word in stopwordList) or pos in ["VB", "VBP", "VBZ", "VBD", "TO", "SYM", "CD"]:
	if (word in stopwordList) or pos not in ["NN", "NNP", "NNS", "NNPS", "JJ","JJR", "JJS", "RB", "RBR", "RBS", "POS" ]:
		return True
	else:
		return False
"""
def calculate_phrases_scores(sentenceList, NE = 0, ABBR = 0, CIT = 0):#NE->name entity; ABBR->abbrevation; CIT->citation
		#text = re.sub('[^a-zA-Z0-9_\t!?,;:\\+\\-\\$@#\'\"/ \(\)]', "", text)
	sentenceKeywordList = defaultdict(list)
	phraseFreq = defaultdict(float)
	for s in sentenceList:
		x = s.rpartition("(")[0]

		x = re.sub('[^a-zA-Z0-9_\t!?,;:\.\\+\\-\\$@#\'\"/ \(\)]', "", x)
		"""
		res = corenlp.raw_parse(x)
		newSentence = ""
		allWords = []
		allLemma = []
		allPOS = []
		#print res["sentences"]
		for sentence in res["sentences"]:
			newSentence += sentence["text"]
			for words in sentence["words"]:
				allWords.append(words[0])
				allLemma.append(words[1]["Lemma"])
				allPOS.append(words[1]["PartOfSpeech"])
		
		#steps: pos-tagging -> stopword removal -> stemming -> remove phrases containing no NNX
		#keep record of NNP , abbrevation and citations
		#tmp = re.sub(stopword_pattern, '|', s.strip())
		m = re.findall(r'\([A-Z]+\)', s)
		abbrCount = len(m)
		citationCount = len(re.findall(r'\[\d+\]', s))
		NNPCount = 0
		wordSeq = []
		posSeq = []
		for word, pos, lemma in zip(allWords, allPOS, allLemma):
			if inSplitCondition(word, pos):
				candidatePhrase = " ".join(wordSeq)
				candidatePos = " ".join(posSeq)
				if re.search(r'^(NNPS?)+$', candidatePos)!=None:
					#bonus
					NNPCount += 1
					#should it be added to candidatePhrase
				elif "NN" in candidatePos:
					#add candidatePhrase
					#sentenceKeywordList.setdefault(s, [])
					if candidatePhrase not in sentenceKeywordList[s]:
						sentenceKeywordList[s].append(candidatePhrase)
					#phraseFreq.setdefault(candidatePhrase, 0)
					phraseFreq[candidatePhrase] += 1
					phraseFreq[candidatePhrase] += 0.05*(len(wordSeq)-1)
				wordSeq = []
				posSeq = []
			else:
				try:
					wordSeq.append(lemma)	
					posSeq.append(pos)
				except:
					pass
		sentenceKeywordList[s].append(NNPCount)
		sentenceKeywordList[s].append(abbrCount)
		sentenceKeywordList[s].append(citationCount)
		"""
	return sentenceKeywordList, phraseFreq

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
	if inputType == "paper":
		#text = text.replace("et al.", "et al.,")
		#text = text.replace("Fig.", "Fig")
		#text = text.replace("  ", " ")
		pass
	
	#sentenceList = text.splitlines()
	#text is a sentence array
	sentenceList = text
	stoppath = "SmartStoplist.txt"
	stopwordList = load_stop_words(stoppath)
	#stopwordpattern = build_stop_word_regex(stoppath)
		
	(sentenceKeywordList, phraseScore) = calculate_phrases_scores_TF(sentenceList, stopwordList)
	sentenceRating = generate_sentences_rating(sentenceKeywordList, phraseScore, NE, ABBR, CIT)
	rate = lambda s : sentenceRating[s]
	SentenceInfo = namedtuple("SentenceInfo", ("sentence", "order", "rating",))
	infos = (SentenceInfo(s, o, rate(s)) for o, s in enumerate(sentenceList))
	
	infos = sorted(infos, key=operator.attrgetter("rating"), reverse=True)
	newSentences = ""
	for i in infos:
		newSentences += i.sentence
		newSentences += "!@#"
		newSentences += str(i.order).zfill(3)
		newSentences += "\n"
	return newSentences
	#return an array, whose order is the rank order, so keep the info of sentence and it original order in the array.
		
def getSortedSentences(text, threshold=1):#threshold value range is from 1~100
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


		
def main(NE, ABBR, CIT):
	global stopwordList
	if test:
		#fid = open("/cygdrive/c/Users/yhlin/Downloads/IEEEpdfToTxt/PdfToText_0304/"+sys.argv[2]+".body", "r")
		fid = open(sys.argv[2], "r")
		#fid = open("/home/yhlin/text_sum/RST/HumanReport.txt", "r")
		text = fid.read()
		#text = text.replace("\r\n", " ")
		text = text.replace("et al.", "et al.,")
		text = text.replace("Fig.", "Fig")
		text = text.replace("  ", " ")
		#text = re.sub('[^a-zA-Z0-9_\t!?,;:\\+\\-\\$@#\'\"/ \(\)]', "", text)
		fid.close()
		sentenceList = text.splitlines()
		stoppath = "/home/yhlin/RAKE-master/SmartStoplist.txt"
		stopwordList = load_stop_words(stoppath)
		stopwordpattern = build_stop_word_regex(stoppath)
		
		(sentenceKeywordList, phraseScore) = calculate_phrases_scores_TF(sentenceList)
	
		sentenceRating = generate_sentences_rating(sentenceKeywordList, phraseScore, NE, ABBR, CIT)
	
		rate = lambda s : sentenceRating[s]
		SentenceInfo = namedtuple("SentenceInfo", ("sentence", "order", "rating",))
		infos = (SentenceInfo(s, o, rate(s)) for o, s in enumerate(sentenceList))
		#infos = (SentenceInfo(" ".join(sentenceList[o:o+3]), o,rate(sentenceList[o])+rate(sentenceList[o+1])+rate(sentenceList[o+2])) for o, s in enumerate(sentenceList[:-2]))
		
		
		infos = sorted(infos, key=operator.attrgetter("rating"), reverse=True)
		count = sys.argv[1]
		if not isinstance(count, ItemsCount):
			count = ItemsCount(count)
		infos = count(infos)
		infos = sorted(infos, key=operator.attrgetter("order"))
		sen_id = 1
		sentences = tuple(i.sentence for i in infos)
		sentence_seq = tuple(i.order for i in infos)
		prev_o = -2
		sen_id = 1
		for s, o in zip(sentences, sentence_seq):
			if prev_o == o-1:
				print sen_id, s, o
			else:
				print sen_id, s, o
			prev_o = o
			sen_id += 1
				

if __name__=="__main__":
	
	try:
		NE = sys.argv[3]
	except:
		NE = 0
	try:
		ABBR = sys.argv[4]
	except:
		ABBR = 0
	try:
		CIT = sys.argv[5]	
	except:
		CIT = 0
	stitch = 2
	main(NE, ABBR, CIT)
