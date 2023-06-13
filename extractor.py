# -*- coding:utf-8 -*-

import re, json
#import jieba
#import jieba.posseg as pseg
import CKIP

#jieba.load_userdict("dict_law.txt")

class Extractor(object):
	def __init__(self, text, title=""):
		super(Extractor, self).__init__()
		self.text = text
		self.text = title

		

def pos_cut(text):
	cut_words = pseg.cut(text)
	return [(word, pos) for word, pos in cut_words]

def regexp_match(text, pattern, target, group=1):
	if target:
		if isinstance(target, list):
			return [re.search(pattern, p).group(group) if re.search(pattern, p) else '' for p in text.split('。') for fil in target
			 if fil in p and re.search(pattern, p)]
		else:
			return [re.search(pattern, p).group(group) if re.search(pattern, p) else '' for p in text.split('。') 
			if target in p and re.search(pattern, p)]
	else:
		return re.search(pattern , text).group(group) if re.search(pattern, text) else ''

def regexp_findall(text, pattern):
	results = re.findall(pattern , text)
	return list(set(["".join(result) for result in results]))

def extract_maintext(text):
	lines = re.split(r'[。]', text)
	targets = ["：主文", "：\n主文"]
	for line in lines:
		for target in targets:
			if target in line:
				result = line[line.find(target)+len(target):].replace("\n", "")
				return result
	return text

def extract_person(result):
	response, others = [], []
	target = ["原告","被告","被害人","證人","目擊證人","法官","檢察官","書記官","調解委員","警員",]
	for i, p in enumerate(result):
		if i < len(result)-1 and (p[1] == 'n' and result[i+1][1] == 'nr'):
			if result[i][0] in target and len(result[i+1][0]) >=2:
				response += [(result[i][0], result[i+1][0])]
			elif len(result[i][0])>=2 and len(result[i+1][0]) >=2:
				others += [(result[i][0], result[i+1][0])]
	response = list(set(response))
	return response

def extract_person_ckip(result):
	response, others = [], []
	target = ["原告","被告","被害人","證人","目擊證人","法官","檢察官","書記官","調解委員","警員",]
	for i, (word, tag) in enumerate(zip(result["ws"][0], result["pos"][0])):
		if i < len(result["ws"][0])-1 and (tag[0] == 'N' and result["pos"][0][i+1] == 'Nb'):
			if word in target and len(result["ws"][0][i+1]) >=2:
				response += [(result["ws"][0][i], result["ws"][0][i+1])]
			elif len(result["ws"][0][i+1]) >=2:
				others += [(result["ws"][0][i], result["ws"][0][i+1])]
	response = list(set(response))
	return response

def extract_result(text, maintext): # 兩個被告暫不處理
	response = ""
	target0 = "判決如下：主文"
	targets1 = ["調解成立", "自訴不受理", "公訴不受理", "上訴駁回", "原判決撤銷", "駁回起訴", "無罪", "公訴駁回"]
	targets2 = ["補正", "增列", "更正", "修正", "改正", "矯正", "調整", "修訂", "糾正", "修改", "調正", "改進"]
	pattern = r'犯?.*處(拘役|罰金)([^，。；]+)'

	result_list = [maintext] + re.split(r'[。]', text)
	for line in result_list:
		for target in targets1:
			if target in line: return target
		for target in targets2:
			if target in line: return "補正"
		res = re.search(pattern, line)
		if res: return res.group(0)
		if target0 in line:
			response = line[line.find(target0)+len(target0):]
			return response
	return maintext

def extract_insult(text, ckip_res):
	ners = [ner[3] for ner in ckip_res['ner'][0] ]
	pattern = r'(「.+?」、?)+'
	targetList = ['罵', '侮辱']
	response = []
	for line in re.split(r'[。；]', text):
		for target in targetList:
			res = re.search(pattern, line)
			if target in line and res:
				words = re.sub(r'[「」]', '', res.group(0))
				words = re.split(r'[、!！]', words)
				for word in words:
					if word not in ners and word not in targetList and word:
						response += [word]

	#response = regexp_match(text, '「(.+?)」', ['罵', '侮辱'])
	response = list(set(response))
	response = [word for word in response if len(word)<15] 
	return response

def extract_feature(text, ckip_res):
	timeList, locaList = [], []
	for ner in ckip_res['ner'][0]:
		if ner[2] in ["DATE"]:
			timeList += [ner[3]]
		elif ner[2] in ["GPE", "LOC", "FAC"]:
			if len(ner[3]) > 1 and ner[3] not in ["中華民國", "台灣", "臺灣"]:
				locaList += [ner[3]]
	addr_pattern = r'([^，；。]{2}[縣市].{1,3}[鄉鎮市區].{2,4}[街路])(.{1,2}段)?(.{1,4}巷)?(.{1,4}弄)?(.{2,10}號)?'
	addrs = regexp_findall(text, addr_pattern)
	date_pattern = r'(?:中華民國|民國)?(\d{2,3}年\d{1,2}月\d{1,2}日)(\d{1,2}時)?(\d{1,2}分)?'
	dates = regexp_findall(text, date_pattern)
	return {"time":list(set(timeList)), "loca":list(set(locaList)),
			"addr":list(set(addrs)), "date":list(set(dates)) }

