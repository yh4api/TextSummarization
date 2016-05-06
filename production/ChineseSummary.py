# -*- coding:utf-8 -*-
# process : 分句(標點符號)-> 分詞(jieba) -> segmentation(vseg) -> sum_ch.py (還要n-gram嗎?)
# example :  python testChineseSummary.py < news4.txt
# version '150812
import sys, os, re
import subprocess
import jieba
from collections import defaultdict, namedtuple
import operator
import random

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
	SentenceInfo = namedtuple("SentenceInfo", ("sentence", "order", "rating",))
	infos = (SentenceInfo(s, o, rate(s)) for o, s in enumerate(sentenceList))
	
	infos = sorted(infos, key=operator.attrgetter("rating"), reverse=True)
	newSentences = ""
	for i in infos:
		#newSentences += i.sentence.replace(" ", "") #this is not working if the text contains both English(or other languages split by space) and Chinese, which has no spaces between
		newSentences += origText[i.order].encode("utf-8")
		newSentences += "!@#"
		newSentences += str(i.order).zfill(3)
		newSentences += "\n"
	return newSentences

def getSortedSentencesCH(text, threshold=1):#threshold value range is from 1~100
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

def splitSentences(text):
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
	sentences = splitSentences(text)
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
	text = u"警方調查，就讀台灣科技大學四年級的鄧姓學生，昨日上午與2名男同學、1名女同學搭乘公車到烏來區啦卡路旁的「桶後溪」溯溪戲水。中午12時許，鄧男與女同學相約一起游泳至對岸，女同學游至對岸時，卻發現鄧男在水面上載浮載沉，其餘同學見狀連忙報警處理。第四救災救護大隊長鍾世銘表示，夏日即將來臨，民眾戲水不該到危險水域，進入水域時應遵守警告標誌及救生人員勸導，不要著長褲下水，更不可從事跳水、水中嬉鬧等危險行為，尤其一般野溪看似平靜，其實水下多半潛藏暗流，稍有不慎就容易發生意外。43歲姜美菊與96歲丈夫任瑞麟，26年前因緣際會在大陸廣州相識相戀，姜不顧家人反對這段「爺孫戀」，隻身飛來台灣與任共組家庭16年，丈夫長年身體不好如今又失智，姜以微薄薪水買二手車，載他求醫、旅行，因此獲頒模範母親。姜美菊等14名外配嫁來台灣多年，悉心照顧年邁丈夫，協助維持家計，獲桃園市外籍配偶協會與桃園市榮服處，頒發模範母親，其中不少人提起艱困過往眼眶泛紅，雖然目前生活不富裕，她們知足常樂，更將台灣視為第二故鄉。姜美菊26年前就讀廣州中山大學時，在飯店打工擔任收銀人員，與赴陸探親、下榻飯店的任瑞麟巧遇相識，由於都是湖南同鄉，2人彼此互留地址，之後的10年來，雙方百封書信往來，彼此鼓勵上進、保重身體，逐漸燃起愛苗。任瑞麟1958年軍階上尉軍官退伍，早年娶妻生子，但在1980年離婚，目前靠著1萬4000元的榮民補助救養金過活，雖不富裕，卻常自掏腰包，帶已故同袍的骨灰赴陸落葉歸根，這種善良，以及在信中表露出的一手好書法，都讓姜美菊傾心。"
	text = u"美國安德森治癌中心腫瘤生物學博士顏榮郎今天指出，防癌養生不能忽視糖、紅肉以及麩醯胺酸等3大促癌因子的危險性。顏榮郎在康健雜誌舉辦的「抗癌新未來」論壇指出，癌細胞與脂肪細胞結構近似，最大的不同在於癌細胞當中多了發炎細胞，癌症其實是一種發炎疾病。顏榮郎將糖列為癌細胞三大「補品」之一，理由在於攝取過多葡萄糖會使血糖快速上升，刺激胰島素增加，類胰島生長因子跟著增加，刺激癌細胞生長，甚至讓癌細胞對化療反應變差，還有糖化蛋白的風險，加重發炎，偏偏現代人常忽略糖分對健康潛藏的危害。他建議，癌症病人少吃糖，減少白米，改吃糙米，至於紅肉與動物性油脂吃多了，會增加血液中的低密度脂蛋白膽固醇（LDL），也就是俗稱的「壞膽固醇」，當壞膽固醇被氧化，被巨噬細胞吞噬的過程就會分泌發炎激素。癌症病友化療期間常吃麩醯胺酸，被當成口腔潰瘍用藥，顏榮郎認為，麩醯胺酸和葡萄糖都是癌細胞喜歡的物質，不是不能吃，一點點就好，不要一天吃二、三十顆，以免在分解過程間接釋放發炎酵素，反而提供癌細胞生長材料。警、消獲報抵達，消防人員利用魚雷浮標救回對岸的女同學，浮潛下水將鄧男救起，當時他已無呼吸心跳，送新店耕莘醫院急救20分鐘，已恢復生命跡象，但到了晚間症狀惡化，宣告不治。"
	tmp_out = summaryToDBCH(text)
	print tmp_out
	#print getSortedSentencesCH(tmp_out, 1)