def extract_law(text, ckip_res): # Unfinished
	result = list(zip(ckip_res["ws"][0], ckip_res["pos"][0]))
	for i, (word, tag) in enumerate(result):
		print(word, tag)

if __name__ == '__main__':


	title = "TEST"
	text = """
臺灣嘉義地方法院刑事簡易判決112年度朴簡字第147號聲請人臺灣嘉義地方檢察署檢察官被告林福傳上列被告因公然侮辱案件，經檢察官提起公訴（112年度偵字第4063號），經訊問後被告自白犯罪，本院認為宜以簡易判決處刑（112年度易字第273號），判決如下：主文林福傳犯公然侮辱罪，處罰金新臺幣捌仟元，如易服勞役，以新臺幣壹仟元折算壹日。犯罪事實及理由一、犯罪事實：林福傳因發現其村內住家附近果樹上之燈飾遭破壞，懷疑係林明助所為，於民國112年1月30日18時40分許，在嘉義縣○○鄉○○村0號前道路上，質問林明助，經林明助否認係其所為後，雙方發生爭執，林福傳竟基於公然侮辱之犯意，在上開公開場所，以台語對林明助辱罵「幹你娘」及「你這個不吃子，只有你會做這種事情，別人不會做這種事」等語，足生損害於林明助之名譽。二、前開犯罪事實，有下列證據足資證明：(一)被告林福傳於警詢、偵訊、本院準備程序時之自白。(二)告訴人林明助、證人即告訴人之妻洪麗珍、證人即告訴人鄰居郭玉珠於警詢時之證述。三、核被告所為，係犯刑法第309條第1項之公然侮辱罪。被告先後以言語公然侮辱告訴人，係就同一犯罪構成事實，本於單一犯意接續進行，於密切接近之時間實施，各行為之獨立性極為薄弱，應論以接續犯之單純一罪。四、爰審酌被告與告訴人發生爭執，而為本件犯行之犯罪動機、手段，對告訴人名譽所受之損害，犯後坦承犯行，態度尚可，惟未能獲得告訴人之原諒，而未能與告訴人達成和解，暨被告自陳國中畢業之智識程度，已婚，子女均已成年，被告目前擔任村長工作，與母親同住等一切情狀，量處如主文所示之刑，並諭知易服勞役之折算標準。五、程序法條：刑事訴訟法第449條第2項。六、如對本判決上訴，須於判決送達後20日內向本院提出上訴狀（應附繕本）。本案經檢察官陳昭廷提起公訴，檢察官陳則銘到庭執行職務。中華民國112年6月8日朴子簡易庭法官吳育汝上列正本證明與原本無異。如不服本判決，應於判決送達後20日內向本院提出上訴狀（應附繕本）。告訴人或被害人如對於本判決不服者，應具備理由請求檢察官上訴，其上訴期間之計算係以檢察官收受判決正本之日期為準。中華民國112年6月8日書記官黃士祐附錄論罪科刑法條：中華民國刑法第309條：公然侮辱人者，處拘役或9千元以下罰金。以強暴犯前項之罪者，處1年以下有期徒刑、拘役或1萬5千元以下罰金。
"""
	text = text.strip()

	with open('./output/臺灣嘉義地方法院 112 年度朴簡字第 147 號刑事判決.json', 'r', encoding='utf-8') as f:
		judge = json.load(f)
	text = judge["主文"]
	text = re.sub('[ 　  \r\n]', '', text)
	print("\n\n")
	res = extract_maintext(text)
	print(res)
	exit()
	ckip_res = CKIP.request(text.strip())
	#print(json.dumps(ckip_res, ensure_ascii=False, indent=4))


	maintext = extract_maintext(text)
	persons = extract_person_ckip(ckip_res)
	bad_words = extract_insult(text, ckip_res)
	fine = regexp_match(maintext,'.*[處科]罰金([^，。]+).*' , None)
	days = regexp_match(maintext,'.*處拘役([^，。]+).*' , None)
	judge_result = extract_result(text)
	features = extract_feature(text, ckip_res)
	data = {'title': title,
			'maintext': maintext,
			'persons': persons,
			'location': list(set(features['loca']+features['addr'])),
			'date': list(set(features['date'])),
			'bad_words': bad_words,
			'fine': fine, #罰金
			'days': days, #拘役X日
			'laws': [],
			'result': judge_result,
			'text': text,
	}
	print(json.dumps(data, ensure_ascii=False, indent=4))
	exit()


	with open('sample/data/sample.json', 'r', encoding='utf-8') as f:
		sample = json.load(f)

	for s in sample:
		ckip_res = CKIP.request(s['judgement'])
		res = extract_result(s['mainText'] if s['mainText'] else s['judgement'])
		print(json.dumps(CKIP.NER1(s['judgement']), ensure_ascii=False, indent=4))

		